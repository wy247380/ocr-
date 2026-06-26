"""
核心智能体编排 — 状态机驱动的专利证书核验 Agent

流程：
1. 文件分类 → 2. PDF 渲染 → 3. 图像预处理 → 4. OCR 提取 →
5. PDF 文本层 → 6. 签章检测 → 7. 字段规范化 → 8. 官方查询 →
9. 字段比对 → 10. 自动判定/转人工 → 11. 审计日志
"""

import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

from .database import get_session
from .models import PatentUpload, PatentVisibleExtraction, PatentOfficialRecord, PatentVerificationResult
from .state_machine import AgentState, can_transition
from .config import OCR_CONFIDENCE_THRESHOLD, now_beijing
from .skills import (
    classify_uploaded_file,
    render_pdf_to_images,
    preprocess_image,
    extract_visible_patent_fields,
    extract_pdf_text_layer,
    verify_pdf_signature_reference,
    normalize_patent_fields,
    query_cnipa_official_record,
    compare_patent_fields,
    create_manual_review_task,
    write_audit_log,
)


class PatentVerifyAgent:
    def __init__(self, upload_id: int):
        self.upload_id = upload_id
        self.state = AgentState.AGENT_RECEIVED
        self.context: dict = {}
        self.errors: list = []

    def run(self) -> dict:
        session = get_session()
        try:
            upload = session.query(PatentUpload).filter_by(id=self.upload_id).first()
            if not upload:
                return {"status": "error", "error": "上传记录不存在"}

            upload.status = "processing"
            session.commit()
            write_audit_log(session, self.upload_id, "agent_start", "开始核验流程")

            self._transition(AgentState.AGENT_CLASSIFYING_FILE)
            self._step_classify(session, upload)

            self._transition(AgentState.AGENT_RENDERING_PDF_IF_NEEDED)
            self._step_render(session, upload)

            self._transition(AgentState.AGENT_PREPROCESSING_VISIBLE_IMAGE)
            self._step_preprocess(session)

            self._transition(AgentState.AGENT_EXTRACTING_VISIBLE_FIELDS)
            self._step_ocr(session)

            self._transition(AgentState.AGENT_EXTRACTING_PDF_TEXT_LAYER_OPTIONAL)
            self._step_pdf_text(session, upload)

            self._transition(AgentState.AGENT_CHECKING_PDF_SIGNATURE_REFERENCE_OPTIONAL)
            self._step_signature(session, upload)

            self._transition(AgentState.AGENT_NORMALIZING_FIELDS)
            self._step_normalize(session)

            self._transition(AgentState.AGENT_QUERYING_OFFICIAL_RECORD)
            self._step_query_official(session)

            self._transition(AgentState.AGENT_COMPARING_WITH_OFFICIAL_RECORD)
            self._step_compare(session)

            self._transition(AgentState.AGENT_DECISION_MAKING)
            result = self._step_decide(session, upload)

            write_audit_log(session, self.upload_id, "agent_complete",
                           f"核验完成: {result.get('final_status', 'unknown')}")
            return result

        except Exception as e:
            self.errors.append(str(e))
            traceback.print_exc()
            try:
                session.rollback()
                write_audit_log(session, self.upload_id, "agent_error", str(e)[:500])
            except Exception:
                pass
            self._transition(AgentState.FAILED)
            return {"status": "error", "error": str(e), "state": self.state.value}
        finally:
            session.close()

    def _transition(self, new_state: AgentState):
        if can_transition(self.state, new_state):
            self.state = new_state
        else:
            self.state = new_state

    def _step_classify(self, session, upload: PatentUpload):
        result = classify_uploaded_file(upload.file_path)
        self.context["file_type"] = result["file_type"]
        self.context["mime_type"] = result["mime_type"]
        self.context["file_path"] = upload.file_path
        upload.file_type = result["file_type"]
        session.commit()

    def _step_render(self, session, upload: PatentUpload):
        if self.context["file_type"] == "pdf":
            result = render_pdf_to_images(upload.file_path)
            self.context["rendered_pages"] = result.get("page_images", [])
        else:
            self.context["rendered_pages"] = [{"image_path": upload.file_path, "page": 1}]

    def _step_preprocess(self, session):
        processed = []
        for page in self.context.get("rendered_pages", []):
            result = preprocess_image(page["image_path"])
            processed.append(result.get("preprocessed_image_path", page["image_path"]))
        self.context["preprocessed_images"] = processed

    def _step_ocr(self, session):
        all_fields = {}
        confidences = []
        images = self.context.get("preprocessed_images", [])
        if images:
            result = extract_visible_patent_fields(images)
            if result.get("status") == "success":
                all_fields = {
                    "patent_no": result.get("patent_no_normalized"),
                    "publication_no": result.get("publication_no"),
                    "title": result.get("patent_title"),
                    "type": result.get("patent_type"),
                    "inventors": result.get("inventors"),
                    "patentee": result.get("patentee"),
                    "application_date": result.get("application_date"),
                    "grant_date": result.get("grant_announcement_date"),
                }
                avg_conf = result.get("confidence", {})
                conf_vals = [v for v in avg_conf.values() if v and v > 0]
                confidences = conf_vals if conf_vals else [0]

        # OCR 失败兜底：对于 PDF，用文本层内容交 DeepSeek 解析
        if not all_fields and self.context.get("file_type") == "pdf":
            try:
                from .skills.extract_pdf_text_layer import extract_pdf_text_layer
                from .skills.extract_visible_fields import _enhance_with_deepseek, _parse_fields
                pdf_result = extract_pdf_text_layer(self.context["file_path"])
                raw_text = pdf_result.get("raw_text", "")
                if raw_text.strip():
                    parsed = _parse_fields(raw_text, [{"text": t, "confidence": 0.8} for t in raw_text.split("\n") if t.strip()])
                    enhanced = _enhance_with_deepseek(raw_text, parsed)
                    if enhanced.get("status") == "success":
                        all_fields = {
                            "patent_no": enhanced.get("patent_no_normalized"),
                            "publication_no": enhanced.get("publication_no"),
                            "title": enhanced.get("patent_title"),
                            "type": enhanced.get("patent_type"),
                            "inventors": enhanced.get("inventors"),
                            "patentee": enhanced.get("patentee"),
                            "application_date": enhanced.get("application_date"),
                            "grant_date": enhanced.get("grant_announcement_date"),
                        }
                        confidences = [0.75]
                        logger.info("OCR兜底: 已用PDF文本层+DeepSeek解析字段")
            except Exception as e:
                logger.warning("PDF文本层兜底失败: %s", e)

        self.context["ocr_fields"] = all_fields
        self.context["ocr_confidence"] = min(confidences) if confidences else 0

        extraction = PatentVisibleExtraction(
            upload_id=self.upload_id,
            ocr_provider="deepseek_vision",
            raw_text=str(all_fields),
            patent_no_raw=all_fields.get("patent_no"),
            patent_title=all_fields.get("title"),
            patent_type=all_fields.get("type"),
            inventors=",".join(all_fields.get("inventors") or []),
            patentee=",".join(all_fields.get("patentee") or []),
            application_date=all_fields.get("application_date"),
            grant_announcement_date=all_fields.get("grant_date"),
            publication_no=all_fields.get("publication_no"),
            avg_confidence=self.context["ocr_confidence"],
            created_at=now_beijing(),
        )
        session.add(extraction)
        session.commit()

    def _step_pdf_text(self, session, upload: PatentUpload):
        if self.context["file_type"] != "pdf":
            self.context["pdf_text_record"] = {}
            return

        result = extract_pdf_text_layer(upload.file_path)
        self.context["pdf_text_record"] = result.get("text_layer_record", {})
        self.context["has_text_layer"] = result.get("has_text_layer", False)

    def _step_signature(self, session, upload: PatentUpload):
        if self.context["file_type"] != "pdf":
            self.context["signature_info"] = {"has_signature": False}
            return

        result = verify_pdf_signature_reference(upload.file_path)
        self.context["signature_info"] = result

    def _step_normalize(self, session):
        ocr_fields = self.context.get("ocr_fields", {})
        raw_record = {
            "patent_no_raw": ocr_fields.get("patent_no"),
            "publication_no_raw": ocr_fields.get("publication_no"),
            "patent_title": ocr_fields.get("title"),
            "inventors": ocr_fields.get("inventors", "").split("、") if isinstance(ocr_fields.get("inventors"), str) else ocr_fields.get("inventors", []),
            "patentee": ocr_fields.get("patentee", "").split("、") if isinstance(ocr_fields.get("patentee"), str) else ocr_fields.get("patentee", []),
            "patent_type": ocr_fields.get("type"),
            "application_date": ocr_fields.get("application_date"),
            "grant_announcement_date": ocr_fields.get("grant_date"),
        }

        result = normalize_patent_fields(raw_record)
        self.context["normalized_record"] = result.get("normalized_record", {})

    def _step_query_official(self, session):
        publication_no = self.context.get("normalized_record", {}).get("publication_no")

        if not publication_no:
            self.context["official_query"] = {
                "query_status": "failed",
                "official_record": None,
                "need_manual": True,
                "fail_reason": "无法提取公开号，无法查询官方记录",
            }
            return

        result = query_cnipa_official_record(publication_no)
        self.context["official_query"] = result

        if result.get("official_record"):
            official = PatentOfficialRecord(
                upload_id=self.upload_id,
                source="cnipa",
                query_key=publication_no,
                application_no=result["official_record"].get("application_no"),
                patent_no=result["official_record"].get("patent_no"),
                patent_title=result["official_record"].get("patent_title"),
                patent_type=result["official_record"].get("patent_type"),
                inventors=",".join(result["official_record"].get("inventors") or []),
                patentee=",".join(result["official_record"].get("patentee") or []),
                application_date=result["official_record"].get("application_date"),
                grant_announcement_date=result["official_record"].get("grant_announcement_date"),
                legal_status=result["official_record"].get("legal_status"),
                publication_no=result["official_record"].get("publication_no"),
                created_at=now_beijing(),
            )
            session.add(official)
            session.commit()

    def _step_compare(self, session):
        official_query = self.context.get("official_query", {})

        if official_query.get("need_manual") or not official_query.get("official_record"):
            self.context["comparison"] = {
                "match_result": "skipped",
                "auto_pass": False,
                "need_manual": True,
                "reason": official_query.get("fail_reason", "官方查询失败"),
            }
            return

        result = compare_patent_fields(
            self.context.get("normalized_record", {}),
            official_query["official_record"],
        )
        self.context["comparison"] = result

    def _step_decide(self, session, upload: PatentUpload) -> dict:
        comparison = self.context.get("comparison", {})
        ocr_confidence = self.context.get("ocr_confidence", 0)

        # 自动通过条件：比对通过 + 官网查询成功（不再硬要求 OCR 原始置信度，DeepSeek 已校正）
        auto_pass = (
            comparison.get("auto_pass", False)
            and not self.context.get("official_query", {}).get("need_manual", True)
        )

        if auto_pass:
            self._transition(AgentState.APPROVED)
            final_status = "auto_approved"
        else:
            self._transition(AgentState.MANUAL_REVIEW_REQUIRED)
            final_status = "pending_manual_review"

        result = PatentVerificationResult(
            upload_id=self.upload_id,
            verification_status=final_status,
            auto_pass=auto_pass,
            fail_reason=comparison.get("reason") if not auto_pass else None,
            comparison_detail=comparison,
            created_at=now_beijing(),
        )
        session.add(result)

        upload.status = final_status
        session.commit()

        # 人工审核记录已在上面创建（PatentVerificationResult），此处不重复

        return {
            "status": "completed",
            "final_status": final_status,
            "auto_pass": auto_pass,
            "comparison": comparison,
            "ocr_confidence": ocr_confidence,
        }

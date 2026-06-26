"""
Skill: compare_patent_fields — 字段比对逻辑

OCR 提取结果 vs 官方查询结果，逐字段比对。
只比较三个字段：作者(inventors), 专利名称(patent_title), 专利公开号(publication_no)
支持两种模式：
  1. 本地规则比对（默认回退）
  2. DeepSeek V4 flash + thinking 深度推理比对（首选）
"""
from __future__ import annotations

from difflib import SequenceMatcher

from ..config import SIMILARITY_THRESHOLD, DEEPSEEK_API_KEY, USE_LLM_COMPARE


def compare_patent_fields(ocr_record: dict, official_record: dict) -> dict:
    if not ocr_record or not official_record:
        return {
            "match_result": "failed",
            "auto_pass": False,
            "need_manual": True,
            "reason": "OCR 记录或官方记录缺失",
            "field_details": [],
        }

    if USE_LLM_COMPARE and DEEPSEEK_API_KEY:
        llm_result = _compare_with_deepseek(ocr_record, official_record)
        if llm_result:
            return llm_result

    return _compare_local(ocr_record, official_record)


def _compare_local(ocr_record: dict, official_record: dict) -> dict:
    details = []
    all_pass = True

    details.append(_compare_exact(
        "publication_no", "公开号",
        ocr_record.get("publication_no"),
        official_record.get("publication_no"),
    ))

    details.append(_compare_similarity(
        "patent_title", "专利名称",
        ocr_record.get("patent_title"),
        official_record.get("patent_title"),
        SIMILARITY_THRESHOLD,
    ))

    details.append(_compare_set(
        "inventors", "发明人/作者",
        ocr_record.get("inventors", []),
        official_record.get("inventors", []),
    ))

    for d in details:
        if not d["matched"]:
            all_pass = False

    mismatch_fields = [d["field_label"] for d in details if not d["matched"] and d["ocr_value"] and d["official_value"]]

    if all_pass:
        result = "matched"
        reason = "公开号、专利名称、作者均匹配"
    else:
        result = "mismatched"
        reason = "以下字段不一致: %s" % ", ".join(mismatch_fields) if mismatch_fields else "关键字段缺失"

    return {
        "match_result": result,
        "auto_pass": all_pass,
        "need_manual": not all_pass,
        "reason": reason,
        "field_details": details,
    }


def _compare_exact(key: str, label: str, ocr_val, official_val) -> dict:
    if not ocr_val or not official_val:
        return _detail(key, label, ocr_val, official_val, None, ocr_val is None or official_val is None)

    matched = str(ocr_val).strip() == str(official_val).strip()
    return _detail(key, label, ocr_val, official_val, 1.0 if matched else 0.0, matched)


def _compare_similarity(key: str, label: str, ocr_val, official_val, threshold: float) -> dict:
    if not ocr_val or not official_val:
        return _detail(key, label, ocr_val, official_val, None, ocr_val is None or official_val is None)

    score = SequenceMatcher(None, str(ocr_val), str(official_val)).ratio()
    return _detail(key, label, ocr_val, official_val, round(score, 4), score >= threshold)


def _compare_set(key: str, label: str, ocr_list, official_list) -> dict:
    if isinstance(ocr_list, str):
        ocr_list = [s.strip() for s in ocr_list.split(",") if s.strip()]
    if isinstance(official_list, str):
        official_list = [s.strip() for s in official_list.split(",") if s.strip()]

    ocr_set = set(ocr_list or [])
    official_set = set(official_list or [])

    if not ocr_set and not official_set:
        return _detail(key, label, list(ocr_set), list(official_set), None, True)
    if not ocr_set or not official_set:
        return _detail(key, label, list(ocr_set), list(official_set), None, False)

    matched = ocr_set == official_set
    intersection = ocr_set & official_set
    score = len(intersection) / max(len(ocr_set), len(official_set))
    return _detail(key, label, list(ocr_set), list(official_set), round(score, 4), matched)


def _detail(key, label, ocr_val, official_val, score, matched) -> dict:
    return {
        "field_key": key,
        "field_label": label,
        "ocr_value": ocr_val,
        "official_value": official_val,
        "similarity_score": score,
        "matched": matched,
    }


def _compare_with_deepseek(ocr_record: dict, official_record: dict):
    """使用 DeepSeek V4 flash + thinking 模式进行字段比对。"""
    try:
        from .deepseek_client import compare_fields_with_llm
        result = compare_fields_with_llm(ocr_record, official_record)
        if result and "match_result" not in result:
            # 兼容处理返回格式
            if "match" in result:
                result["match_result"] = "matched" if result["match"] else "mismatched"
                result["auto_pass"] = result.pop("match", False)
        if result:
            result.setdefault("need_manual", not result.get("auto_pass", False))
            result["compare_method"] = "deepseek-v4-flash+thinking"
        return result
    except Exception:
        return None

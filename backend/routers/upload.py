"""
路由: 文件上传 + 触发核验（支持单个/批量）
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse

from ..config import UPLOAD_DIR, now_beijing
from ..database import get_session
from ..models import PatentUpload
from ..agent import PatentVerifyAgent
from ..skills import write_audit_log

router = APIRouter(prefix="/api/patent", tags=["upload"])

ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@router.post("/upload")
async def upload_patent_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    result = _save_file(file)
    if "error" in result:
        return JSONResponse(status_code=400, content=result)

    if background_tasks:
        background_tasks.add_task(_run_agent, result["upload_id"])
    else:
        _run_agent(result["upload_id"])

    return result


@router.post("/upload-batch")
async def upload_patent_files_batch(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "未选择文件"})

    if len(files) > 50:
        return JSONResponse(status_code=400, content={"error": "单次最多上传 50 个文件"})

    batch_id = uuid.uuid4().hex[:12]
    results = []
    errors = []

    for file in files:
        result = _save_file(file, batch_id=batch_id)
        if "error" in result:
            errors.append({"filename": file.filename, "error": result["error"]})
        else:
            results.append(result)
            if background_tasks:
                background_tasks.add_task(_run_agent, result["upload_id"])
            else:
                _run_agent(result["upload_id"])

    return {
        "batch_id": batch_id,
        "total": len(files),
        "accepted": len(results),
        "rejected": len(errors),
        "tasks": results,
        "errors": errors,
        "message": f"已接收 {len(results)} 个文件，核验流程已启动",
    }


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    session = get_session()
    try:
        uploads = session.query(PatentUpload).filter_by(batch_id=batch_id).order_by(PatentUpload.id).all()
        if not uploads:
            return JSONResponse(status_code=404, content={"error": "批次不存在"})

        from ..models import PatentVerificationResult
        items = []
        for u in uploads:
            result = session.query(PatentVerificationResult).filter_by(upload_id=u.id).order_by(
                PatentVerificationResult.id.desc()
            ).first()

            mismatch_fields = []
            if result and result.comparison_detail:
                details = result.comparison_detail.get("field_details", [])
                for d in details:
                    if not d.get("matched") and d.get("ocr_value") and d.get("official_value"):
                        mismatch_fields.append({
                            "field": d.get("field_label", d.get("field_key")),
                            "ocr_value": d.get("ocr_value"),
                            "official_value": d.get("official_value"),
                        })

            items.append({
                "task_id": u.task_id,
                "upload_id": u.id,
                "filename": u.original_filename,
                "status": u.status,
                "auto_pass": result.auto_pass if result else None,
                "fail_reason": result.fail_reason if result else None,
                "mismatch_fields": mismatch_fields,
            })

        total = len(items)
        passed = sum(1 for i in items if i["status"] == "auto_approved" or i["status"] == "approved_manual")
        failed = sum(1 for i in items if i["status"] == "rejected_manual")
        pending = sum(1 for i in items if i["status"] in ("pending_manual_review", "processing", "uploaded"))

        return {
            "batch_id": batch_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pending_review": pending,
            "items": items,
        }
    finally:
        session.close()


def _save_file(file: UploadFile, batch_id: str = None) -> dict:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return {"error": f"不支持的文件格式: {ext}"}

    task_id = uuid.uuid4().hex[:16]
    task_dir = UPLOAD_DIR / f"task_{task_id}"
    task_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{task_id}{ext}"
    dest_path = task_dir / safe_name
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    session = get_session()
    try:
        upload = PatentUpload(
            task_id=task_id,
            batch_id=batch_id,
            original_filename=file.filename,
            file_path=str(dest_path),
            file_type=ext.lstrip("."),
            file_size=os.path.getsize(dest_path),
            status="uploaded",
            created_at=now_beijing(),
        )
        session.add(upload)
        session.commit()
        session.refresh(upload)

        write_audit_log(session, upload.id, "file_uploaded", f"文件上传: {file.filename}")

        return {
            "task_id": task_id,
            "upload_id": upload.id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "文件上传成功，核验流程已启动",
        }
    finally:
        session.close()


def _run_agent(upload_id: int):
    import traceback
    try:
        agent = PatentVerifyAgent(upload_id)
        agent.run()
    except Exception as e:
        traceback.print_exc()
        session = get_session()
        try:
            upload = session.query(PatentUpload).filter_by(id=upload_id).first()
            if upload:
                upload.status = "failed"
                session.commit()
            write_audit_log(session, upload_id, "agent_crash", str(e)[:500])
        except Exception:
            pass
        finally:
            session.close()

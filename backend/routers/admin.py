"""
路由: 管理后台 — 人工审核 + 审计日志 + 截图服务
"""
from __future__ import annotations

import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..database import get_session
from ..models import PatentVerificationResult, PatentUpload
from ..skills import approve_manual_review, reject_manual_review, get_audit_logs, write_audit_log

router = APIRouter(prefix="/api/admin", tags=["admin"])

_SCREENSHOT_PATH = str(Path.home() / ".patent_verify_screenshot.png")


def _image_to_base64(path: str) -> str | None:
    """将图片文件转为 base64 字符串。"""
    try:
        if Path(path).exists():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None


class ReviewAction(BaseModel):
    reviewer: str
    comment: str = ""


@router.get("/reviews")
async def list_pending_reviews(limit: int = 50, offset: int = 0):
    session = get_session()
    try:
        query = session.query(PatentVerificationResult).filter_by(
            verification_status="pending_manual_review"
        ).order_by(PatentVerificationResult.created_at.desc())

        total = query.count()
        items = query.offset(offset).limit(limit).all()

        reviews = []
        for r in items:
            task_id = None
            if r.upload_id:
                upload = session.query(PatentUpload).filter_by(id=r.upload_id).first()
                if upload:
                    task_id = upload.task_id
            reviews.append({
                "id": r.id,
                "upload_id": r.upload_id,
                "task_id": task_id,
                "verification_status": r.verification_status,
                "fail_reason": r.fail_reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        return {"total": total, "reviews": reviews}
    finally:
        session.close()


@router.post("/reviews/{result_id}/approve")
async def approve_review(result_id: int, body: ReviewAction):
    session = get_session()
    try:
        result = approve_manual_review(session, result_id, body.reviewer, body.comment)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])

        write_audit_log(session, result.get("upload_id", 0), "manual_approve",
                        f"审核人: {body.reviewer}, 备注: {body.comment}")
        return result
    finally:
        session.close()


@router.post("/reviews/{result_id}/reject")
async def reject_review(result_id: int, body: ReviewAction):
    session = get_session()
    try:
        result = reject_manual_review(session, result_id, body.reviewer, body.comment)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])

        write_audit_log(session, result.get("upload_id", 0), "manual_reject",
                        f"审核人: {body.reviewer}, 备注: {body.comment}")
        return result
    finally:
        session.close()


@router.get("/audit-logs")
async def list_audit_logs(upload_id: int = None, limit: int = 100, offset: int = 0):
    session = get_session()
    try:
        return get_audit_logs(session, upload_id=upload_id, limit=limit, offset=offset)
    finally:
        session.close()


@router.get("/reviews/{result_id}/screenshots")
async def get_review_screenshots(result_id: int):
    """获取审核所需的截图（OCR 原图 + 官网查询截图）。"""
    session = get_session()
    try:
        result = session.query(PatentVerificationResult).filter_by(id=result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="审核记录不存在")

        screenshots = {
            "ocr_image": None,        # OCR 识别原图 base64
            "official_screenshot": None,  # 官网查询截图 base64
        }

        # 获取上传记录中的 OCR 图片
        if result.upload_id:
            upload = session.query(PatentUpload).filter_by(id=result.upload_id).first()
            if upload and upload.original_filename:
                # 尝试在 rendered 目录找渲染图
                from ..config import RENDERED_DIR
                import os as _os
                task_dir = _os.path.join(str(RENDERED_DIR), "task_%d" % result.upload_id)
                if Path(task_dir).exists():
                    # 找第一张渲染图
                    for img_file in sorted(Path(task_dir).glob("*.png")):
                        screenshots["ocr_image"] = _image_to_base64(str(img_file))
                        break
                    if not screenshots["ocr_image"]:
                        for img_file in sorted(Path(task_dir).glob("*.jpg")):
                            screenshots["ocr_image"] = _image_to_base64(str(img_file))
                            break

        # 获取官网查询截图
        screenshots["official_screenshot"] = _image_to_base64(_SCREENSHOT_PATH)

        return JSONResponse(screenshots)
    finally:
        session.close()

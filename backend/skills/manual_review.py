"""
Skill: manual_review — 人工审核任务管理
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from ..config import now_beijing
from ..models import PatentVerificationResult, PatentUpload


def create_manual_review_task(
    session: Session,
    upload_id: int,
    reason: str,
    comparison_result: dict | None = None,
) -> dict:
    """创建人工审核任务——检查是否已有 pending 记录，避免重复。"""
    existing = session.query(PatentVerificationResult).filter_by(
        upload_id=upload_id, verification_status="pending_manual_review"
    ).first()
    if existing:
        return {
            "status": "manual_review_exists",
            "result_id": existing.id,
            "upload_id": upload_id,
            "reason": reason,
        }

    result = PatentVerificationResult(
        upload_id=upload_id,
        verification_status="pending_manual_review",
        auto_pass=False,
        fail_reason=reason,
        comparison_detail=comparison_result,
        reviewed_by=None,
        review_comment=None,
        created_at=now_beijing(),
    )
    session.add(result)
    session.commit()
    session.refresh(result)

    return {
        "status": "manual_review_created",
        "result_id": result.id,
        "upload_id": upload_id,
        "reason": reason,
    }


def _sync_upload_status(session: Session, upload_id: int, status: str):
    """同步更新 PatentUpload 的状态。"""
    upload = session.query(PatentUpload).filter_by(id=upload_id).first()
    if upload:
        upload.status = status


def approve_manual_review(
    session: Session,
    result_id: int,
    reviewer: str,
    comment: str = "",
) -> dict:
    result = session.query(PatentVerificationResult).filter_by(id=result_id).first()
    if not result:
        return {"status": "error", "error": "审核记录不存在"}

    if result.verification_status != "pending_manual_review":
        return {"status": "error", "error": f"当前状态 {result.verification_status} 不可操作"}

    result.verification_status = "approved_manual"
    result.reviewed_by = reviewer
    result.review_comment = comment
    result.reviewed_at = now_beijing()
    _sync_upload_status(session, result.upload_id, "approved_manual")
    session.commit()

    return {"status": "approved", "result_id": result_id, "reviewer": reviewer, "upload_id": result.upload_id}


def reject_manual_review(
    session: Session,
    result_id: int,
    reviewer: str,
    comment: str = "",
) -> dict:
    result = session.query(PatentVerificationResult).filter_by(id=result_id).first()
    if not result:
        return {"status": "error", "error": "审核记录不存在"}

    if result.verification_status != "pending_manual_review":
        return {"status": "error", "error": f"当前状态 {result.verification_status} 不可操作"}

    result.verification_status = "rejected_manual"
    result.reviewed_by = reviewer
    result.review_comment = comment
    result.reviewed_at = now_beijing()
    _sync_upload_status(session, result.upload_id, "rejected_manual")
    session.commit()

    return {"status": "rejected", "result_id": result_id, "reviewer": reviewer, "upload_id": result.upload_id}

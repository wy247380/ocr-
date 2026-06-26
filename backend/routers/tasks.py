"""
路由: 查询任务状态和详情
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..database import get_session
from ..models import (
    PatentUpload,
    PatentVisibleExtraction,
    PatentOfficialRecord,
    PatentVerificationResult,
)

router = APIRouter(prefix="/api/patent", tags=["tasks"])


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    session = get_session()
    try:
        upload = session.query(PatentUpload).filter_by(task_id=task_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="任务不存在")

        extraction = session.query(PatentVisibleExtraction).filter_by(upload_id=upload.id).first()
        official = session.query(PatentOfficialRecord).filter_by(upload_id=upload.id).first()
        result = session.query(PatentVerificationResult).filter_by(upload_id=upload.id).order_by(
            PatentVerificationResult.id.desc()
        ).first()

        return {
            "task_id": task_id,
            "upload_id": upload.id,
            "filename": upload.original_filename,
            "status": upload.status,
            "created_at": upload.created_at.isoformat() if upload.created_at else None,
            "extraction": _serialize_extraction(extraction),
            "official_record": _serialize_official(official),
            "verification_result": _serialize_result(result),
        }
    finally:
        session.close()


@router.get("/tasks")
async def list_tasks(status: str = None, limit: int = 50, offset: int = 0):
    session = get_session()
    try:
        query = session.query(PatentUpload).order_by(PatentUpload.created_at.desc())
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        uploads = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "tasks": [
                {
                    "task_id": u.task_id,
                    "upload_id": u.id,
                    "filename": u.original_filename,
                    "status": u.status,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in uploads
            ],
        }
    finally:
        session.close()


def _serialize_extraction(ext) -> dict | None:
    if not ext:
        return None
    return {
        "patent_no": ext.patent_no_raw,
        "patent_title": ext.patent_title,
        "patent_type": ext.patent_type,
        "inventors": ext.inventors,
        "patentee": ext.patentee,
        "application_date": ext.application_date,
        "grant_announcement_date": ext.grant_announcement_date,
        "publication_no": ext.publication_no,
        "avg_confidence": ext.avg_confidence,
    }


def _serialize_official(off) -> dict | None:
    if not off:
        return None
    return {
        "source": off.source,
        "application_no": off.application_no,
        "patent_no": off.patent_no,
        "patent_title": off.patent_title,
        "patent_type": off.patent_type,
        "inventors": off.inventors,
        "patentee": off.patentee,
        "application_date": off.application_date,
        "grant_announcement_date": off.grant_announcement_date,
        "legal_status": off.legal_status,
        "publication_no": off.publication_no,
    }


def _serialize_result(res) -> dict | None:
    if not res:
        return None

    mismatch_fields = []
    if res.comparison_detail:
        details = res.comparison_detail.get("field_details", [])
        for d in details:
            if not d.get("matched") and d.get("ocr_value") and d.get("official_value"):
                mismatch_fields.append({
                    "field": d.get("field_label", d.get("field_key")),
                    "ocr_value": d.get("ocr_value"),
                    "official_value": d.get("official_value"),
                    "similarity_score": d.get("similarity_score"),
                })

    return {
        "id": res.id,
        "verification_status": res.verification_status,
        "auto_pass": res.auto_pass,
        "fail_reason": res.fail_reason,
        "comparison_detail": res.comparison_detail,
        "mismatch_fields": mismatch_fields,
        "reviewed_by": res.reviewed_by,
        "review_comment": res.review_comment,
    }

"""
Skill: write_audit_log — 审计日志写入
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..config import now_beijing
from ..models import AuditLog


def write_audit_log(
    session: Session,
    upload_id: int,
    action: str,
    detail: str = "",
    operator: str = "system",
) -> dict:
    log = AuditLog(
        upload_id=upload_id,
        action=action,
        detail=detail,
        operator=operator,
        created_at=now_beijing(),
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    return {"status": "logged", "log_id": log.id}


def get_audit_logs(
    session: Session,
    upload_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    query = session.query(AuditLog).order_by(AuditLog.created_at.desc())

    if upload_id is not None:
        query = query.filter_by(upload_id=upload_id)

    total = query.count()
    logs = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "upload_id": log.upload_id,
                "action": log.action,
                "detail": log.detail,
                "operator": log.operator,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }

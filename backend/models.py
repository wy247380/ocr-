"""
数据库模型 — 核心表（简化版，与 agent/router 字段对齐）
"""

from datetime import datetime

from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime,
    Float, JSON, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from .config import now_beijing

class Base(DeclarativeBase):
    pass


class PatentUpload(Base):
    __tablename__ = "patent_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False, unique=True, index=True)
    batch_id = Column(String(64), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    created_at = Column(DateTime, nullable=False, default=now_beijing)
    updated_at = Column(DateTime, nullable=False, default=now_beijing, onupdate=now_beijing)


class PdfRenderPage(Base):
    __tablename__ = "patent_pdf_render_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    page_no = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(128), nullable=True)
    dpi = Column(Integer, nullable=False, default=300)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class PdfSignatureReference(Base):
    __tablename__ = "patent_pdf_signature_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    has_signature = Column(Integer, nullable=False, default=0)
    local_verify_status = Column(String(50), nullable=True)
    signer_name = Column(String(255), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    is_modified_after_signing = Column(Integer, nullable=True)
    used_for_decision = Column(Integer, nullable=False, default=0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class PatentVisibleExtraction(Base):
    __tablename__ = "patent_visible_extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    ocr_provider = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=True)
    patent_no_raw = Column(String(100), nullable=True)
    patent_title = Column(Text, nullable=True)
    patent_type = Column(String(50), nullable=True)
    inventors = Column(Text, nullable=True)
    patentee = Column(Text, nullable=True)
    application_date = Column(String(20), nullable=True)
    grant_announcement_date = Column(String(20), nullable=True)
    publication_no = Column(String(100), nullable=True)
    avg_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class PdfTextLayer(Base):
    __tablename__ = "patent_pdf_text_layers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    raw_text = Column(Text, nullable=True)
    extracted_record = Column(JSON, nullable=True)
    has_text_layer = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class PatentOfficialRecord(Base):
    __tablename__ = "patent_official_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    source = Column(String(100), nullable=False, default="cnipa")
    query_key = Column(String(100), nullable=True)
    application_no = Column(String(100), nullable=True)
    patent_no = Column(String(100), nullable=True)
    patent_title = Column(Text, nullable=True)
    patent_type = Column(String(50), nullable=True)
    inventors = Column(Text, nullable=True)
    patentee = Column(Text, nullable=True)
    application_date = Column(String(20), nullable=True)
    grant_announcement_date = Column(String(20), nullable=True)
    legal_status = Column(String(255), nullable=True)
    publication_no = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class PatentVerificationResult(Base):
    __tablename__ = "patent_verification_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("patent_uploads.id"), nullable=False)
    verification_status = Column(String(50), nullable=False)
    auto_pass = Column(Integer, nullable=False, default=0)
    fail_reason = Column(Text, nullable=True)
    comparison_detail = Column(JSON, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_beijing)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, nullable=True, index=True)
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    operator = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime, nullable=False, default=now_beijing)

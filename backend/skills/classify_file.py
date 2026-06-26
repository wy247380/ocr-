"""
Skill: classify_uploaded_file — 判断上传文件类型
"""

import mimetypes
from pathlib import Path


def classify_uploaded_file(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"file_type": "unknown", "status": "error", "error": "文件不存在"}

    ext = path.suffix.lower()
    mime, _ = mimetypes.guess_type(str(path))

    pdf_exts = {".pdf"}
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".heic", ".webp"}

    if ext in pdf_exts or (mime and "pdf" in mime):
        return {
            "file_type": "pdf",
            "mime_type": mime or "application/pdf",
            "requires_pdf_render": True,
            "requires_image_preprocess": False,
            "status": "success",
        }
    elif ext in image_exts or (mime and mime.startswith("image/")):
        return {
            "file_type": "image",
            "mime_type": mime or f"image/{ext.lstrip('.')}",
            "requires_pdf_render": False,
            "requires_image_preprocess": True,
            "status": "success",
        }
    else:
        return {
            "file_type": "unknown",
            "mime_type": mime or "application/octet-stream",
            "requires_pdf_render": False,
            "requires_image_preprocess": False,
            "status": "unsupported",
        }

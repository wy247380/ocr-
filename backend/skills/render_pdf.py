"""
Skill: render_pdf_to_images — 将 PDF 每页渲染为高清图片
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ..config import PDF_RENDER_DPI, RENDERED_DIR


def render_pdf_to_images(file_path: str, dpi: int | None = None) -> dict:
    dpi = dpi or PDF_RENDER_DPI

    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {"status": "error", "error": "PyMuPDF 未安装，请运行: pip install pymupdf"}

    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "error": "PDF 文件不存在"}

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        return {"status": "error", "error": f"PDF 打开失败: {e}"}

    stem = path.stem
    task_dir = RENDERED_DIR / stem
    task_dir.mkdir(parents=True, exist_ok=True)

    page_images = []
    for page_no in range(len(doc)):
        page = doc[page_no]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img_path = task_dir / f"{stem}_page_{page_no + 1}.png"
        pix.save(str(img_path))

        img_hash = hashlib.sha256(img_path.read_bytes()).hexdigest()
        page_images.append({
            "page": page_no + 1,
            "image_path": str(img_path),
            "image_hash": img_hash,
        })

    doc.close()

    return {
        "status": "success",
        "page_count": len(page_images),
        "page_images": page_images,
    }

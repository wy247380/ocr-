"""
Skill: extract_pdf_text_layer — 提取 PDF 文本层用于辅助交叉检查
"""

import re
from pathlib import Path


def extract_pdf_text_layer(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "error": "文件不存在"}

    try:
        import fitz
    except ImportError:
        return {"status": "error", "error": "PyMuPDF 未安装"}

    try:
        doc = fitz.open(str(path))
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        return {"status": "error", "error": f"PDF 文本层提取失败: {e}"}

    if not full_text.strip():
        return {
            "status": "success",
            "text_layer_record": {},
            "raw_text": "",
            "has_text_layer": False,
        }

    record = _parse_text_layer(full_text)

    return {
        "status": "success",
        "text_layer_record": record,
        "raw_text": full_text,
        "has_text_layer": True,
    }


def _parse_text_layer(text: str) -> dict:
    record = {}

    match = re.search(r"[ZＺ][LＬ]\s*(\d{12,13}(?:\.\d)?)", text, re.IGNORECASE)
    if match:
        record["patent_no_raw"] = match.group(0).strip()

    match = re.search(r"(?:发明名称|专利名称)[：:]\s*(.+?)(?:\n|$)", text)
    if match:
        record["patent_title"] = match.group(1).strip()

    match = re.search(r"(?:发明人|设计人)[：:]\s*(.+?)(?:\n|$)", text)
    if match:
        record["inventors"] = [n.strip() for n in re.split(r"[，,、\s]+", match.group(1)) if n.strip()]

    match = re.search(r"(?:专利权人|申请人)[：:]\s*(.+?)(?:\n|$)", text)
    if match:
        record["patentee"] = [n.strip() for n in re.split(r"[，,、\s]+", match.group(1)) if n.strip()]

    return record

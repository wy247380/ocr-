"""
Skill: verify_pdf_signature_reference — PDF 签章参考验签（仅作为参考）
"""

from pathlib import Path


def verify_pdf_signature_reference(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return _no_signature("文件不存在")

    try:
        import fitz
        doc = fitz.open(str(path))
    except ImportError:
        return _no_signature("PyMuPDF 未安装")
    except Exception as e:
        return _no_signature(f"PDF 打开失败: {e}")

    # 检测是否含有签章 widget
    has_sig = False
    for page in doc:
        for widget in page.widgets():
            if widget.field_type_string == "Sig":
                has_sig = True
                break
        if has_sig:
            break

    doc.close()

    if not has_sig:
        return {
            "has_signature": False,
            "local_verify_status": "no_signature",
            "is_modified_after_signing": None,
            "signer_name": None,
            "signed_at": None,
            "used_for_decision": False,
            "note": "未检测到 PDF 签章",
        }

    # pyHanko 验签尝试
    try:
        from pyhanko.sign.validation import validate_pdf_signature
        from pyhanko.pdf_utils.reader import PdfFileReader

        with open(str(path), "rb") as f:
            reader = PdfFileReader(f)
            sigs = reader.embedded_signatures
            if not sigs:
                return {
                    "has_signature": True,
                    "local_verify_status": "no_embedded_signature",
                    "is_modified_after_signing": None,
                    "signer_name": None,
                    "signed_at": None,
                    "used_for_decision": False,
                    "note": "检测到签章 widget 但无嵌入签名数据",
                }

            sig = sigs[0]
            status = validate_pdf_signature(sig)

            return {
                "has_signature": True,
                "local_verify_status": "passed" if status.intact and status.valid else "failed",
                "is_modified_after_signing": not status.intact,
                "signer_name": str(status.signer_reported_name) if hasattr(status, "signer_reported_name") else None,
                "signed_at": None,
                "used_for_decision": False,
                "note": "PDF 签章仅作为辅助证据，不能作为自动通过依据",
            }

    except ImportError:
        return {
            "has_signature": True,
            "local_verify_status": "pyhanko_not_installed",
            "is_modified_after_signing": None,
            "signer_name": None,
            "signed_at": None,
            "used_for_decision": False,
            "note": "pyHanko 未安装，无法验签。签章结果仅作参考",
        }
    except Exception as e:
        return {
            "has_signature": True,
            "local_verify_status": "error",
            "is_modified_after_signing": None,
            "signer_name": None,
            "signed_at": None,
            "used_for_decision": False,
            "note": f"签章验签出错: {e}",
        }


def _no_signature(reason: str) -> dict:
    return {
        "has_signature": False,
        "local_verify_status": "error",
        "is_modified_after_signing": None,
        "signer_name": None,
        "signed_at": None,
        "used_for_decision": False,
        "note": reason,
    }

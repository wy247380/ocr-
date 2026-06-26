"""
Skill: extract_visible_patent_fields — OCR 提取可见专利字段
EasyOCR 提取文字 → 正则解析 → DeepSeek chat 纠错补全
"""
from __future__ import annotations

import re
import logging

from ..config import OCR_PROVIDER, OCR_CONFIDENCE_THRESHOLD, USE_LLM_OCR_PARSE

logger = logging.getLogger(__name__)


def extract_visible_patent_fields(image_paths: list[str]) -> dict:
    if not image_paths:
        return _empty_result("image_paths 为空")

    if OCR_PROVIDER == "easyocr":
        return _extract_with_easyocr(image_paths)
    elif OCR_PROVIDER == "paddle":
        return _extract_with_paddle(image_paths)
    elif OCR_PROVIDER == "vision_llm":
        return _extract_with_vision_llm(image_paths)
    else:
        return _extract_with_easyocr(image_paths)


# ── EasyOCR ──────────────────────────────────────────────

def _get_model_dir() -> str | None:
    """返回 EasyOCR 模型目录路径，找不到返回 None（将在线下载）。"""
    import sys
    from pathlib import Path
    # PyInstaller 打包后 sys._MEIPASS 是临时解压目录
    if getattr(sys, 'frozen', False):
        bundled = Path(sys._MEIPASS) / 'easyocr_models'
        if bundled.exists():
            return str(bundled)
    # 开发模式：项目根目录
    dev = Path(__file__).resolve().parent.parent.parent / 'easyocr_models'
    if dev.exists():
        return str(dev)
    # 用户缓存
    user = Path.home() / '.EasyOCR' / 'model'
    if user.exists():
        return str(user)
    return None


def _cpu_supports_avx2() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(40))
    except Exception:
        return True


def _easyocr_subprocess_worker(image_paths, result_file: str):
    """独立进程运行 EasyOCR，结果写入临时文件（避免 Queue 管道死锁）。"""
    try:
        import ctypes
        SEM_FAILCRITICALERRORS = 0x0001
        SEM_NOGPFAULTERRORBOX = 0x0002
        SEM_NOOPENFILEERRORBOX = 0x8000
        ctypes.windll.kernel32.SetErrorMode(
            SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX
        )
    except Exception:
        pass
    import json
    try:
        import numpy as np
        from PIL import Image
        import easyocr
        model_dir = _get_model_dir()
        reader = easyocr.Reader(
            ["ch_sim", "en"], gpu=False, verbose=False,
            model_storage_directory=model_dir,
            download_enabled=(model_dir is None),
        )
        texts = []
        for img_path in image_paths:
            img = Image.open(img_path).convert("RGB")
            for _, text, conf in reader.readtext(np.array(img)):
                texts.append({"text": text, "confidence": round(conf, 4)})
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "texts": texts}, f, ensure_ascii=False)
    except Exception as e:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "error": str(e)}, f, ensure_ascii=False)


def _extract_with_easyocr(image_paths: list[str]) -> dict:
    import multiprocessing as mp
    import json
    import tempfile
    import os

    if not _cpu_supports_avx2():
        logger.warning("CPU 不支持 AVX2，跳过 EasyOCR，回退 PaddleOCR")
        return _extract_with_paddle(image_paths)

    logger.info("EasyOCR 启动: 处理 %d 张图片", len(image_paths))

    # 用临时文件传递结果，避免 Queue 管道对大图片数据死锁
    fd, result_file = tempfile.mkstemp(suffix=".json", prefix="easyocr_")
    os.close(fd)

    ctx = mp.get_context("spawn")
    proc = ctx.Process(target=_easyocr_subprocess_worker, args=(image_paths, result_file), daemon=True)
    proc.start()
    proc.join(timeout=300)

    if proc.exitcode != 0 or proc.exitcode is None:
        logger.error("EasyOCR 子进程崩溃 exitcode=%s，回退 PaddleOCR", proc.exitcode)
        try:
            proc.kill()
        except Exception:
            pass
        _cleanup_file(result_file)
        return _extract_with_paddle(image_paths)

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        _cleanup_file(result_file)
        return _empty_result("EasyOCR 子进程结果读取失败")
    finally:
        _cleanup_file(result_file)

    if not data.get("ok"):
        logger.error("EasyOCR 错误: %s", data.get("error"))
        return _empty_result(f"EasyOCR 错误: {data.get('error')}")

    all_text = data["texts"]
    logger.info("EasyOCR 检测 %d 段文字", len(all_text))

    full_text = "\n".join(t["text"] for t in all_text)
    logger.info("EasyOCR 文字(前200字): %s", full_text[:200])
    result = _parse_fields(full_text, all_text)

    if USE_LLM_OCR_PARSE:
        result = _enhance_with_deepseek(full_text, result)

    return result


def _cleanup_file(path: str) -> None:
    try:
        import os
        os.unlink(path)
    except Exception:
        pass


# ── PaddleOCR (回退) ─────────────────────────────────────

def _extract_with_paddle(image_paths: list[str]) -> dict:
    all_text = []
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        for img_path in image_paths:
            ocr_result = ocr.ocr(img_path)
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    all_text.append({"text": line[1][0], "confidence": round(line[1][1], 4)})
    except ImportError:
        return _empty_result("PaddleOCR 未安装。请运行: pip install paddleocr")
    except Exception as e:
        return _empty_result(f"PaddleOCR 错误: {e}")

    full_text = "\n".join(t["text"] for t in all_text)
    result = _parse_fields(full_text, all_text)

    if USE_LLM_OCR_PARSE:
        result = _enhance_with_deepseek(full_text, result)

    return result


# ── Vision LLM (DeepSeek 多模态 API 就绪后启用) ──────────

def _extract_with_vision_llm(image_paths: list[str]) -> dict:
    try:
        from .deepseek_client import parse_image_ocr
    except ImportError as e:
        logger.error("deepseek_client 导入失败: %s", e)
        return _empty_result("deepseek_client 未找到")

    errors = []
    combined = _empty_result("")
    for img_path in image_paths[:2]:
        logger.info("Vision OCR 处理: %s", img_path)
        result = parse_image_ocr(img_path)
        if not result:
            errors.append(f"{img_path}: API 返回空")
            continue
        logger.info("Vision OCR 原始返回: %s", {k: v for k, v in result.items() if v})
        field_map = {
            "patent_no_normalized": result.get("patent_no"),
            "publication_no": result.get("publication_no"),
            "patent_title": result.get("patent_title"),
            "patent_type": result.get("patent_type"),
            "inventors": result.get("inventors"),
            "patentee": result.get("patentee"),
            "application_date": result.get("application_date"),
            "grant_announcement_date": result.get("grant_announcement_date"),
        }
        for k, v in field_map.items():
            if v and not combined.get(k):
                combined[k] = v

    if combined.get("publication_no") or combined.get("patent_no_normalized"):
        combined["application_no"] = combined.get("patent_no_normalized")
        combined["status"] = "success"
        combined["document_type"] = "patent_certificate"
        for key in combined.get("confidence", {}):
            combined["confidence"][key] = 0.90
        logger.info("Vision OCR 完成: pub=%s title=%s", combined.get("publication_no"), combined.get("patent_title"))
    else:
        combined["status"] = "failed"
        combined["error"] = "Vision OCR 未能提取有效字段; " + "; ".join(errors) if errors else "Vision OCR 未能提取有效字段"

    return combined


# ── 正则解析 ──────────────────────────────────────────────

def _parse_fields(full_text: str, all_text: list[dict]) -> dict:
    result = _empty_result("")
    result["raw_ocr_text"] = full_text
    result["evidence_text"] = [t["text"] for t in all_text[:20]]

    avg_conf = sum(t["confidence"] for t in all_text) / len(all_text) if all_text else 0

    # 专利号
    patent_patterns = [
        r"[ZＺ乙之][LＬl]\s*(\d[\d\s\.]{10,15})",
        r"(?:专利号|证书号)[：:\s]*[ZＺ乙之]?[LＬl]?\s*(\d[\d\s\.]{10,15})",
    ]
    for pattern in patent_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            raw = match.group(0).strip()
            result["patent_no_raw"] = raw
            normalized = _normalize_patent_no(raw)
            result["patent_no_normalized"] = normalized
            result["application_no"] = normalized
            result["confidence"]["patent_no"] = 0.95 if avg_conf > 0.8 else avg_conf
            result["confidence"]["application_no"] = result["confidence"]["patent_no"]
            break

    # 专利名称
    title_patterns = [
        r"(?:发明名称|专利名称|实用新型名称|外观设计名称|新型名称|新刑名称|用新.{0,2}名称)[：:\s]*\n?\s*(.+?)(?:\n|$)",
        r"名称\s*[:：]\s*\n?\s*(.+?)(?:\n|$)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, full_text)
        if match:
            title = match.group(1).strip().lstrip("-一")
            if len(title) >= 2:
                result["patent_title"] = title
                result["confidence"]["patent_title"] = 0.90 if avg_conf > 0.8 else avg_conf
                break

    if not result["patent_title"]:
        lines = full_text.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"名称\s*[:：]?$", line) and i + 1 < len(lines):
                title = lines[i + 1].strip().lstrip("-一")
                if len(title) >= 2 and not re.match(r"^[\d\s]+$", title):
                    result["patent_title"] = title
                    result["confidence"]["patent_title"] = 0.85
                    break

    # 专利类型
    if "发明专利" in full_text:
        result["patent_type"] = "发明专利"
    elif "实用新型" in full_text:
        result["patent_type"] = "实用新型专利"
    elif "外观设计" in full_text:
        result["patent_type"] = "外观设计专利"

    # 发明人
    inv_patterns = [
        r"(?<!\S)人\s*[:：]\s+(.+?)(?:\n(?:专|申|授|法|局|地|接)|$)",
        r"(?:发明人|设计人)\s*[:：]\s*(.+?)(?:\n(?:专|申|授|法|局|地|接)|$)",
        r"发明人\s*[:：]\s*\n\s*(.+?)(?:\n|$)",
        r"(?:发\s*明\s*人|发.{0,3}人)\s*[:：]\s*(.+?)(?:\n(?:专|申|授|法|局|地|接)|$)",
    ]
    for pattern in inv_patterns:
        match = re.search(pattern, full_text, re.DOTALL)
        if match:
            raw_names = match.group(1).strip()
            raw_names = raw_names.split("\n")[0]
            if re.search(r"信息|如下|记载|应当|依照", raw_names):
                continue
            names = [n.strip() for n in re.split(r"[，,、;；\s]+", raw_names) if n.strip() and len(n.strip()) >= 2]
            if names:
                result["inventors"] = names
                result["confidence"]["inventors"] = 0.90 if avg_conf > 0.8 else avg_conf
                break

    # 专利权人
    pat_patterns = [
        r"(?:专\s*利\s*权\s*人|专利权人|申请人)[：:\s]*(.+?)(?:\n(?:地|址|发|设|专利号|授|法|局|接)|$)",
    ]
    for pattern in pat_patterns:
        match = re.search(pattern, full_text, re.DOTALL)
        if match:
            raw_names = match.group(1).strip()
            raw_names = raw_names.split("\n")[0]
            names = [n.strip() for n in re.split(r"[，,、;；\s]+", raw_names) if n.strip() and len(n.strip()) >= 2]
            if names:
                result["patentee"] = names
                result["confidence"]["patentee"] = 0.90 if avg_conf > 0.8 else avg_conf
                break

    # 日期
    app_date_match = re.search(r"(?:申请日|请日|请\|)[：:\s]*(\d{4})[年午](\d{1,2})月(\d{1,2})", full_text)
    if app_date_match:
        result["application_date"] = f"{app_date_match.group(1)}-{app_date_match.group(2).zfill(2)}-{app_date_match.group(3).zfill(2)}"

    grant_date_match = re.search(r"(?:授权公告日|授权公s|接权公s|接权公告)[^:：]*[：:\s]*(\d{4})[年](\d{1,2})月(\d{1,2})", full_text)
    if grant_date_match:
        result["grant_announcement_date"] = f"{grant_date_match.group(1)}-{grant_date_match.group(2).zfill(2)}-{grant_date_match.group(3).zfill(2)}"

    if not result.get("application_date") or not result.get("grant_announcement_date"):
        date_pattern = r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})"
        dates = re.findall(date_pattern, full_text)
        if dates and not result.get("application_date"):
            result["application_date"] = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}"
        if len(dates) >= 2 and not result.get("grant_announcement_date"):
            result["grant_announcement_date"] = f"{dates[-1][0]}-{dates[-1][1].zfill(2)}-{dates[-1][2].zfill(2)}"

    # 公开号
    pub_patterns = [
        r"(?:公开号|公告号|公布号|公苦)[：:\s!]*\n?\s*(CN\s*\d{7,13}\s*[A-Z]?)",
        r"(CN\s*\d{7,13}\s*[A-Z]?)",
    ]
    for pattern in pub_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            raw_pub = match.group(1).replace(" ", "")
            result["publication_no"] = raw_pub
            break

    if result["patent_no_normalized"] or result.get("publication_no"):
        result["document_type"] = "patent_certificate"
        result["status"] = "success"
    else:
        result["document_type"] = "unknown"
        result["status"] = "patent_no_missing"
        result["uncertain_fields"].append("patent_no")

    for field in ["patent_no", "application_no", "patent_title", "inventors", "patentee"]:
        if result["confidence"].get(field, 0) < OCR_CONFIDENCE_THRESHOLD:
            if field not in result["uncertain_fields"]:
                result["uncertain_fields"].append(field)

    return result


def _normalize_patent_no(value: str) -> str | None:
    if not value:
        return None
    s = value.upper().strip()
    s = s.replace("ＺＬ", "ZL").replace("ＣＮ", "CN")
    for prefix in ["ZL", "CN", "乙L", "之L", "乙l", "之l"]:
        s = s.replace(prefix, "")
    s = re.sub(r"[\s\.\-_/]", "", s)
    s = re.sub(r"[^0-9X]", "", s)
    if 9 <= len(s) <= 13:
        return s
    return None


def _empty_result(error: str) -> dict:
    return {
        "document_type": "unknown",
        "patent_no_raw": None,
        "patent_no_normalized": None,
        "application_no": None,
        "publication_no": None,
        "patent_title": None,
        "patent_type": None,
        "inventors": [],
        "patentee": [],
        "application_date": None,
        "grant_announcement_date": None,
        "confidence": {
            "patent_no": 0, "application_no": 0,
            "patent_title": 0, "inventors": 0, "patentee": 0,
        },
        "uncertain_fields": [],
        "evidence_text": [],
        "raw_ocr_text": "",
        "status": "failed" if error else "pending",
        "error": error,
    }


# ── DeepSeek chat 校正 ────────────────────────────────────

def _enhance_with_deepseek(ocr_text: str, regex_result: dict) -> dict:
    """用 DeepSeek V4 flash 校正和补全 OCR 结果。"""
    try:
        from .deepseek_client import parse_ocr_text
    except ImportError:
        return regex_result

    ds_result = parse_ocr_text(ocr_text)
    if not ds_result:
        return regex_result

    field_map = {
        "publication_no": "publication_no",
        "patent_title": "patent_title",
        "inventors": "inventors",
        "patentee": "patentee",
        "patent_no": "patent_no_normalized",
        "patent_type": "patent_type",
        "application_date": "application_date",
        "grant_announcement_date": "grant_announcement_date",
    }

    for ds_key, local_key in field_map.items():
        ds_val = ds_result.get(ds_key)
        if not ds_val:
            continue

        local_val = regex_result.get(local_key)
        conf_key = ds_key.replace("_normalized", "")
        local_conf = regex_result.get("confidence", {}).get(conf_key, 0)

        should_override = (
            not local_val
            or (isinstance(local_val, list) and len(local_val) == 0)
            or local_conf < 0.85
        )

        if should_override:
            if local_key in ("inventors", "patentee"):
                if isinstance(ds_val, list):
                    regex_result[local_key] = ds_val
                elif isinstance(ds_val, str):
                    regex_result[local_key] = [
                        n.strip() for n in re.split(r"[，,、;；]+", ds_val)
                        if n.strip()
                    ]
            else:
                regex_result[local_key] = ds_val
            regex_result["confidence"][conf_key] = 0.92

    if regex_result.get("publication_no"):
        regex_result["status"] = "success"
        regex_result["document_type"] = "patent_certificate"

    logger.info("DeepSeek 校正完成: pub=%s title=%s inv=%s",
                regex_result.get("publication_no"),
                regex_result.get("patent_title"),
                regex_result.get("inventors"))
    return regex_result

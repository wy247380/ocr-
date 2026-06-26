"""
DeepSeek API 客户端 — 双模型架构
- deepseek-chat (V4): 用于 OCR 文本解析（快速、低成本）
- deepseek-reasoner (V4): 用于官方页面解析和字段比对（高精度推理）

兼容 Windows 7 + Python 3.8+
"""
from __future__ import annotations

import json
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CACHE_FILE = str(Path.home() / ".patent_verify_deepseek_cache.json")

_OCR_SYSTEM_PROMPT = (
    "你是专利信息提取助手。从用户发送的OCR识别文字中提取专利信息，只返回JSON。"
    "注意：OCR经常出现形近字错误（如'固'误识为'旧'、'加固'误识为'加旧'、"
    "'墙'误识为'牆'等），请根据专利领域常见术语和上下文语义进行纠错。"
    "专利名称应该是有意义的技术描述，如果某个字明显不通顺请推断正确的字。\n"
    "找不到的字段填null。字段名必须是以下英文名：\n"
    "patent_no (专利号，如ZL202321160956.9)、"
    "publication_no (公开/公告号，如CN219910140U)、"
    "patent_title (专利名称，注意纠正OCR形近字错误)、"
    "patent_type (专利类型：发明专利/实用新型专利/外观设计专利)、"
    "inventors (发明人列表，数组格式)、"
    "patentee (专利权人列表，数组格式)、"
    "application_date (申请日，格式YYYY-MM-DD)、"
    "grant_announcement_date (授权公告日，格式YYYY-MM-DD)"
)

_OFFICIAL_SYSTEM_PROMPT = (
    "你是专利信息提取助手。从用户发送的官方网站页面文字中提取专利信息，只返回JSON。\n"
    "重要：patent_title 必须去掉前缀如 [实用新型]、[发明授权]、[外观设计] 等方括号标签，只保留纯专利名称。\n"
    "找不到的字段填null。字段名必须是以下英文名：\n"
    "patent_no (专利号)、publication_no (公开/公告号)、"
    "patent_title (专利名称，去掉[xxx]前缀)、patent_type (专利类型)、"
    "inventors (发明人列表，数组格式)、patentee (专利权人列表，数组格式)、"
    "application_date (申请日，YYYY-MM-DD)、"
    "grant_announcement_date (授权公告日，YYYY-MM-DD)、"
    "legal_status (法律状态)"
)

_COMPARE_SYSTEM_PROMPT = (
    "你是专利核验助手。比较OCR提取字段与官方记录，判断是否一致。\n"
    "只比较以下三个字段：inventors(发明人)、patent_title(专利名称)、publication_no(公开号)。\n"
    "返回JSON格式：{\"match\": true/false, \"field_details\": ["
    "{\"field_key\": \"...\", \"field_label\": \"...\", \"ocr_value\": \"...\", "
    "\"official_value\": \"...\", \"matched\": true/false, \"reason\": \"...\"}]}"
)


def _load_cache() -> dict:
    try:
        if Path(_CACHE_FILE).exists():
            return json.loads(Path(_CACHE_FILE).read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        Path(_CACHE_FILE).write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


def _make_cache_key(text: str, model: str) -> str:
    normalized = re.sub(r"\s+", "", text)[:200]
    return "%s_%s" % (model, hash(normalized))


def call_deepseek(
    text: str,
    system_prompt: str,
    model: str = "chat",
    use_cache: bool = True,
) -> Optional[dict]:
    """
    调用 DeepSeek V4 API 解析文本。
    model: "chat" 普通模式（快速）, "reasoner" 启用 thinking 模式（深度推理）
    两者默认都用 deepseek-v4-flash 模型，reasoner 通过 thinking 参数启用推理。
    """
    from ..config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL_CHAT, DEEPSEEK_MODEL_REASONER

    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY 未配置，跳过 DeepSeek 解析")
        return None

    model_name = DEEPSEEK_MODEL_REASONER if model == "reasoner" else DEEPSEEK_MODEL_CHAT
    cache_key = _make_cache_key(text, model_name + "_" + model)

    if use_cache:
        cache = _load_cache()
        if cache_key in cache:
            logger.info("DeepSeek 缓存命中 (model=%s, mode=%s)", model_name, model)
            return cache[cache_key]

    try:
        import requests
    except ImportError:
        logger.error("requests 库未安装")
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text[:50000]},
    ]

    request_body = {
        "model": model_name,
        "messages": messages,
        "max_tokens": 2048,
        "stream": False,
    }

    # reasoner 模式启用 thinking（深度推理）
    if model == "reasoner":
        request_body["thinking"] = {"type": "enabled"}
        request_body["reasoning_effort"] = "high"
    else:
        request_body["temperature"] = 0

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": "Bearer " + DEEPSEEK_API_KEY,
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=60,
            proxies={"http": None, "https": None},
        )
        if resp.status_code != 200:
            logger.error("DeepSeek API [%s/%s] 返回 %d: %s", model_name, model, resp.status_code, resp.text[:200])
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            logger.warning("DeepSeek [%s/%s] 返回内容中未找到 JSON", model_name, model)
            return None

        result = json.loads(match.group())

        if use_cache:
            cache = _load_cache()
            cache[cache_key] = result
            if len(cache) > 500:
                keys = list(cache.keys())
                for k in keys[:100]:
                    del cache[k]
            _save_cache(cache)

        return result

    except Exception as e:
        logger.error("DeepSeek API [%s/%s] 调用失败: %s", model_name, model, e)
        return None


def parse_image_ocr(image_path: str) -> Optional[dict]:
    """用 DeepSeek Vision 模型直接从图片提取专利字段（无需本地OCR）。"""
    import base64
    from ..config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL_VISION

    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY 未配置，跳过 Vision OCR")
        return None

    if not DEEPSEEK_MODEL_VISION:
        logger.warning("DEEPSEEK_MODEL_VISION 未配置，跳过 Vision OCR")
        return None

    try:
        import requests
        logger.info("Vision API 调用: model=%s url=%s image=%s", DEEPSEEK_MODEL_VISION, DEEPSEEK_API_URL, Path(image_path).name)

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        suffix = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/png" if suffix == "png" else "image/jpeg"

        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL_VISION,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                        {"type": "text", "text": _OCR_SYSTEM_PROMPT + "\n请从图片中直接识别专利证书内容并返回JSON。"},
                    ],
                }],
                "max_tokens": 2048,
            },
            timeout=120,
            proxies={"http": None, "https": None},
        )
        if resp.status_code != 200:
            logger.error("Vision API 返回 %d: %s", resp.status_code, resp.text[:500])
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        logger.info("Vision API 响应内容(前300字): %s", content[:300])
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            logger.warning("Vision API 响应中未找到 JSON: %s", content[:200])
            return None
        return json.loads(match.group())

    except Exception as e:
        logger.error("Vision OCR 失败: %s", e)
        return None


def parse_ocr_text(ocr_text: str) -> Optional[dict]:
    """用 deepseek-chat 解析 OCR 原始文本（快速）。"""
    return call_deepseek(ocr_text, _OCR_SYSTEM_PROMPT, model="chat")


def parse_official_page(page_text: str) -> Optional[dict]:
    """用 deepseek-reasoner 解析官方网站页面文本（高精度推理）。"""
    return call_deepseek(page_text, _OFFICIAL_SYSTEM_PROMPT, model="reasoner", use_cache=False)


def compare_fields_with_llm(ocr_fields: dict, official_fields: dict) -> Optional[dict]:
    """用 deepseek-reasoner 进行字段比对（高精度推理）。"""
    prompt_text = (
        "OCR提取结果：\n%s\n\n官方记录：\n%s"
        % (json.dumps(ocr_fields, ensure_ascii=False), json.dumps(official_fields, ensure_ascii=False))
    )
    return call_deepseek(prompt_text, _COMPARE_SYSTEM_PROMPT, model="reasoner", use_cache=False)

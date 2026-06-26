"""
路由: 系统设置 — DeepSeek API Key 管理等
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

_SETTINGS_FILE = str(Path.home() / ".patent_verify_settings.json")


class SettingsModel(BaseModel):
    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/chat/completions"
    deepseek_model_chat: str = "deepseek-v4-flash"
    deepseek_model_reasoner: str = "deepseek-v4-flash"
    deepseek_model_vision: str = "deepseek-vl2"
    ocr_provider: str = "easyocr"
    use_llm_ocr_parse: bool = True
    use_llm_compare: bool = True


def _load_settings() -> dict:
    try:
        if Path(_SETTINGS_FILE).exists():
            return json.loads(Path(_SETTINGS_FILE).read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_settings(data: dict) -> None:
    Path(_SETTINGS_FILE).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _apply_settings(data: dict) -> None:
    """将设置应用到运行时环境变量和 config 模块。"""
    from ..config import (
        DEEPSEEK_API_KEY as _,
    )
    import backend.config as cfg

    if data.get("deepseek_api_key"):
        os.environ["DEEPSEEK_API_KEY"] = data["deepseek_api_key"]
        cfg.DEEPSEEK_API_KEY = data["deepseek_api_key"]
    if data.get("deepseek_api_url"):
        os.environ["DEEPSEEK_API_URL"] = data["deepseek_api_url"]
        cfg.DEEPSEEK_API_URL = data["deepseek_api_url"]
    if data.get("deepseek_model_chat"):
        os.environ["DEEPSEEK_MODEL_CHAT"] = data["deepseek_model_chat"]
        cfg.DEEPSEEK_MODEL_CHAT = data["deepseek_model_chat"]
    if data.get("deepseek_model_reasoner"):
        os.environ["DEEPSEEK_MODEL_REASONER"] = data["deepseek_model_reasoner"]
        cfg.DEEPSEEK_MODEL_REASONER = data["deepseek_model_reasoner"]
    if data.get("deepseek_model_vision"):
        os.environ["DEEPSEEK_MODEL_VISION"] = data["deepseek_model_vision"]
        cfg.DEEPSEEK_MODEL_VISION = data["deepseek_model_vision"]
    if data.get("ocr_provider"):
        os.environ["OCR_PROVIDER"] = data["ocr_provider"]
        cfg.OCR_PROVIDER = data["ocr_provider"]

    cfg.USE_LLM_OCR_PARSE = data.get("use_llm_ocr_parse", True)
    cfg.USE_LLM_COMPARE = data.get("use_llm_compare", True)


# 启动时加载已保存的设置
_saved = _load_settings()
if _saved:
    _apply_settings(_saved)


@router.get("")
async def get_settings():
    """获取当前设置（API Key 脱敏显示）。"""
    data = _load_settings()
    key = data.get("deepseek_api_key", "")
    masked = ""
    if key and len(key) > 8:
        masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
    elif key:
        masked = "****"

    return {
        "deepseek_api_key_masked": masked,
        "deepseek_api_key_set": bool(key),
        "deepseek_api_url": data.get("deepseek_api_url", "https://api.deepseek.com/chat/completions"),
        "deepseek_model_chat": data.get("deepseek_model_chat", "deepseek-v4-flash"),
        "deepseek_model_reasoner": data.get("deepseek_model_reasoner", "deepseek-v4-flash"),
        "deepseek_model_vision": data.get("deepseek_model_vision", "deepseek-vl2"),
        "ocr_provider": data.get("ocr_provider", "easyocr"),
        "use_llm_ocr_parse": data.get("use_llm_ocr_parse", True),
        "use_llm_compare": data.get("use_llm_compare", True),
    }


@router.post("")
async def save_settings(settings: SettingsModel):
    """保存设置到本地文件并应用到运行时。"""
    data = settings.dict()

    # 如果前端传回来的是掩码值，保留原有的 key
    if "****" in data.get("deepseek_api_key", "") or not data.get("deepseek_api_key"):
        old = _load_settings()
        if old.get("deepseek_api_key"):
            data["deepseek_api_key"] = old["deepseek_api_key"]

    _save_settings(data)
    _apply_settings(data)

    return {"status": "ok", "message": "设置已保存"}


@router.post("/test-deepseek")
async def test_deepseek_connection():
    """测试 DeepSeek V4 API 连接（flash 模型两种模式分别测试）。"""
    from ..config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL_CHAT, DEEPSEEK_MODEL_REASONER

    if not DEEPSEEK_API_KEY:
        return {"status": "error", "message": "API Key 未配置"}

    results = {}
    try:
        import requests

        # 测试 chat 模式（普通，快速）
        body_chat = {
            "model": DEEPSEEK_MODEL_CHAT,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 10,
            "temperature": 0,
            "stream": False,
        }
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"},
            json=body_chat,
            timeout=15,
            proxies={"http": None, "https": None},
        )
        results["chat"] = "ok (%s)" % DEEPSEEK_MODEL_CHAT if resp.status_code == 200 else "HTTP %d" % resp.status_code

        # 测试 reasoner 模式（thinking 启用）
        body_reasoner = {
            "model": DEEPSEEK_MODEL_REASONER,
            "messages": [{"role": "user", "content": "1+1=?"}],
            "max_tokens": 50,
            "thinking": {"type": "enabled"},
            "stream": False,
        }
        resp2 = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"},
            json=body_reasoner,
            timeout=20,
            proxies={"http": None, "https": None},
        )
        results["reasoner"] = "ok (%s+thinking)" % DEEPSEEK_MODEL_REASONER if resp2.status_code == 200 else "HTTP %d" % resp2.status_code

    except Exception as e:
        return {"status": "error", "message": str(e)}

    all_ok = all("ok" in v for v in results.values())
    msg = "chat: %s | reasoner: %s" % (results.get("chat", "未测"), results.get("reasoner", "未测"))
    return {"status": "ok" if all_ok else "partial", "message": msg, "details": results}

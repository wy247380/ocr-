"""
全局配置
"""

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 用户数据目录 — 放在用户主目录下，避免 C:\Program Files\ 权限问题
_USER_DATA_DIR = Path(os.getenv("PATENT_VERIFY_DATA_DIR", str(Path.home() / ".patent_verify")))

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(_USER_DATA_DIR / "uploads")))
RENDERED_DIR = Path(os.getenv("RENDERED_DIR", str(_USER_DATA_DIR / "rendered")))
PREPROCESSED_DIR = Path(os.getenv("PREPROCESSED_DIR", str(_USER_DATA_DIR / "preprocessed")))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_USER_DATA_DIR}/patent_verify.db")

PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "300"))

OCR_PROVIDER = os.getenv("OCR_PROVIDER", "easyocr")
OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.90"))

TITLE_SIMILARITY_THRESHOLD = float(os.getenv("TITLE_SIMILARITY_THRESHOLD", "0.92"))
SIMILARITY_THRESHOLD = TITLE_SIMILARITY_THRESHOLD

CNIPA_QUERY_URL = os.getenv("CNIPA_QUERY_URL", "https://pss-system.cponline.cnipa.gov.cn/conventionalSearch")
CNIPA_CDP_PORT_START = int(os.getenv("CNIPA_CDP_PORT_START", "9222"))
CNIPA_LOGIN_TIMEOUT = int(os.getenv("CNIPA_LOGIN_TIMEOUT", "300000"))

# Chrome 自定义路径（Win7 用户可指定 Chrome ≤ v109 的路径，或放 ./chrome/chrome.exe）
CNIPA_CHROME_PATH = os.getenv("CNIPA_CHROME_PATH", "")

THIRD_PARTY_API_KEY = os.getenv("THIRD_PARTY_API_KEY", "")
THIRD_PARTY_API_URL = os.getenv("THIRD_PARTY_API_URL", "")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL_CHAT = os.getenv("DEEPSEEK_MODEL_CHAT", "deepseek-v4-flash")
DEEPSEEK_MODEL_REASONER = os.getenv("DEEPSEEK_MODEL_REASONER", "deepseek-v4-flash")
DEEPSEEK_MODEL_VISION = os.getenv("DEEPSEEK_MODEL_VISION", "deepseek-vl2")
USE_LLM_COMPARE = os.getenv("USE_LLM_COMPARE", "true").lower() in ("true", "1", "yes")
USE_LLM_OCR_PARSE = os.getenv("USE_LLM_OCR_PARSE", "true").lower() in ("true", "1", "yes")

BEIJING_TZ = timezone(timedelta(hours=8))


def now_beijing() -> datetime:
    return datetime.now(BEIJING_TZ)


for d in [UPLOAD_DIR, RENDERED_DIR, PREPROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

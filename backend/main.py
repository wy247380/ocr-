"""
FastAPI 应用主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .database import init_db
from .routers import upload_router, tasks_router, admin_router
from .routers.settings import router as settings_router

app = FastAPI(
    title="专利证书可见内容核验智能体",
    version="2.0.0",
    description="上传专利证书 → OCR提取 → 官方查询 → 自动比对 → 人工审核",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.on_event("shutdown")
def on_shutdown():
    from .skills.query_official import shutdown_chrome
    shutdown_chrome()


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "patent_verify_agent_v2"}


app.include_router(upload_router)
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(settings_router)

# 静态文件挂载必须在所有 API 路由之后，否则会拦截 /api/* 请求
# 兼容开发环境和 PyInstaller 打包环境
import sys as _sys
_dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if not _dist_path.exists() and getattr(_sys, 'frozen', False):
    # PyInstaller: 检查 sys._MEIPASS
    _meipass = getattr(_sys, '_MEIPASS', '')
    if _meipass:
        _dist_path = Path(_meipass) / "frontend" / "dist"
if _dist_path.exists():
    app.mount("/", StaticFiles(directory=str(_dist_path), html=True), name="frontend")

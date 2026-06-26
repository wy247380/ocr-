# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — 专利证书核验系统
兼容 Windows 7 (Python 3.8.10) 和 Windows 10+

构建命令:
    pyinstaller PatentVerifyAgent.spec

输出:
    dist/专利证书核验系统/专利证书核验系统.exe
"""

import sys
from pathlib import Path

# SPECPATH = spec 文件所在目录
PROJECT_ROOT = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(PROJECT_ROOT / 'desktop' / 'desktop_app.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # 后端代码
        (str(PROJECT_ROOT / 'backend'), 'backend'),
        # 前端 dist
        (str(PROJECT_ROOT / 'frontend' / 'dist'), 'frontend/dist'),
        # EasyOCR 离线模型
        (str(PROJECT_ROOT / 'easyocr_models'), 'easyocr_models'),
    ],
    hiddenimports=[
        # FastAPI & Uvicorn
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'starlette', 'starlette.middleware', 'starlette.routing',
        'fastapi', 'fastapi.middleware', 'fastapi.openapi',
        # SQLAlchemy
        'sqlalchemy', 'sqlalchemy.ext', 'sqlalchemy.sql',
        # Playwright
        'playwright', 'playwright._impl',
        'greenlet',
        # EasyOCR
        'easyocr', 'easyocr.model',
        'torch', 'torchvision',
        'numpy', 'numpy.core',
        'PIL', 'PIL.Image',
        # PyMuPDF
        'fitz',
        # Other
        'requests', 'urllib3',
        'multipart', 'multipart.multipart',
        'json', 'csv', 'io', 'hashlib',
        'asyncio', 'concurrent.futures',
        'queue', 'socket', 'subprocess',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'IPython', 'jupyter',
        'notebook', 'sphinx', 'pytest', 'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='专利证书核验系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口以便查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='专利证书核验系统',
)

@echo off
title PatentVerifyAgent
echo ========================================
echo   Patent Certificate Verify System v2.0
echo   Starting server...
echo ========================================

cd /d "%~dp0"

set UPLOAD_DIR=%~dp0data\uploads
set DATABASE_URL=sqlite:///%~dp0data\patent_verify.db
set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright-browsers
set EASYOCR_MODULE_PATH=%~dp0python\.EasyOCR

if not exist "data\uploads" mkdir "data\uploads"

start "" /B python\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo Waiting for server to start...
timeout /t 5 /nobreak >nul

echo Opening browser...
start http://127.0.0.1:8000

echo.
echo Server is running at: http://127.0.0.1:8000
echo Close this window to stop the server.
echo.
pause
taskkill /f /im python.exe >nul 2>&1
@echo off
chcp 65001 >nul
echo ============================================================
echo   专利证书核验系统 — 打包构建脚本
echo   Patent Certificate Verification Agent v2.0
echo ============================================================
echo.

set PROJECT_DIR=%~dp0..
cd /d "%PROJECT_DIR%"

echo [1/4] 构建前端...
cd frontend
call npm run build
if errorlevel 1 (
    echo 前端构建失败！
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] 安装打包依赖...
pip install pyinstaller -q 2>nul
echo 安装 PyTorch 1.13.1 CPU-only (Win7 AVX2 兼容)...
pip install torch==1.13.1+cpu torchvision==0.14.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu -q
echo 安装其余依赖...
pip install -r backend\requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu -q

echo.
echo [3/4] PyInstaller 打包...
pyinstaller --clean desktop\PatentVerifyAgent.spec
if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo [4/4] 复制附加文件...

set DIST_DIR=dist\专利证书核验系统

:: 复制 README（如存在）
if exist "README.md" copy "README.md" "%DIST_DIR%\" >nul 2>nul

:: Win7 Chrome 提示
echo Windows 7 用户请注意：> "%DIST_DIR%\Win7用户必读.txt"
echo.>> "%DIST_DIR%\Win7用户必读.txt"
echo 请将 Chrome 浏览器 (v109 或更低版本) 的 chrome.exe>> "%DIST_DIR%\Win7用户必读.txt"
echo 放入本目录下的 chrome\ 文件夹中。>> "%DIST_DIR%\Win7用户必读.txt"
echo.>> "%DIST_DIR%\Win7用户必读.txt"
echo Chrome v109 下载地址：>> "%DIST_DIR%\Win7用户必读.txt"
echo https://www.slimjet.com/chrome/google-chrome-old-version.php>> "%DIST_DIR%\Win7用户必读.txt"
echo.>> "%DIST_DIR%\Win7用户必读.txt"
echo 或设置环境变量 CNIPA_CHROME_PATH 指向 chrome.exe 路径。>> "%DIST_DIR%\Win7用户必读.txt"
echo.>> "%DIST_DIR%\Win7用户必读.txt"
echo Windows 10+ 用户无需额外配置，系统会自动使用已安装的 Chrome。>> "%DIST_DIR%\Win7用户必读.txt"

echo.
echo ============================================================
echo   打包完成！
echo   输出目录: %DIST_DIR%
echo   可执行文件: %DIST_DIR%\专利证书核验系统.exe
echo ============================================================
pause

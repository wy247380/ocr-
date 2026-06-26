@echo off
chcp 65001 >nul
echo ========================================
echo   专利证书核验系统 — 打包脚本
echo ========================================
echo.

:: 1. 构建前端
echo [1/4] 构建 Vue 3 前端...
cd /d "%~dp0..\frontend"
call npm install
call npm run build
if errorlevel 1 (
    echo 前端构建失败！
    pause
    exit /b 1
)
echo 前端构建完成。
echo.

:: 2. 准备 Python 嵌入式环境
echo [2/4] 准备 Python 嵌入式运行时...
cd /d "%~dp0"
if not exist "python" (
    echo 请先下载 Python 3.11 嵌入式版本并解压到 desktop\python\ 目录
    echo 下载地址: https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
    echo.
    echo 解压后还需:
    echo   1. 下载 get-pip.py 并运行: python\python.exe get-pip.py
    echo   2. 编辑 python\python311._pth，取消 import site 的注释
    echo   3. 安装依赖: python\python.exe -m pip install -r ..\backend\requirements.txt --target python\Lib\site-packages
    echo.
    pause
    exit /b 1
)
echo Python 运行时就绪。
echo.

:: 3. 安装 Python 依赖到嵌入式环境
echo [3/4] 安装 Python 依赖...
python\python.exe -m pip install -r ..\backend\requirements.txt --target python\Lib\site-packages --quiet
if errorlevel 1 (
    echo 依赖安装失败！
    pause
    exit /b 1
)
echo 依赖安装完成。
echo.

:: 4. 编译 Inno Setup 安装包
echo [4/4] 编译安装包...
where iscc >nul 2>&1
if errorlevel 1 (
    echo Inno Setup 未安装或未在 PATH 中。
    echo 请安装 Inno Setup 6: https://jrsoftware.org/isdl.php
    echo 或手动编译: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
    pause
    exit /b 1
)
iscc setup.iss
if errorlevel 1 (
    echo 安装包编译失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！安装程序位于 desktop\output\ 目录
echo ========================================
pause

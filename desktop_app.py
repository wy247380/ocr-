"""
桌面入口 — 专利证书核验系统
启动后端服务 + 自动打开浏览器
支持 PyInstaller 打包后运行 (sys.frozen)
兼容 Windows 7 (Python 3.8.10)
"""
import os
import sys
import time
import io
import traceback
import threading
import webbrowser
from pathlib import Path

# 全局崩溃日志文件（兼容中英文 Windows 桌面路径）
def _get_desktop_path() -> str:
    """获取桌面路径（中文Win7=桌面, 英文=Desktop）。"""
    try:
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf)
        return buf.value
    except Exception:
        return str(Path.home() / "Desktop")

_DESKTOP = _get_desktop_path()
_CRASH_LOG = str(Path(_DESKTOP) / "patent_verify_crash.log")


def _setup_crash_handler():
    """捕获所有未处理异常，写入崩溃日志。"""
    def _handler(exc_type, exc_val, exc_tb):
        tb_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
        msg = "[%s] 未捕获异常:\n%s\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            "".join(tb_lines),
        )
        try:
            with io.open(_CRASH_LOG, "a", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_val, exc_tb)
        sys.stderr.write(msg)
    sys.excepthook = _handler


_TRACE_LOG = str(Path(_DESKTOP) / "patent_verify_trace.log")


def _trace(msg: str):
    """写入启动跟踪日志（立即刷盘，确保硬崩溃前写入）。"""
    try:
        with io.open(_TRACE_LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


# multiprocessing freeze_support 必须最早调用（PyInstaller + Windows spawn 模式必须）
import multiprocessing as _mp
_mp.freeze_support()

# 最早写入——在任何 import 之前
_trace("=== 程序启动 ===")
_trace("Python: %s | Platform: %s | Frozen: %s" % (
    sys.version, sys.platform, getattr(sys, 'frozen', False)))
_setup_crash_handler()
_trace("崩溃处理器已安装")


def get_base_dir():
    """获取资源根目录（开发时=项目根，打包后=exe所在目录）。"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _setup_pyinstaller_paths(base_dir: Path):
    """PyInstaller 打包后设置模块搜索路径。"""
    if not getattr(sys, 'frozen', False):
        return
    # _internal 目录包含所有 Python 模块
    internal_dir = base_dir / "_internal"
    if internal_dir.exists() and str(internal_dir) not in sys.path:
        sys.path.insert(0, str(internal_dir))
        print("已添加 _internal 到 sys.path")


def _check_win7_chrome(base_dir: Path):
    """Win7 环境检测并引导安装 Chrome v109。"""
    import platform
    try:
        if not platform.version().startswith("6.1"):
            return  # 不是 Win7，跳过
    except Exception:
        return

    # 检查是否已有可用的 Chrome ≤v109
    chrome_exe = base_dir / "chrome" / "chrome.exe"
    if chrome_exe.exists():
        return  # 已经有 Chrome

    # 检查是否有安装包
    installer = base_dir / "chrome" / "Chrome_109.0.5414.120_64bit.exe"
    if installer.exists():
        print("检测到 Windows 7，正在安装兼容的 Chrome v109...")
        print("这可能需要几分钟，请勿关闭此窗口。")
        import subprocess
        try:
            subprocess.run(
                [str(installer), "/silent", "/install"],
                check=True, timeout=180,
            )
            print("Chrome v109 安装完成。")
            # 安装后检测
            for d in [
                Path("C:/Program Files/Google/Chrome/Application"),
                Path("C:/Program Files (x86)/Google/Chrome/Application"),
            ]:
                if d.exists():
                    exe = d / "chrome.exe"
                    if exe.exists():
                        os.environ["CNIPA_CHROME_PATH"] = str(exe)
                        return
        except Exception as e:
            print("Chrome 自动安装失败: %s" % e)
            print("请手动运行: %s" % installer)
    else:
        print("Windows 7 需要 Chrome v109 或更低版本。")
        print("请将 chrome.exe 放入: %s" % (base_dir / "chrome"))


def _setup_env(base_dir: Path):
    """设置运行时环境变量。数据目录使用用户主目录，避免 Program Files 权限问题。"""
    user_data = Path.home() / ".patent_verify"
    os.environ["UPLOAD_DIR"] = str(user_data / "uploads")
    os.environ["DATABASE_URL"] = f"sqlite:///{user_data / 'patent_verify.db'}"
    # Win7 Chrome 自动安装
    _check_win7_chrome(base_dir)
    # Chrome 路径自动检测
    if not os.getenv("CNIPA_CHROME_PATH"):
        for d in [base_dir, base_dir / "chrome"]:
            p = d / "chrome.exe"
            if p.exists():
                os.environ["CNIPA_CHROME_PATH"] = str(p)
                break

    # 自动部署 EasyOCR 模型（将捆绑的模型复制到用户缓存目录）
    _deploy_easyocr_models(base_dir)

    (user_data / "uploads").mkdir(parents=True, exist_ok=True)


def _deploy_easyocr_models(base_dir: Path):
    """将捆绑的 EasyOCR 模型复制到用户目录，避免首次运行需下载。"""
    import shutil
    bundled = base_dir / "easyocr_models"
    target = Path.home() / ".EasyOCR" / "model"
    if not bundled.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for f in bundled.glob("*.pth"):
        dest = target / f.name
        if not dest.exists():
            try:
                shutil.copy2(str(f), str(dest))
                print("已部署 EasyOCR 模型: %s" % f.name)
            except Exception as e:
                print("模型部署失败 %s: %s" % (f.name, e))


def run_server(host="127.0.0.1", port=8000):
    """在同一进程中启动 uvicorn（PyInstaller 兼容方式）。"""
    _trace("uvicorn 线程启动")
    try:
        _trace("import uvicorn...")
        import uvicorn
        import logging
        _trace("uvicorn import OK")

        # 强制日志 — 先于 uvicorn 挂上 root logger
        import logging
        _trace("logging setup...")
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        log_file = _DESKTOP + "/patent_verify_run.log"
        _trace("log file path: " + log_file)
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s"))
            root.addHandler(fh)
            _trace("FileHandler OK")
        except Exception as e:
            _trace("FileHandler FAIL: " + str(e))
        root.addHandler(logging.StreamHandler(sys.stdout))
        _trace("StreamHandler OK")
        logging.info("=== 日志系统就绪 ===")
        _trace("logging.info test done")

        # uvicorn config: 最简配置，不覆盖已有 handler
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
        }

        _trace("import backend.main...")
        from backend.main import app
        _trace("backend.main import OK")
        _trace("uvicorn.run 开始...")
        uvicorn.run(app, host=host, port=port, log_level="info", log_config=log_config)
    except Exception:
        _trace("uvicorn 异常: " + traceback.format_exc())
        raise


def main():
    _trace("main() 开始")
    base_dir = get_base_dir()
    _trace("base_dir: " + str(base_dir))
    _trace("_setup_pyinstaller_paths...")
    _setup_pyinstaller_paths(base_dir)
    _trace("PyInstaller paths OK")
    _trace("_setup_env...")
    _setup_env(base_dir)
    _trace("env setup OK")
    _trace("import webbrowser...")
    _trace("webbrowser OK")
    _setup_pyinstaller_paths(base_dir)
    _trace("PyInstaller paths OK")
    _setup_env(base_dir)
    _trace("env setup OK")

    print("=" * 50)
    print("  专利证书可见内容核验系统 v2.0")
    print("  Patent Certificate Verification Agent")
    print("=" * 50)
    print("工作目录: %s" % base_dir)
    print("启动服务...")

    host = "127.0.0.1"
    port = 8000
    url = "http://%s:%d" % (host, port)

    # 在后台线程启动服务器
    _trace("启动 uvicorn 线程...")
    server_thread = threading.Thread(
        target=run_server,
        args=(host, port),
        daemon=True,
    )
    server_thread.start()
    _trace("uvicorn 线程已启动")

    # 等待服务就绪
    print("等待服务就绪...")
    for _ in range(60):
        time.sleep(1)
        try:
            import urllib.request as _req
            resp = _req.urlopen(url + "/api/health", timeout=2)
            if resp.status == 200:
                print("服务已启动: %s" % url)
                webbrowser.open(url)
                print("浏览器已打开。关闭此窗口将停止服务。")
                break
        except Exception:
            pass
    else:
        print("")

        print("服务启动超时。")
        print("请手动打开浏览器访问: %s" % url)
        print("如果无法访问，请检查日志或重新安装。")

    # 保持主线程存活，直到用户按 Ctrl+C
    try:
        while server_thread.is_alive():
            server_thread.join(1)
    except KeyboardInterrupt:
        print("正在关闭...")


if __name__ == "__main__":
    main()

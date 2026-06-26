"""首次运行初始化 — 配置离线环境（模型和浏览器已预装）"""
import sys
import os

def main():
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_dir = os.path.join(app_dir, "python")
    marker = os.path.join(python_dir, ".deps_installed")

    if os.path.exists(marker):
        return True

    print("=" * 50)
    print("  首次运行，正在配置环境...")
    print("=" * 50)

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(app_dir, "playwright-browsers")
    os.environ["EASYOCR_MODULE_PATH"] = os.path.join(python_dir, ".EasyOCR")

    with open(marker, "w") as f:
        f.write("ok")

    print("  配置完成！")
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

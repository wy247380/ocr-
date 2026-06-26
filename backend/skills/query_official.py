"""
Skill: query_cnipa_official_record — 通过 PSS 系统查询国知局官方记录

策略：Chrome 常驻模式
- Chrome 作为后台常驻进程运行，不在每次查询后关闭
- 保持登录态，避免 session 丢失
- 通过 CDP 协议连接（避免 Playwright 自动化标记）
- 持久化用户数据目录
- 最少启动参数

兼容 Windows 7 + Python 3.8+
"""
from __future__ import annotations

import logging
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from ..config import CNIPA_QUERY_URL, CNIPA_CDP_PORT_START, CNIPA_LOGIN_TIMEOUT

logger = logging.getLogger(__name__)

_CHROME_USER_DATA = str(Path.home() / ".patent_verify_browser")
_SCREENSHOT_PATH = str(Path.home() / ".patent_verify_screenshot.png")

# PSS 公开搜索系统
# 查询 URL 列表（按优先级，第一个失败则回退）
# epub 无需登录可直接查询，优先使用
_QUERY_URLS = [
    "http://epub.cnipa.gov.cn/",
    "https://pss-system.cponline.cnipa.gov.cn/conventionalSearch",
]

# 常驻 Chrome 进程和端口（模块级别单例）
_chrome_proc = None  # type: Optional[subprocess.Popen]
_chrome_port = None  # type: Optional[int]


def query_cnipa_official_record(publication_no: str) -> dict:
    """查询国知局 PSS 系统获取官方专利记录。"""
    if not publication_no or len(publication_no) < 5:
        return _failed("publication_no（公开号）格式不合法")

    try:
        return _query_via_cdp(publication_no)
    except ImportError as e:
        return _failed("Playwright 未安装: %s" % e)
    except Exception as e:
        logger.error("官方查询异常: %s", e, exc_info=True)
        return _failed("官方查询出错: %s" % e)


def _is_windows7() -> bool:
    """检测是否为 Windows 7。"""
    import platform
    try:
        ver = platform.version()
        # Win7: 6.1.x, Win10: 10.0.x
        return ver.startswith("6.1")
    except Exception:
        return False


def _get_chrome_version(chrome_path: str) -> Optional[int]:
    """获取 Chrome/Chromium 主版本号。"""
    import subprocess as _sp
    try:
        info = _sp.check_output(
            [chrome_path, "--version"],
            shell=False, stderr=_sp.STDOUT, timeout=5,
        )
        m = re.search(r"(\d+)\.\d+\.\d+", info.decode("utf-8", errors="ignore"))
        if m:
            return int(m.group(1))
    except Exception:
        pass
    # 从文件属性获取
    try:
        import win32api
        info = win32api.GetFileVersionInfo(chrome_path, "\\")
        ms = info["FileVersionMS"]
        return (ms >> 16) & 0xFFFF
    except Exception:
        pass
    return None


def _find_chrome() -> Optional[str]:
    """查找可用的 Chrome 浏览器路径。

    优先级：
    1. 环境变量 CNIPA_CHROME_PATH 指定路径
    2. 项目目录下 ./chrome/chrome.exe（Win7 用户可放旧版 Chrome）
    3. Playwright 安装的 Chromium
    4. 系统安装的 Chrome

    Win7 自动过滤版本 >109 的 Chromium。
    """
    is_win7 = _is_windows7()
    candidates = []

    # 1. 环境变量指定的路径
    from ..config import CNIPA_CHROME_PATH as _chrome_env
    if _chrome_env and Path(_chrome_env).exists():
        candidates.append(_chrome_env)

    # 2. 项目目录下 bundled Chrome
    bundled_paths = [
        Path(__file__).resolve().parent.parent.parent / "chrome" / "chrome.exe",
        Path(__file__).resolve().parent.parent.parent.parent / "chrome" / "chrome.exe",
        Path("chrome/chrome.exe"),  # 当前工作目录
    ]
    for bp in bundled_paths:
        if bp.exists():
            candidates.append(str(bp))

    # 3. Playwright 安装的 Chromium
    pw_base = Path.home() / "AppData" / "Local" / "ms-playwright"
    if pw_base.exists():
        for chrome_dir in sorted(pw_base.glob("chromium-*"), reverse=True):
            for sub in ["chrome-win64/chrome.exe", "chrome-win/chrome.exe"]:
                p = chrome_dir / sub
                if p.exists():
                    candidates.append(str(p))

    # 4. 系统 Chrome
    system_paths = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe",
    ]
    for p in system_paths:
        if p.exists():
            candidates.append(str(p))

    if not candidates:
        # 兜底：自动安装 Playwright 的 Chromium
        logger.info("未找到 Chrome，尝试自动安装 Playwright Chromium...")
        try:
            import subprocess as _sp
            import sys as _sys
            _sp.run(
                [_sys.executable, "-m", "playwright", "install", "chromium"],
                check=True, timeout=300,
                capture_output=True,
                env={**__import__('os').environ, "PLAYWRIGHT_BROWSERS_PATH": "0"},
            )
            # 安装后重新查找
            pw_base = Path.home() / "AppData" / "Local" / "ms-playwright"
            if pw_base.exists():
                for chrome_dir in sorted(pw_base.glob("chromium-*"), reverse=True):
                    for sub in ["chrome-win64/chrome.exe", "chrome-win/chrome.exe"]:
                        p = chrome_dir / sub
                        if p.exists():
                            candidates.append(str(p))
                            logger.info("自动安装 Chromium 成功: %s", p)
        except Exception as e:
            logger.warning("自动安装 Chromium 失败: %s", e)

    if not candidates:
        return None

    if is_win7:
        logger.info("检测到 Windows 7，筛选 Chrome ≤ v109...")
        for c in candidates:
            ver = _get_chrome_version(c)
            if ver is None or ver <= 109:
                logger.info("Win7 兼容 Chrome: %s (v%s)", c, ver)
                return c
        logger.warning("未找到 Win7 兼容的 Chrome (需 ≤ v109)，请设置 CNIPA_CHROME_PATH")
        return None

    return candidates[0]


def _find_available_port() -> int:
    """扫描可用的 CDP 调试端口。"""
    for port in range(CNIPA_CDP_PORT_START, CNIPA_CDP_PORT_START + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    return CNIPA_CDP_PORT_START


def _scan_chrome_cdp() -> Optional[int]:
    """扫描本地已有的 Chrome CDP 端口。"""
    for port in range(CNIPA_CDP_PORT_START, CNIPA_CDP_PORT_START + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
            return port
        except Exception:
            continue
    return None


def _ensure_chrome_running() -> int:
    """确保 Chrome 常驻进程在运行，返回 CDP 端口号。"""
    global _chrome_proc, _chrome_port

    # 1. 先检查已知的进程和端口
    if _chrome_proc is not None and _chrome_port is not None:
        if _chrome_proc.poll() is None:
            # 进程还在运行，验证端口
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(("127.0.0.1", _chrome_port))
                s.close()
                logger.info("Chrome 常驻进程已运行 (port=%d)", _chrome_port)
                return _chrome_port
            except Exception:
                pass
        # 进程不在了，清除引用
        _chrome_proc = None
        _chrome_port = None

    # 2. 扫描网络，看是否有之前留下的 Chrome CDP
    existing_port = _scan_chrome_cdp()
    if existing_port is not None:
        logger.info("发现已有 Chrome CDP (port=%d)，复用", existing_port)
        _chrome_port = existing_port
        _chrome_proc = None  # 不是我们启动的，不管理生命周期
        return existing_port

    # 3. 启动新的 Chrome
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError("未找到 Chrome 或 Chromium 浏览器")

    port = _find_available_port()
    logger.info("启动 Chrome 常驻进程: port=%d, path=%s", port, chrome)

    Path(_CHROME_USER_DATA).mkdir(parents=True, exist_ok=True)

    args = [
        chrome,
        "--remote-debugging-port=%d" % port,
        "--user-data-dir=%s" % _CHROME_USER_DATA,
        "--no-first-run",
        "--no-default-browser-check",
    ]
    proc = subprocess.Popen(args, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

    if proc.poll() is not None:
        # exit code 0 = Chrome 检测到已有实例并退出（profile 冲突）
        # 重新扫描端口，看是否已有可用的 CDP
        existing = _scan_chrome_cdp()
        if existing is not None:
            logger.info("Chrome 可能已通过已有实例启动，复用 port=%d", existing)
            _chrome_port = existing
            _chrome_proc = None
            return existing
        raise RuntimeError("Chrome 启动失败 (exit code: %s)" % proc.returncode)

    _chrome_proc = proc
    _chrome_port = port
    return port


def shutdown_chrome():
    """关闭常驻 Chrome（应用退出时调用）。"""
    global _chrome_proc, _chrome_port
    if _chrome_proc is not None:
        try:
            _chrome_proc.terminate()
            _chrome_proc.wait(timeout=10)
        except Exception:
            try:
                _chrome_proc.kill()
            except Exception:
                pass
        _chrome_proc = None
        _chrome_port = None
        logger.info("Chrome 常驻进程已关闭")


def _query_via_cdp(publication_no: str) -> dict:
    """
    通过 CDP 协议连接常驻 Chrome 查询。
    按优先级尝试多个站点，首个有搜索框的站点被使用。
    Chrome 不会在查询后关闭，保持登录态。
    """
    from playwright.sync_api import sync_playwright

    port = _ensure_chrome_running()

    # 构建 URL 列表：config 指定优先，否则用内置列表
    if CNIPA_QUERY_URL:
        urls = [CNIPA_QUERY_URL] + [u for u in _QUERY_URLS if u != CNIPA_QUERY_URL]
    else:
        urls = list(_QUERY_URLS)

    last_error = None

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp("http://localhost:%d" % port)
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        page_text = ""
        used_url = ""

        for url_idx, target_url in enumerate(urls):
            used_url = target_url
            logger.info("[%d/%d] 尝试: %s", url_idx + 1, len(urls), target_url)

            # 导航
            page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

            # 等待页面稳定
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(3000)

            # 检查页面是否有可用内容 + 输入框
            body_len = 0
            try:
                body_len = len(page.inner_text("body") or "")
            except Exception:
                body_len = 0

            input_count = 0
            try:
                input_count = page.locator("input").count()
            except Exception:
                input_count = 0

            logger.info("  页面内容: %d chars, inputs: %d", body_len, input_count)

            # 判定是否可用
            page_usable = input_count > 0 and body_len > 50

            if not page_usable:
                if url_idx < len(urls) - 1:
                    logger.info("  当前站点无有效内容，回退到下一个...")
                    continue
                else:
                    # 最后一个站点也失败了，尝试等待登录
                    logger.info("  所有站点均无有效内容，等待用户登录 (超时 %dms)", CNIPA_LOGIN_TIMEOUT)
                    try:
                        page.wait_for_selector("input", timeout=CNIPA_LOGIN_TIMEOUT)
                        page_usable = True
                    except Exception:
                        last_error = "所有查询站点均不可用，请手动登录"
                        break

            if page_usable:
                break

        if last_error:
            return _failed(last_error)

        # 等待页面稳定后进行搜索
        page.wait_for_timeout(2000)

        # 寻找搜索输入框并填入公开号（对齐参考项目：直接用 .first）
        filled = False
        for selector in ['input[type="text"]', 'input:not([type])', "input"]:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=500):
                    el.click()
                    el.fill("")
                    el.fill(publication_no)
                    # 验证填入的值（部分网站会 JS 自动格式化）
                    actual_val = el.input_value()
                    if actual_val != publication_no:
                        logger.info("搜索框自动格式化: 输入=%s → 实际=%s", publication_no, actual_val)
                    else:
                        logger.info("搜索框填入: %s", publication_no)
                    filled = True
                    break
            except Exception:
                continue

        if not filled:
            return _failed("无法定位搜索输入框")

        logger.info("填入公开号: %s", publication_no)
        page.wait_for_timeout(500)

        # 回车搜索
        page.keyboard.press("Enter")
        logger.info("已按回车搜索，等待结果...")

        # 等待结果渲染
        page.wait_for_timeout(5000)

        # 从当前站点域名中选内容最多的页面（避免旧页面干扰）
        from urllib.parse import urlparse as _urlparse
        _site_domain = _urlparse(used_url).netloc
        best_page = page
        best_len = 0
        for p in ctx.pages:
            p_url = p.url or ""
            # 只看属于同一站点的页面，忽略其他站点旧页面
            if _urlparse(p_url).netloc != _site_domain:
                continue
            try:
                tlen = len(p.inner_text("body") or "")
                if tlen > best_len:
                    best_len = tlen
                    best_page = p
            except Exception:
                pass
        result_page = best_page
        logger.info("结果页: %s, 内容: %d chars", result_page.url[:80] if result_page.url else "?", best_len)

        # 关闭其他站点的旧页面，避免积累
        for p in ctx.pages:
            if p == result_page or p == page:
                continue
            try:
                p_url = p.url or ""
                if _urlparse(p_url).netloc != _site_domain and p_url not in ("about:blank", ""):
                    p.close()
            except Exception:
                pass

        # 截图保存（调试用）
        try:
            result_page.screenshot(path=_SCREENSHOT_PATH, full_page=True)
        except Exception:
            pass

        # 提取页面文本
        page_text = result_page.inner_text("body")[:50000]

        # 查询完毕关闭结果标签页，避免干扰下次查询
        try:
            if result_page != page:
                result_page.close()
        except Exception:
            pass

    # 注意：不关闭 Chrome，保持常驻

    if not page_text or len(page_text) < 200:
        return _failed("页面内容过少，查询可能失败")

    # 用 DeepSeek reasoner 模型解析页面文本
    record = _parse_with_deepseek(page_text)
    if not record:
        record = _parse_with_regex(page_text)

    if record:
        source = "deepseek" if record.get("_from_deepseek") else "regex"
        record.pop("_from_deepseek", None)
        logger.info("解析成功 (%s): %d 个字段", source, len(record))
        return {
            "query_status": "success",
            "record_count": 1,
            "official_record": record,
            "need_manual": False,
        }

    return _failed("未能从页面提取有效专利信息")


def _parse_with_deepseek(page_text: str) -> Optional[dict]:
    """用 DeepSeek reasoner 模型解析官方页面文本。"""
    try:
        from .deepseek_client import parse_official_page
        result = parse_official_page(page_text)
        if result:
            result["_from_deepseek"] = True
        return result
    except Exception as e:
        logger.warning("DeepSeek 解析失败: %s", e)
        return None


def _parse_with_regex(text: str) -> Optional[dict]:
    """正则解析官方页面（支持 epub 和 PSS 两种格式）。"""
    record = {}  # type: dict

    # --- 专利号/公开号 ---
    # epub 格式: 授权公告号：CN219910140U, 申请号：2023211609569
    m = re.search(r"(?:授权公告号|公告号|公开号|公布号)[：:\s]*\n?\s*(CN\s*\d{7,13}\s*[A-Z]?)", text, re.IGNORECASE)
    if m:
        record["publication_no"] = re.sub(r"\s+", "", m.group(1))

    # PSS 格式
    if not record.get("publication_no"):
        for p in [r"[CＣ][NＮ]\s*(\d[\d\s]{4,12}[A-Z]?)"]:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                record["publication_no"] = re.sub(r"\s+", "", m.group(0).upper())

    # 专利号 ZL
    for p in [r"[ZＺ][LＬ]\s*(\d[\d\s\.]{10,16})"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            record["patent_no"] = re.sub(r"\s+", "", m.group(0).upper())

    # --- 申请号 ---
    m = re.search(r"(?:申请号)[：:\s]+(\d{9,13})", text)
    if m:
        record["application_no"] = m.group(1)

    # --- 专利名称 ---
    # epub 格式: [实用新型] 一种加固墙体结构, [发明授权] xxx, 等等
    # 优先匹配已知类型（可同时提取类型）
    m = re.search(r"\[(?:发明专利|发明授权|实用新型|实用新型专利|外观设计|外观设计专利)\]\s*(.+?)(?:\n|$)", text)
    if m:
        record["patent_title"] = m.group(1).strip()
        type_match = re.search(r"\[(发明\S*|实用新型\S*|外观设计\S*)\]", m.group(0))
        if type_match:
            t = type_match.group(1)
            if "发明" in t and "实用" not in t and "外观" not in t:
                record["patent_type"] = "发明专利"
            elif "实用" in t:
                record["patent_type"] = "实用新型专利"
            elif "外观" in t:
                record["patent_type"] = "外观设计专利"
    else:
        # 回退：去掉任意 [xxx] 前缀提取名称
        m = re.search(r"\[[^\]]+\]\s*(.+?)(?:\n|$)", text)
        if m:
            record["patent_title"] = m.group(1).strip()

    # PSS 格式: 发明名称：xxx
    if not record.get("patent_title"):
        m = re.search(r"(?:发明名称|专利名称|实用新型名称|外观设计名称)[：:\s]+(.+?)(?:\n|$)", text)
        if m:
            record["patent_title"] = m.group(1).strip()

    # --- 发明人 ---
    # epub: 发明人：邱守展;陈晨
    m = re.search(r"(?:发明人|设计人)[：:\s]+(.+?)(?:\n|$)", text)
    if m:
        names = re.split(r"[;；,，、\s]+", m.group(1).strip())
        record["inventors"] = [n.strip() for n in names if n.strip() and len(n.strip()) >= 2]

    # --- 专利权人 ---
    # epub: 专利权人：邱守展;陈晨
    m = re.search(r"(?:专利权人|申请人)[：:\s]+(.+?)(?:\n|$)", text)
    if m:
        names = re.split(r"[;；,，、\s]+", m.group(1).strip())
        record["patentee"] = [n.strip() for n in names if n.strip() and len(n.strip()) >= 2]

    # --- 日期 ---
    m = re.search(r"(?:申请日)[：:\s]+([\d\-\.]+)", text)
    if m:
        record["application_date"] = m.group(1).replace(".", "-")

    m = re.search(r"(?:授权公告日|公告日)[：:\s]+([\d\-\.]+)", text)
    if m:
        record["grant_announcement_date"] = m.group(1).replace(".", "-")

    # --- 法律状态 ---
    m = re.search(r"(?:法律状态|案件状态)[：:\s]+(.+?)(?:\n|$)", text)
    if m:
        record["legal_status"] = m.group(1).strip()

    return record if len(record) >= 2 else None


def _failed(reason: str) -> dict:
    logger.warning("官方查询失败: %s", reason)
    return {
        "query_status": "failed",
        "official_record": None,
        "need_manual": True,
        "fail_reason": reason,
    }

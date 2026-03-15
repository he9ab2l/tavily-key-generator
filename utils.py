"""
工具函数: 文件保存、代理上传、数据同步
"""
import os
import re
import time
import tempfile
import threading
from datetime import datetime

import logger as log

_file_lock = threading.Lock()


def save_api_key(email, api_key, password=None):
    """保存 API key: 双文件同步写入 + 自动上传代理"""
    from config import API_KEYS_FILE, API_KEYS_TXT

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pwd = password if password else "N/A"

    with _file_lock:
        # 1. 写入 md 文件 (表格格式)
        _append_md(API_KEYS_FILE, email, pwd, api_key, timestamp)
        # 2. 写入 txt 文件 (一行一个 key)
        _append_txt(API_KEYS_TXT, api_key)

    log.info(f"[saved] {email} | {api_key[:24]}...")

    # 3. 自动上传到代理
    upload_to_proxy(api_key, email, pwd)


def _append_md(filepath, email, pwd, api_key, timestamp):
    """追加一行到 md 表格文件"""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        _init_md_file(filepath)
    row_num = _count_md_rows(filepath) + 1
    line = f"| {row_num} | {email} | {pwd} | `{api_key}` | {timestamp} |\n"
    _atomic_append(filepath, line)


def _append_txt(filepath, api_key):
    """追加一行到 txt 文件"""
    _atomic_append(filepath, api_key + "\n")


def _atomic_append(filepath, content):
    """原子追加: 直接追加, 确保每次写入完整"""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


def _init_md_file(filepath):
    """初始化 md 文件表头"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Tavily API Keys\n\n")
        f.write("| # | 邮箱 | 密码 | API Key | 时间 |\n")
        f.write("|---|------|------|---------|------|\n")


def _count_md_rows(filepath):
    """统计 md 文件中已有的数据行数"""
    if not os.path.exists(filepath):
        return 0
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
                count += 1
    return count


def upload_to_proxy(api_key, email="", password=""):
    """上传 API Key 到代理网关 (带重试)"""
    try:
        from config import PROXY_AUTO_UPLOAD, PROXY_URL, PROXY_ADMIN_PASSWORD, UPLOAD_RETRY
    except ImportError:
        return

    if not PROXY_AUTO_UPLOAD or not PROXY_URL:
        return

    import urllib.request
    import json

    max_retry = getattr(__import__("config"), "UPLOAD_RETRY", 3)
    url = f"{PROXY_URL.rstrip('/')}/api/keys"
    data = json.dumps({"key": api_key, "email": email, "password": password}).encode()

    for attempt in range(max_retry):
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Admin-Password", PROXY_ADMIN_PASSWORD)
            req.add_header("User-Agent", "TavilyKeyGen/2.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    log.info("[proxy] uploaded")
                    return
                else:
                    log.warn(f"[proxy] HTTP {resp.status}")
        except Exception as e:
            if attempt < max_retry - 1:
                log.warn(f"[proxy] retry {attempt + 1}/{max_retry}: {e}")
                time.sleep(2)
            else:
                log.error(f"[proxy] failed after {max_retry} attempts: {e}")


def sync_key_files():
    """同步双文件: 读取现有数据, 统一格式重新生成

    兼容旧格式:
    - CSV: email,password,key,timestamp;
    - MD表格: | # | email | pwd | `key` | timestamp |
    """
    from config import API_KEYS_FILE, API_KEYS_TXT

    entries = []

    # 读取 md 文件
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                entry = _parse_line(line)
                if entry:
                    entries.append(entry)

    if not entries:
        log.info("[sync] no existing keys found")
        return 0

    # 去重 (按 key)
    seen = set()
    unique = []
    for e in entries:
        if e["key"] not in seen:
            seen.add(e["key"])
            unique.append(e)

    # 重新生成 md 文件
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        f.write("# Tavily API Keys\n\n")
        f.write("| # | 邮箱 | 密码 | API Key | 时间 |\n")
        f.write("|---|------|------|---------|------|\n")
        for i, e in enumerate(unique, 1):
            f.write(f"| {i} | {e['email']} | {e['pwd']} | `{e['key']}` | {e['time']} |\n")

    # 重新生成 txt 文件
    with open(API_KEYS_TXT, "w", encoding="utf-8") as f:
        for e in unique:
            f.write(e["key"] + "\n")

    log.success(f"[sync] {len(unique)} keys synced to {API_KEYS_FILE} + {API_KEYS_TXT}")
    return len(unique)


def _parse_line(line):
    """解析一行数据, 兼容 CSV 和 MD 表格格式"""
    # MD 表格: | 1 | email | pwd | `key` | time |
    md_match = re.match(
        r'\|\s*\d+\s*\|\s*(\S+)\s*\|\s*([^|]+)\s*\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\s*\|',
        line
    )
    if md_match:
        return {
            "email": md_match.group(1).strip(),
            "pwd": md_match.group(2).strip(),
            "key": md_match.group(3).strip(),
            "time": md_match.group(4).strip(),
        }

    # CSV: email,password,key,timestamp;
    csv_match = re.match(r'^([^,]+),([^,]+),(tvly-[^,;]+),([^;]+);?\s*$', line)
    if csv_match:
        return {
            "email": csv_match.group(1).strip(),
            "pwd": csv_match.group(2).strip(),
            "key": csv_match.group(3).strip(),
            "time": csv_match.group(4).strip(),
        }

    return None


def wait_with_message(seconds, message="waiting"):
    """带消息的等待"""
    log.info(f"{message}, {seconds}s...")
    time.sleep(seconds)

"""
工具函数
"""
import os
import time
from datetime import datetime
from config import API_KEYS_FILE, API_KEYS_TXT


def _init_md_file(filepath):
    """初始化 md 文件，写入表头"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Tavily API Keys\n\n")
        f.write("| # | 邮箱 | 密码 | API Key | 时间 |\n")
        f.write("|---|------|------|---------|------|\n")


def _count_md_rows(filepath):
    """统计 md 文件中已有的数据行数"""
    if not os.path.exists(filepath):
        return 0
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
                count += 1
    return count


def save_api_key(email, api_key, password=None):
    """保存 API key：双重保存（md 表格 + txt 纯 key），并自动上传到 Proxy"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pwd = password if password else "N/A"

    # ── 1. 保存到 md 文件（表格格式） ──
    if not os.path.exists(API_KEYS_FILE) or os.path.getsize(API_KEYS_FILE) == 0:
        _init_md_file(API_KEYS_FILE)

    row_num = _count_md_rows(API_KEYS_FILE) + 1
    md_line = f"| {row_num} | {email} | {pwd} | `{api_key}` | {timestamp} |\n"

    with open(API_KEYS_FILE, 'a', encoding='utf-8') as f:
        f.write(md_line)

    # ── 2. 保存到 txt 文件（一行一个 key） ──
    with open(API_KEYS_TXT, 'a', encoding='utf-8') as f:
        f.write(api_key + "\n")

    print(f"✅ 账户信息已保存")
    print(f"   📧 邮箱: {email}")
    print(f"   🔐 密码: {pwd}")
    print(f"   🔑 API Key: {api_key}")
    print(f"   📄 MD: {API_KEYS_FILE} | TXT: {API_KEYS_TXT}")

    # 自动上传到 Proxy
    upload_to_proxy(api_key, email)


def upload_to_proxy(api_key, email=""):
    """将 API Key 上传到 Proxy 网关"""
    try:
        from config import PROXY_AUTO_UPLOAD, PROXY_URL, PROXY_ADMIN_PASSWORD
    except ImportError:
        return

    if not PROXY_AUTO_UPLOAD or not PROXY_URL:
        return

    import urllib.request
    import json

    url = f"{PROXY_URL.rstrip('/')}/api/keys"
    data = json.dumps({"key": api_key, "email": email}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Admin-Password", PROXY_ADMIN_PASSWORD)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"   ☁️ 已自动上传到 Proxy ({PROXY_URL})")
            else:
                print(f"   ⚠️ Proxy 上传失败: HTTP {resp.status}")
    except Exception as e:
        print(f"   ⚠️ Proxy 上传失败: {e}")


def wait_with_message(seconds, message="等待中"):
    """带消息的等待函数"""
    print(f"⏳ {message}，等待 {seconds} 秒...")
    time.sleep(seconds)

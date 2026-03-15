#!/usr/bin/env python3
"""
Tavily API Key 自动注册工具
支持多线程并行注册, Ctrl+C 优雅退出, 数据实时保存
"""
import sys
import time
import signal
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import logger as log
import config
from config import EMAIL_PREFIX, CAPTCHA_SOLVER
from automation import TavilyAutomation
from utils import sync_key_files

# 全局状态
lock = threading.Lock()
success_count = 0
fail_count = 0

# 优雅退出
shutdown_event = threading.Event()

# 速率控制
rate_lock = threading.Lock()
last_start_time = 0


def signal_handler(sig, frame):
    """Ctrl+C 处理: 设置退出标志, 等待当前任务完成"""
    if shutdown_event.is_set():
        log.warn("[main] force quit")
        sys.exit(1)
    log.warn("[main] Ctrl+C received, finishing current tasks...")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)


def detect_backends():
    """检测已配置的邮箱后端"""
    backends = []
    if getattr(config, 'EMAIL_DOMAIN', '') and getattr(config, 'EMAIL_API_URL', '') and getattr(config, 'EMAIL_API_TOKEN', ''):
        backends.append({
            'name': 'cloudflare',
            'label': f"Cloudflare ({config.EMAIL_DOMAIN})",
        })
    if getattr(config, 'DUCKMAIL_BEARER', '') and getattr(config, 'DUCKMAIL_DOMAIN', ''):
        backends.append({
            'name': 'duckmail',
            'label': f"DuckMail ({config.DUCKMAIL_DOMAIN})",
        })
    return backends


def choose_backend(backends):
    """选择邮箱后端"""
    if len(backends) == 0:
        log.error("[main] no email backend configured, edit config.py first")
        sys.exit(1)
    if len(backends) == 1:
        log.info(f"[main] email backend: {backends[0]['label']}")
        return backends[0]['name']

    print("\n  available backends:")
    for i, b in enumerate(backends, 1):
        print(f"    {i}. {b['label']}")
    while True:
        choice = input("  choose (default 1): ").strip()
        if choice == '':
            return backends[0]['name']
        if choice.isdigit() and 1 <= int(choice) <= len(backends):
            return backends[int(choice) - 1]['name']
        print("  invalid choice")


def wait_for_cooldown():
    """速率控制"""
    global last_start_time
    cooldown = getattr(config, 'COOLDOWN_SECONDS', 45)
    with rate_lock:
        now = time.time()
        wait = cooldown - (now - last_start_time)
        if wait > 0:
            wait += random.uniform(0, 5)
            time.sleep(wait)
        last_start_time = time.time()


def register_one(task_id, total, provider_name):
    """单个注册任务"""
    global success_count, fail_count

    if shutdown_event.is_set():
        return None

    wait_for_cooldown()

    if shutdown_event.is_set():
        return None

    with lock:
        log.info(f"[{task_id}/{total}] starting registration...")

    automation = None
    try:
        config.EMAIL_PROVIDER = provider_name
        automation = TavilyAutomation()
        automation.email_prefix = EMAIL_PREFIX
        automation.start_browser(headless=config.HEADLESS)

        start_time = time.time()
        api_key = automation.run_complete_automation()
        elapsed = time.time() - start_time

        with lock:
            if api_key:
                success_count += 1
                log.success(f"[{task_id}/{total}] OK  {automation.email}  {api_key[:24]}...  {elapsed:.0f}s")
            else:
                fail_count += 1
                log.error(f"[{task_id}/{total}] FAIL  {elapsed:.0f}s")

        return api_key

    except Exception as e:
        with lock:
            fail_count += 1
            log.error(f"[{task_id}/{total}] ERROR: {e}")
        return None
    finally:
        if automation:
            try:
                automation.close_browser()
            except Exception:
                pass


def print_summary(elapsed):
    """打印结果摘要"""
    print()
    print("  " + "-" * 45)
    print(f"  done in {elapsed:.0f}s")
    print(f"  success: {success_count}  |  fail: {fail_count}  |  total: {success_count + fail_count}")
    print(f"  keys saved to: {config.API_KEYS_FILE} + {config.API_KEYS_TXT}")
    print("  " + "-" * 45)
    print()


def main():
    global success_count, fail_count

    print()
    print("  Tavily Key Auto-Register")
    print("  " + "-" * 30)

    backends = detect_backends()
    provider_name = choose_backend(backends)

    pwd_mode = "random" if not config.DEFAULT_PASSWORD else "fixed"
    log.info(f"[main] captcha: {CAPTCHA_SOLVER}")
    log.info(f"[main] password: {pwd_mode}")

    # 先同步已有的 key 文件
    sync_key_files()

    max_threads = getattr(config, 'MAX_THREADS', 2)
    cooldown = getattr(config, 'COOLDOWN_SECONDS', 45)

    count_input = input(f"\n  register count (default 10): ").strip()
    count = int(count_input) if count_input.isdigit() and int(count_input) > 0 else 10

    threads_input = input(f"  threads (default {max_threads}): ").strip()
    threads = int(threads_input) if threads_input.isdigit() and int(threads_input) > 0 else max_threads
    threads = min(threads, count)

    print()
    log.info(f"[main] target: {count} | threads: {threads} | cooldown: {cooldown}s")
    print("  press Ctrl+C to stop gracefully")
    print()

    success_count = 0
    fail_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i in range(1, count + 1):
            if shutdown_event.is_set():
                break
            futures.append(executor.submit(register_one, i, count, provider_name))

        for future in as_completed(futures):
            if shutdown_event.is_set():
                break

    elapsed = time.time() - start_time
    print_summary(elapsed)


if __name__ == "__main__":
    main()

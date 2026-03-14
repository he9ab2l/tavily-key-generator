#!/usr/bin/env python3
"""
Turnstile-Solver API 适配器
调用本地 Turnstile-Solver (https://github.com/Theyka/Turnstile-Solver) 解决验证码
"""
import time
import requests


def solve_turnstile_via_api(solver_url, website_url, sitekey, timeout=120, max_retries=3):
    """
    通过本地 Turnstile-Solver API 解决 Turnstile
    内置重试机制，返回 token 或 None
    """
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"🔄 重试第 {attempt + 1}/{max_retries} 次...")

        print(f"🔐 [Turnstile-Solver] 请求解码: sitekey={sitekey[:20]}...")

        # 发起解码任务
        try:
            resp = requests.get(
                f"{solver_url}/turnstile",
                params={"url": website_url, "sitekey": sitekey},
                timeout=15,
            )
            if resp.status_code != 202:
                print(f"❌ 创建任务失败: HTTP {resp.status_code}")
                continue

            task_id = resp.json().get("task_id")
            if not task_id:
                continue

            print(f"✅ 任务已创建: {task_id}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            continue

        # 轮询结果（单次任务最多等 30 秒，solver 本身 10 次尝试约 10s）
        start = time.time()
        while time.time() - start < 30:
            time.sleep(2)
            try:
                resp = requests.get(
                    f"{solver_url}/result",
                    params={"id": task_id},
                    timeout=15,
                )

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, dict):
                            token = data.get("value")
                            elapsed = data.get("elapsed_time", "?")
                            if token and token not in ("CAPTCHA_NOT_READY", "CAPTCHA_FAIL"):
                                print(f"✅ Turnstile 已解决 (耗时 {elapsed}s)")
                                return token
                            if token == "CAPTCHA_FAIL":
                                print(f"⚠️ 本次解码失败，准备重试...")
                                break
                    except (ValueError, AttributeError):
                        pass

                if resp.status_code == 422:
                    print(f"⚠️ 本次解码失败 (422)，准备重试...")
                    break

                if "CAPTCHA_NOT_READY" in resp.text:
                    continue

            except Exception:
                pass

    print("❌ 所有重试均失败")
    return None


def extract_sitekey_from_page(page):
    """从 Playwright 页面中提取 Turnstile sitekey"""
    import re

    # 方法1: 从 iframe URL 提取
    for frame in page.frames:
        if "challenges.cloudflare.com" in frame.url:
            match = re.search(r'/(0x[0-9a-zA-Z_-]{10,})/', frame.url)
            if match:
                return match.group(1)

    # 方法2: 从 DOM 查找
    sitekey = page.evaluate("""() => {
        const selectors = [
            '[data-sitekey]',
            '[data-captcha-sitekey]',
            '.cf-turnstile',
        ];
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) {
                return el.getAttribute('data-sitekey')
                    || el.getAttribute('data-captcha-sitekey')
                    || null;
            }
        }
        return null;
    }""")
    if sitekey:
        return sitekey

    # 方法3: 从页面源码匹配
    content = page.content()
    patterns = [
        r'data-sitekey="(0x[0-9a-zA-Z_-]{10,})"',
        r'sitekey["\s:=]+["\'](0x[0-9a-zA-Z_-]{10,})["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def inject_turnstile_token(page, token):
    """将 token 注入页面"""
    page.evaluate("""(token) => {
        const inputs = document.querySelectorAll(
            '[name="cf-turnstile-response"], [name="cf-chl-turnstile-response"], [name="captcha"]'
        );
        inputs.forEach(input => { input.value = token; });

        // 触发回调
        const els = document.querySelectorAll(
            '[data-callback], [data-captcha-sitekey], .cf-turnstile, [data-sitekey]'
        );
        for (const el of els) {
            const cbName = el.getAttribute('data-callback');
            if (cbName && typeof window[cbName] === 'function') {
                window[cbName](token);
                return;
            }
        }
        for (const key of Object.keys(window)) {
            if (key.startsWith('captchaCallback_') && typeof window[key] === 'function') {
                window[key](token);
                return;
            }
        }

        // 触发 turnstile 全局回调
        if (window.turnstile) {
            try {
                const widgetId = Object.keys(window.turnstile._widgets || {})[0];
                if (widgetId) {
                    const cb = window.turnstile._widgets[widgetId]?.callback;
                    if (typeof cb === 'function') cb(token);
                }
            } catch(e) {}
        }
    }""", token)
    print("✅ Token 已注入页面")

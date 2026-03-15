"""
CapSolver Turnstile 验证码解决器
"""
import re
import time
import requests
import logger as log
from config import CAPSOLVER_API_KEY

API_BASE = "https://api.capsolver.com"


def solve_turnstile(website_url, website_key, metadata=None):
    """调用 CapSolver API 解决 Turnstile, 返回 token 或 None"""
    log.info(f"[capsolver] solving: sitekey={website_key[:20]}...")

    task = {
        "type": "AntiTurnstileTaskProxyLess",
        "websiteURL": website_url,
        "websiteKey": website_key,
    }
    if metadata:
        task["metadata"] = metadata

    try:
        resp = requests.post(f"{API_BASE}/createTask", json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": task,
        }, timeout=30)
        data = resp.json()

        if data.get("errorId", 0) != 0:
            log.error(f"[capsolver] create failed: {data.get('errorDescription', data)}")
            return None

        task_id = data.get("taskId")
        if not task_id:
            log.error(f"[capsolver] no taskId: {data}")
            return None

        log.info(f"[capsolver] task created: {task_id}")
    except Exception as e:
        log.error(f"[capsolver] request error: {e}")
        return None

    # 轮询结果 (最多 120 秒)
    for i in range(60):
        time.sleep(2)
        try:
            resp = requests.post(f"{API_BASE}/getTaskResult", json={
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id,
            }, timeout=30)
            result = resp.json()

            status = result.get("status")
            if status == "ready":
                token = result.get("solution", {}).get("token")
                if token:
                    log.success(f"[capsolver] solved in {(i+1)*2}s")
                    return token
                else:
                    log.error(f"[capsolver] solved but no token: {result}")
                    return None
            elif status == "processing":
                if i % 5 == 0:
                    log.info(f"[capsolver] waiting... ({(i+1)*2}s)")
            else:
                error = result.get("errorDescription", "")
                if error:
                    log.error(f"[capsolver] failed: {error}")
                    return None
        except Exception as e:
            log.warn(f"[capsolver] poll error: {e}")

    log.error("[capsolver] timeout")
    return None


def extract_turnstile_sitekey(page):
    """从页面中提取 Turnstile sitekey"""
    # 方法1: DOM 查找
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
        log.info(f"[capsolver] sitekey from DOM: {sitekey}")
        return sitekey

    # 方法2: 源码正则
    content = page.content()
    patterns = [
        r'data-captcha-sitekey="(0x[0-9a-zA-Z_-]{10,})"',
        r'data-sitekey="(0x[0-9a-zA-Z_-]{10,})"',
        r'sitekey["\s:=]+["\'](0x[0-9a-zA-Z_-]{10,})["\']',
        r'siteKey["\s:=]+["\'](0x[0-9a-zA-Z_-]{10,})["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            sitekey = match.group(1)
            log.info(f"[capsolver] sitekey from source: {sitekey}")
            return sitekey

    # 方法3: iframe URL
    for frame in page.frames:
        url = frame.url
        if "challenges.cloudflare.com" in url:
            match = re.search(r'/(0x[0-9a-zA-Z_-]{10,})/', url)
            if match:
                sitekey = match.group(1)
                log.info(f"[capsolver] sitekey from iframe: {sitekey}")
                return sitekey

    log.warn("[capsolver] no sitekey found")
    return None


def inject_turnstile_token(page, token):
    """将 token 注入页面"""
    page.evaluate("""(token) => {
        const inputSelectors = [
            '[name="cf-turnstile-response"]',
            '[name="cf-chl-turnstile-response"]',
            '[name="captcha"]',
            'input[data-captcha]',
        ];
        for (const sel of inputSelectors) {
            document.querySelectorAll(sel).forEach(input => {
                input.value = token;
            });
        }
        const callbackEls = document.querySelectorAll(
            '[data-callback], [data-captcha-sitekey], .cf-turnstile, [data-sitekey]'
        );
        for (const el of callbackEls) {
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
    }""", token)
    log.info("[capsolver] token injected")

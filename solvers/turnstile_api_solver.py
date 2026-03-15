"""
Turnstile-Solver API 适配器
调用本地 Turnstile-Solver 解决验证码
"""
import time
import requests
import logger as log


def solve_turnstile_via_api(solver_url, website_url, sitekey, timeout=120, max_retries=3):
    """通过本地 Turnstile-Solver API 解决, 返回 token 或 None"""
    for attempt in range(max_retries):
        if attempt > 0:
            log.info(f"[solver-api] retry {attempt + 1}/{max_retries}...")

        log.info(f"[solver-api] requesting: sitekey={sitekey[:20]}...")

        try:
            resp = requests.get(
                f"{solver_url}/turnstile",
                params={"url": website_url, "sitekey": sitekey},
                timeout=15,
            )
            if resp.status_code != 202:
                log.error(f"[solver-api] create failed: HTTP {resp.status_code}")
                continue

            task_id = resp.json().get("task_id")
            if not task_id:
                continue

            log.info(f"[solver-api] task created: {task_id}")
        except Exception as e:
            log.error(f"[solver-api] request error: {e}")
            continue

        # 轮询结果
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
                                log.success(f"[solver-api] solved in {elapsed}s")
                                return token
                            if token == "CAPTCHA_FAIL":
                                log.warn("[solver-api] captcha fail, retrying...")
                                break
                    except (ValueError, AttributeError):
                        pass

                if resp.status_code == 422:
                    log.warn("[solver-api] 422 error, retrying...")
                    break

                if "CAPTCHA_NOT_READY" in resp.text:
                    continue

            except Exception:
                pass

    log.error("[solver-api] all retries failed")
    return None


def extract_sitekey_from_page(page):
    """从页面提取 Turnstile sitekey"""
    import re

    # 方法1: iframe URL
    for frame in page.frames:
        if "challenges.cloudflare.com" in frame.url:
            match = re.search(r'/(0x[0-9a-zA-Z_-]{10,})/', frame.url)
            if match:
                return match.group(1)

    # 方法2: DOM
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

    # 方法3: 源码匹配
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
    log.info("[solver-api] token injected")

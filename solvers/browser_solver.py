"""
浏览器原生 Turnstile 验证码解决器 (免费)
通过在真实浏览器中点击 Turnstile 复选框来通过验证
"""
import time
import logger as log


def solve_turnstile_browser(page, timeout=30):
    """
    在浏览器中直接解决 Turnstile 验证
    返回 True/False
    """
    log.info("[turnstile] browser solver: checking...")

    # 等待 Turnstile iframe 出现
    has_iframe = False
    try:
        page.wait_for_selector(
            'iframe[src*="challenges.cloudflare.com"]',
            timeout=15000,
        )
        has_iframe = True
    except Exception:
        has_captcha = page.evaluate("""() => {
            const el = document.querySelector('[name="captcha"], [name="cf-turnstile-response"]');
            return el ? true : false;
        }""")
        if not has_captcha:
            log.info("[turnstile] not detected, skip")
            return True
        log.info("[turnstile] invisible mode detected, waiting...")

    time.sleep(2)

    # 尝试在 iframe 中点击复选框
    clicked = False
    if has_iframe:
        for frame in page.frames:
            if "challenges.cloudflare.com" not in frame.url:
                continue
            try:
                selectors = [
                    'input[type="checkbox"]',
                    '[role="checkbox"]',
                    '.cb-lb',
                    '#challenge-stage input',
                ]
                for sel in selectors:
                    try:
                        cb = frame.wait_for_selector(sel, timeout=3000)
                        if cb:
                            cb.click()
                            log.success(f"[turnstile] clicked checkbox: {sel}")
                            clicked = True
                            break
                    except Exception:
                        continue
            except Exception:
                continue
            if clicked:
                break

        if not clicked:
            log.info("[turnstile] no checkbox found, waiting for auto-verify...")

    # 等待 cf-turnstile-response 被填充
    try:
        page.wait_for_function(
            """
            () => {
                const fields = document.querySelectorAll(
                    '[name="cf-turnstile-response"], [name="cf-chl-turnstile-response"], [name="captcha"]'
                );
                for (const f of fields) {
                    if (f.value && f.value.length > 50) return true;
                }
                return false;
            }
            """,
            timeout=timeout * 1000,
        )
        log.success("[turnstile] passed")
        return True
    except Exception:
        log.error("[turnstile] timeout")
        return False

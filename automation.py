#!/usr/bin/env python3
"""
Tavily 自动化注册模块
基于智能元素检测和等待机制
"""
import time
import re
import string
import random

try:
    from patchright.sync_api import sync_playwright
except ImportError:
    from playwright.sync_api import sync_playwright

from config import *
from utils import save_api_key
from email_providers import create_email_provider
import logger as log


def generate_random_password(length=16):
    """生成随机强密码: 大小写+数字+特殊字符"""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%&*"
    password = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(special),
    ]
    all_chars = upper + lower + digits + special
    password += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(password)
    return ''.join(password)


class TavilyAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.email = None
        self.password = DEFAULT_PASSWORD if DEFAULT_PASSWORD else generate_random_password()
        self.debug = True
        self.email_prefix = None
        self.headless_mode = None
        self.provider = create_email_provider(EMAIL_PROVIDER)

        # 智能选择器
        self.selectors = {
            'signup_button': {
                'primary': [
                    'a:has-text("Sign up")',
                    'a[href*="signup"]',
                ],
                'fallback': [
                    'p:has-text("Don\'t have an account?") a',
                    'a[class*="c7c2d7b15"]',
                ]
            },
            'email_input': {
                'primary': [
                    'input#username',
                    'input[name="username"]',
                    'input#email',
                    'input[name="email"]',
                ],
                'fallback': [
                    'input[type="text"][autocomplete="email"]',
                    'label:has-text("Email address") + div input',
                ]
            },
            'continue_button': {
                'primary': [
                    'button[name="action"][type="submit"]',
                    'button[type="submit"]:has-text("Continue")',
                ],
                'fallback': [
                    'form._form-signup-id button[type="submit"]',
                    'button._button-signup-id',
                ]
            },
            'password_input': {
                'primary': [
                    'input#password',
                    'input[name="password"]',
                    'input[type="password"][autocomplete="new-password"]',
                ],
                'fallback': [
                    'input[type="password"]',
                    'label:has-text("Password") + div input',
                ]
            },
            'submit_button': {
                'primary': [
                    'button[name="action"][type="submit"]',
                    'button[type="submit"]:has-text("Continue")',
                ],
                'fallback': [
                    'button[type="submit"]',
                    'input[type="submit"]',
                ]
            }
        }

    def start_browser(self, headless=None):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        headless_mode = headless if headless is not None else HEADLESS
        self.headless_mode = headless_mode

        # 优先 patchright chromium
        try:
            from patchright.sync_api import sync_playwright as _check
            self.browser = self.playwright.chromium.launch(
                headless=headless_mode,
                args=['--ignore-certificate-errors'],
            )
            log.info("[browser] patchright chromium")
        except ImportError:
            if BROWSER_TYPE == "firefox":
                self.browser = self.playwright.firefox.launch(headless=headless_mode)
            elif BROWSER_TYPE == "webkit":
                self.browser = self.playwright.webkit.launch(headless=headless_mode)
            else:
                self.browser = self.playwright.chromium.launch(headless=headless_mode)

        context = self.browser.new_context(ignore_https_errors=True)
        self.page = context.new_page()
        self.page.set_default_timeout(30000)

        # stealth 补丁 (仅非 patchright)
        try:
            from patchright.sync_api import sync_playwright as _check
        except ImportError:
            try:
                from playwright_stealth import stealth_sync
                stealth_sync(self.page)
            except Exception:
                pass

    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception:
            pass

    def smart_wait_for_element(self, element_config, timeout=30000):
        """智能等待元素"""
        primary = element_config['primary']
        fallback = element_config['fallback']

        for selector in primary:
            try:
                element = self.page.wait_for_selector(selector, timeout=timeout // len(primary))
                if element:
                    return element, selector
            except Exception:
                continue

        for selector in fallback:
            try:
                element = self.page.wait_for_selector(selector, timeout=timeout // len(fallback))
                if element:
                    return element, selector
            except Exception:
                continue

        return None, None

    def smart_click(self, element_name, retries=3):
        """智能点击"""
        element_config = self.selectors.get(element_name)
        if not element_config:
            return False

        for attempt in range(retries):
            element, selector = self.smart_wait_for_element(element_config)
            if element:
                try:
                    element.wait_for_element_state('visible', timeout=5000)
                    element.wait_for_element_state('stable', timeout=5000)
                    element.click()
                    time.sleep(0.5)
                    try:
                        self.page.wait_for_load_state('networkidle', timeout=5000)
                    except Exception:
                        pass
                    return True
                except Exception:
                    pass

            if attempt < retries - 1:
                self.page.reload(wait_until='domcontentloaded')
                try:
                    self.page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                time.sleep(1)

        return False

    def smart_fill(self, element_name, text, retries=3):
        """智能填写"""
        element_config = self.selectors.get(element_name)
        if not element_config:
            return False

        for attempt in range(retries):
            element, selector = self.smart_wait_for_element(element_config)
            if element:
                try:
                    element.wait_for_element_state('visible', timeout=5000)
                    element.wait_for_element_state('editable', timeout=5000)
                    element.fill('')
                    element.fill(text)
                    time.sleep(0.5)
                    filled_value = element.input_value()
                    if filled_value == text:
                        return True
                except Exception:
                    pass

            if attempt < retries - 1:
                self.page.reload(wait_until='domcontentloaded')
                try:
                    self.page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                time.sleep(1)

        return False

    def navigate_to_signup(self):
        """导航到注册页面"""
        try:
            log.info("[reg] navigating to signup...")
            auth_url = (
                "https://auth.tavily.com/authorize"
                "?response_type=code"
                "&client_id=RRIAvvXNFxpfTWIozX1mXqLnyUmYSTrQ"
                "&redirect_uri=https%3A%2F%2Fapp.tavily.com%2Fapi%2Fauth%2Fcallback"
                "&scope=openid%20profile%20email"
                "&screen_hint=signup"
            )
            self.page.goto(auth_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(2)

            if "auth.tavily.com" in self.page.url:
                return True

            # 回退
            self.page.goto(TAVILY_HOME_URL, wait_until='domcontentloaded', timeout=60000)
            for _ in range(10):
                time.sleep(1)
                if "auth.tavily.com" in self.page.url:
                    break

            if self.smart_click('signup_button'):
                return True

            self.page.goto(TAVILY_SIGNUP_URL, wait_until='domcontentloaded', timeout=60000)
            return True

        except Exception as e:
            log.error(f"[reg] navigate failed: {e}")
            return False

    def fill_registration_form(self):
        """填写注册表单"""
        try:
            self.email = self.provider.create_email(self.email_prefix)
            log.info(f"[reg] email: {self.email}")

            if not self.smart_fill('email_input', self.email):
                return False

            if not self.solve_turnstile_if_present():
                log.warn("[reg] turnstile failed, trying to continue...")

            if not self.smart_click('continue_button'):
                return False

            return True
        except Exception as e:
            log.error(f"[reg] form failed: {e}")
            return False

    def solve_turnstile_if_present(self):
        """检测并解决 Turnstile"""
        try:
            log.info("[reg] checking turnstile...")
            time.sleep(2)

            if CAPTCHA_SOLVER == "browser":
                from solvers.browser_solver import solve_turnstile_browser
                return solve_turnstile_browser(self.page)
            elif CAPTCHA_SOLVER == "turnstile-solver":
                from solvers.turnstile_api_solver import solve_turnstile_via_api, extract_sitekey_from_page, inject_turnstile_token

                sitekey = extract_sitekey_from_page(self.page)
                if not sitekey:
                    return True

                log.info(f"[reg] turnstile detected: {sitekey[:20]}...")
                token = solve_turnstile_via_api(TURNSTILE_SOLVER_URL, self.page.url, sitekey)
                if not token:
                    return False

                inject_turnstile_token(self.page, token)
                time.sleep(2)
                try:
                    self.page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                return True
            else:
                from solvers.capsolver_solver import solve_turnstile, extract_turnstile_sitekey, inject_turnstile_token

                sitekey = extract_turnstile_sitekey(self.page)
                if not sitekey:
                    return True

                log.info(f"[reg] turnstile detected: {sitekey[:20]}...")
                token = solve_turnstile(self.page.url, sitekey)
                if not token:
                    return False

                inject_turnstile_token(self.page, token)
                time.sleep(2)
                try:
                    self.page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                return True

        except Exception as e:
            log.error(f"[reg] turnstile error: {e}")
            return False

    def fill_password(self):
        """填写密码"""
        try:
            log.info("[reg] filling password...")

            element_config = self.selectors['password_input']
            element, selector = self.smart_wait_for_element(element_config, timeout=5000)

            if not element:
                log.info("[reg] password field not found, solving turnstile...")
                if self.solve_turnstile_if_present():
                    self.smart_click('continue_button')
                    time.sleep(3)
                else:
                    return False

            if not self.smart_fill('password_input', self.password):
                return False

            if not self.smart_click('submit_button'):
                return False

            time.sleep(1)
            self.solve_turnstile_if_present()
            return True

        except Exception as e:
            log.error(f"[reg] password failed: {e}")
            return False

    def run_registration(self):
        """完整注册流程"""
        try:
            log.info("[reg] starting registration...")

            if not self.navigate_to_signup():
                raise Exception("navigate failed")

            if not self.fill_registration_form():
                raise Exception("form failed")

            if not self.fill_password():
                raise Exception("password failed")

            return True
        except Exception as e:
            log.error(f"[reg] registration failed: {e}")
            return False

    def run_complete_automation(self):
        """完整流程: 注册 + 验证 + 获取 key"""
        try:
            if not self.run_registration():
                raise Exception("registration failed")

            log.info("[reg] waiting for verification email...")
            api_key = self.handle_email_verification_and_login()

            if api_key:
                log.success(f"[reg] done: {api_key[:24]}...")
                save_api_key(self.email, api_key, self.password)
                return api_key
            else:
                raise Exception("verification or key extraction failed")

        except Exception as e:
            log.error(f"[reg] automation failed: {e}")
            return None

    def handle_email_verification_and_login(self):
        """邮件验证 + 登录 + 获取 key"""
        try:
            verification_link = self.provider.check_for_verification_email(self.email)
            if not verification_link:
                raise Exception("no verification email")

            log.info("[reg] visiting verification link...")
            self.page.goto(verification_link, wait_until='domcontentloaded', timeout=60000)
            try:
                self.page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass
            time.sleep(2)

            current_url = self.page.url
            page_content = self.page.content().lower()

            if "login" in current_url.lower() or "sign in" in page_content:
                log.info("[reg] login required...")
                if not self.login_to_tavily():
                    raise Exception("login failed")

            log.info("[reg] extracting API key...")
            api_key = self.get_api_key()

            if api_key:
                self.provider.cleanup(self.email)
                return api_key
            else:
                raise Exception("API key not found")

        except Exception as e:
            log.error(f"[reg] verification failed: {e}")
            return None

    def login_to_tavily(self):
        """登录 Tavily"""
        try:
            if not self.smart_fill('email_input', self.email):
                return False
            if not self.smart_click('continue_button'):
                return False
            time.sleep(1)
            if not self.smart_fill('password_input', self.password):
                return False
            if not self.smart_click('submit_button'):
                return False
            time.sleep(2)
            return True
        except Exception as e:
            log.error(f"[reg] login failed: {e}")
            return False

    def get_api_key(self):
        """从仪表板获取 API key"""
        try:
            self.page.goto("https://app.tavily.com/home", wait_until='domcontentloaded', timeout=60000)
            try:
                self.page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass
            time.sleep(2)

            page_text = self.page.content()
            api_key_match = re.search(r'tvly-[A-Za-z0-9\-_]{20,}', page_text)
            if api_key_match:
                return api_key_match.group(0)

            show_key_selectors = [
                'button:has-text("Show")',
                'button:has-text("Copy")',
                'button:has-text("Reveal")',
                '[data-testid="api-key"]',
            ]
            for selector in show_key_selectors:
                try:
                    btn = self.page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        btn.click()
                        time.sleep(1)
                        page_text = self.page.content()
                        api_key_match = re.search(r'tvly-[A-Za-z0-9\-_]{20,}', page_text)
                        if api_key_match:
                            return api_key_match.group(0)
                except Exception:
                    continue

            log.warn("[reg] API key not found on page")
            return None

        except Exception as e:
            log.error(f"[reg] get key failed: {e}")
            return None

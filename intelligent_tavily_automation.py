#!/usr/bin/env python3
"""
智能Tavily自动化模块
基于深层HTML信息分析，使用智能元素检测和等待机制
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


def generate_random_password(length=16):
    """生成随机强密码：包含大小写字母、数字和特殊字符"""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%&*"
    # 保证每种字符至少一个
    password = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(special),
    ]
    # 剩余随机填充
    all_chars = upper + lower + digits + special
    password += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(password)
    return ''.join(password)


class IntelligentTavilyAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.email = None
        self.password = DEFAULT_PASSWORD if DEFAULT_PASSWORD else generate_random_password()
        self.debug = True
        self.email_prefix = None  # 动态邮箱前缀
        self.headless_mode = None  # 记住headless设置
        self.provider = create_email_provider(EMAIL_PROVIDER)
        
        # 基于深层分析的智能选择器配置
        self.selectors = {
            'signup_button': {
                'primary': [
                    'a:has-text("Sign up")',  # 最稳定：基于文本内容
                    'a[href*="signup"]',      # 稳定：基于URL特征
                ],
                'fallback': [
                    'p:has-text("Don\'t have an account?") a',  # 基于父元素上下文
                    'a[class*="c7c2d7b15"]',  # 基于部分class（如果稳定）
                ]
            },
            'email_input': {
                'primary': [
                    'input#username',                 # Auth0 新版：基于ID
                    'input[name="username"]',         # Auth0 新版：基于name
                    'input#email',                    # 旧版：基于ID
                    'input[name="email"]',            # 旧版：基于name
                ],
                'fallback': [
                    'input[type="text"][autocomplete="email"]',  # 组合属性
                    'label:has-text("Email address") + div input',  # 基于标签关联
                ]
            },
            'continue_button': {
                'primary': [
                    'button[name="action"][type="submit"]',  # 最稳定：精确属性组合
                    'button[type="submit"]:has-text("Continue")',  # 稳定：类型+文本
                ],
                'fallback': [
                    'form._form-signup-id button[type="submit"]',  # 基于表单上下文
                    'button._button-signup-id',  # 基于特定class
                ]
            },
            'password_input': {
                'primary': [
                    'input#password',                 # 最稳定：基于ID
                    'input[name="password"]',         # 最稳定：基于name
                    'input[type="password"][autocomplete="new-password"]',  # 稳定：组合属性
                ],
                'fallback': [
                    'input[type="password"]',         # 基于类型
                    'label:has-text("Password") + div input',  # 基于标签关联
                ]
            },
            'submit_button': {
                'primary': [
                    'button[name="action"][type="submit"]',  # 复用continue按钮逻辑
                    'button[type="submit"]:has-text("Continue")',
                ],
                'fallback': [
                    'button[type="submit"]',
                    'input[type="submit"]',
                ]
            }
        }
    
    def log(self, message, level="INFO"):
        """调试日志"""
        if self.debug:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def start_browser(self, headless=None):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        headless_mode = headless if headless is not None else HEADLESS

        # 记住headless设置，供后续使用
        self.headless_mode = headless_mode

        # 优先使用 patchright chromium（反检测能力强，能通过 Turnstile）
        try:
            from patchright.sync_api import sync_playwright as _check
            self.browser = self.playwright.chromium.launch(
                headless=headless_mode,
                args=['--ignore-certificate-errors'],
            )
            self.log("✅ 使用 patchright chromium（反检测模式）")
        except ImportError:
            # 回退到普通 playwright
            if BROWSER_TYPE == "firefox":
                self.browser = self.playwright.firefox.launch(headless=headless_mode)
            elif BROWSER_TYPE == "webkit":
                self.browser = self.playwright.webkit.launch(headless=headless_mode)
            else:
                self.browser = self.playwright.chromium.launch(headless=headless_mode)

        context = self.browser.new_context(ignore_https_errors=True)
        self.page = context.new_page()
        self.page.set_default_timeout(30000)

        # 仅在非 patchright 时应用 stealth 补丁
        try:
            from patchright.sync_api import sync_playwright as _check
            self.log("✅ patchright 已内建反检测，无需额外补丁")
        except ImportError:
            try:
                from playwright_stealth import stealth_sync
                stealth_sync(self.page)
                self.log("✅ 已应用浏览器反检测补丁")
            except ImportError:
                self.log("⚠️ playwright-stealth 未安装，跳过反检测")
            except Exception as e:
                self.log(f"⚠️ 反检测补丁应用失败: {e}")
    
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
        except Exception as e:
            # 浏览器可能已经关闭，忽略错误
            self.log(f"⚠️ 浏览器关闭时出现错误（可忽略）: {e}", "DEBUG")
            pass
    
    def smart_wait_for_element(self, element_config, timeout=30000):
        """智能等待元素出现"""
        primary_selectors = element_config['primary']
        fallback_selectors = element_config['fallback']
        
        # 首先尝试主要选择器
        for selector in primary_selectors:
            try:
                self.log(f"🔍 尝试主要选择器: {selector}")
                element = self.page.wait_for_selector(selector, timeout=timeout//len(primary_selectors))
                if element:
                    self.log(f"✅ 找到元素: {selector}")
                    return element, selector
            except Exception as e:
                self.log(f"❌ 主要选择器失败: {selector}")
                continue
        
        # 如果主要选择器都失败，尝试备用选择器
        self.log("⚠️ 主要选择器都失败，尝试备用选择器...")
        for selector in fallback_selectors:
            try:
                self.log(f"🔍 尝试备用选择器: {selector}")
                element = self.page.wait_for_selector(selector, timeout=timeout//len(fallback_selectors))
                if element:
                    self.log(f"✅ 找到元素（备用）: {selector}")
                    return element, selector
            except Exception as e:
                self.log(f"❌ 备用选择器失败: {selector}")
                continue
        
        return None, None
    
    def smart_click(self, element_name, retries=3):
        """智能点击元素"""
        element_config = self.selectors.get(element_name)
        if not element_config:
            self.log(f"❌ 未找到元素配置: {element_name}")
            return False
        
        for attempt in range(retries):
            self.log(f"🔄 尝试点击 {element_name} (第 {attempt+1}/{retries} 次)")
            
            element, selector = self.smart_wait_for_element(element_config)
            
            if element:
                try:
                    # 确保元素可见和稳定
                    element.wait_for_element_state('visible', timeout=5000)
                    element.wait_for_element_state('stable', timeout=5000)
                    
                    # 点击元素
                    element.click()
                    self.log(f"✅ 成功点击 {element_name}")

                    # 增加1秒延迟确保操作稳定
                    time.sleep(1)

                    # 等待页面响应
                    try:
                        self.page.wait_for_load_state('networkidle', timeout=10000)
                    except:
                        pass
                    return True
                    
                except Exception as e:
                    self.log(f"❌ 点击失败: {e}")
            
            # 如果失败，刷新页面重试
            if attempt < retries - 1:
                self.log("🔄 刷新页面后重试...")
                self.page.reload(wait_until='domcontentloaded')
                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                time.sleep(2)

        self.log(f"❌ 最终未能点击 {element_name}")
        return False
    
    def smart_fill(self, element_name, text, retries=3):
        """智能填写输入框"""
        element_config = self.selectors.get(element_name)
        if not element_config:
            self.log(f"❌ 未找到元素配置: {element_name}")
            return False
        
        for attempt in range(retries):
            self.log(f"🔄 尝试填写 {element_name} (第 {attempt+1}/{retries} 次)")
            
            element, selector = self.smart_wait_for_element(element_config)
            
            if element:
                try:
                    # 确保元素可见和可编辑
                    element.wait_for_element_state('visible', timeout=5000)
                    element.wait_for_element_state('editable', timeout=5000)
                    
                    # 清空并填写
                    element.fill('')  # 先清空
                    element.fill(text)
                    
                    # 增加1秒延迟确保填写稳定
                    time.sleep(1)

                    # 验证填写结果
                    filled_value = element.input_value()
                    if filled_value == text:
                        self.log(f"✅ 成功填写 {element_name}: {text}")
                        return True
                    else:
                        self.log(f"⚠️ 填写验证失败: 期望 '{text}', 实际 '{filled_value}'")
                        
                except Exception as e:
                    self.log(f"❌ 填写失败: {e}")
            
            # 如果失败，刷新页面重试
            if attempt < retries - 1:
                self.log("🔄 刷新页面后重试...")
                self.page.reload(wait_until='domcontentloaded')
                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                time.sleep(2)

        self.log(f"❌ 最终未能填写 {element_name}")
        return False
    
    def navigate_to_signup(self):
        """导航到注册页面"""
        try:
            # 方案1（最可靠）：直接访问 Auth0 authorize 端点，跳过 SPA
            self.log("🌐 直接访问 Auth0 注册页面...")
            auth_url = (
                "https://auth.tavily.com/authorize"
                "?response_type=code"
                "&client_id=RRIAvvXNFxpfTWIozX1mXqLnyUmYSTrQ"
                "&redirect_uri=https%3A%2F%2Fapp.tavily.com%2Fapi%2Fauth%2Fcallback"
                "&scope=openid%20profile%20email"
                "&screen_hint=signup"
            )
            self.page.goto(auth_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)

            # 检查是否到达了注册页面
            if "auth.tavily.com" in self.page.url:
                self.log(f"✅ 已到达 Auth0 注册页面: {self.page.url}")
                return True

            # 方案2：回退到原始方式
            self.log("⚠️ Auth0 直达失败，尝试通过 app.tavily.com...")
            self.page.goto(TAVILY_HOME_URL, wait_until='domcontentloaded', timeout=60000)
            for _ in range(10):
                time.sleep(2)
                if "auth.tavily.com" in self.page.url:
                    break

            if self.smart_click('signup_button'):
                self.log("✅ 成功导航到注册页面")
                return True

            self.log("⚠️ 未找到Sign Up按钮，尝试直接访问注册页面...")
            self.page.goto(TAVILY_SIGNUP_URL, wait_until='domcontentloaded', timeout=60000)
            return True

        except Exception as e:
            self.log(f"❌ 导航到注册页面失败: {e}")
            return False
    
    def fill_registration_form(self):
        """填写注册表单"""
        try:
            # 通过 provider 创建邮箱
            self.email = self.provider.create_email(self.email_prefix)
            self.log(f"📧 注册邮箱: {self.email}")

            # 智能填写邮箱
            if not self.smart_fill('email_input', self.email):
                return False

            # 先解决 Turnstile，再点 Continue
            if not self.solve_turnstile_if_present():
                self.log("⚠️ Turnstile 解决失败，尝试继续...")

            # 智能点击继续按钮
            if not self.smart_click('continue_button'):
                return False

            self.log("✅ 注册表单填写完成")
            return True

        except Exception as e:
            self.log(f"❌ 填写注册表单失败: {e}")
            return False

    def solve_turnstile_if_present(self):
        """检测并解决 Cloudflare Turnstile 验证"""
        try:
            self.log("🔍 检查是否有 Turnstile 验证...")
            time.sleep(5)

            if CAPTCHA_SOLVER == "browser":
                # 免费模式：浏览器内点击复选框
                from solvers.browser_solver import solve_turnstile_browser
                return solve_turnstile_browser(self.page)
            elif CAPTCHA_SOLVER == "turnstile-solver":
                # 本地 Turnstile-Solver API
                from solvers.turnstile_api_solver import solve_turnstile_via_api, extract_sitekey_from_page, inject_turnstile_token

                sitekey = extract_sitekey_from_page(self.page)
                if not sitekey:
                    self.log("✅ 未检测到 Turnstile，跳过")
                    return True

                self.log(f"⚠️ 检测到 Turnstile! sitekey: {sitekey[:20]}...")

                current_url = self.page.url
                from config import TURNSTILE_SOLVER_URL
                token = solve_turnstile_via_api(TURNSTILE_SOLVER_URL, current_url, sitekey)

                if not token:
                    self.log("❌ Turnstile 解决失败")
                    return False

                inject_turnstile_token(self.page, token)
                time.sleep(3)

                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass

                self.log("✅ Turnstile 验证已通过")
                return True
            else:
                # 付费模式：CapSolver API
                from solvers.capsolver_solver import solve_turnstile, extract_turnstile_sitekey, inject_turnstile_token

                sitekey = extract_turnstile_sitekey(self.page)
                if not sitekey:
                    self.log("✅ 未检测到 Turnstile，跳过")
                    return True

                self.log(f"⚠️ 检测到 Turnstile! sitekey: {sitekey[:20]}...")

                current_url = self.page.url
                token = solve_turnstile(current_url, sitekey)

                if not token:
                    self.log("❌ Turnstile 解决失败")
                    return False

                inject_turnstile_token(self.page, token)
                time.sleep(3)

                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass

                self.log("✅ Turnstile 验证已通过")
                return True

        except Exception as e:
            self.log(f"❌ Turnstile 处理异常: {e}")
            return False

    def fill_password(self):
        """填写密码"""
        try:
            self.log("🔐 正在填写密码...")

            # 先尝试直接找密码框
            element_config = self.selectors['password_input']
            element, selector = self.smart_wait_for_element(element_config, timeout=5000)

            # 如果找不到密码框，可能有 Turnstile 挡着
            if not element:
                self.log("⚠️ 密码框未出现，尝试解决 Turnstile...")
                if self.solve_turnstile_if_present():
                    # Turnstile 解决后需要重新点击 Continue 提交表单
                    self.log("🔄 Turnstile 已解决，重新点击 Continue...")
                    self.smart_click('continue_button')
                    time.sleep(5)
                else:
                    return False

            # 智能填写密码
            if not self.smart_fill('password_input', self.password):
                return False

            # 智能点击提交按钮
            if not self.smart_click('submit_button'):
                return False

            # 提交后也可能有 Turnstile
            time.sleep(2)
            self.solve_turnstile_if_present()

            self.log("✅ 密码填写完成")
            return True

        except Exception as e:
            self.log(f"❌ 填写密码失败: {e}")
            return False

    def run_registration(self):
        """运行完整的智能注册流程"""
        try:
            self.log("🚀 开始智能注册流程...")

            if not self.navigate_to_signup():
                raise Exception("导航到注册页面失败")

            if not self.fill_registration_form():
                raise Exception("填写注册表单失败")

            if not self.fill_password():
                raise Exception("填写密码失败")

            self.log("🎉 智能注册流程完成!")
            return True

        except Exception as e:
            self.log(f"❌ 智能注册流程失败: {e}")
            return False

    def run_complete_automation(self):
        """运行完整的智能自动化流程：注册 + 邮件验证 + API key获取"""
        try:
            self.log("🚀 开始完整的智能自动化流程...")

            # 步骤1: 注册账户
            self.log("📋 步骤1: 智能注册账户...")
            if not self.run_registration():
                raise Exception("注册流程失败")

            # 步骤2: 邮件验证和登录
            self.log("📋 步骤2: 邮件验证和登录...")
            api_key = self.handle_email_verification_and_login()

            if api_key:
                self.log(f"🎉 完整自动化流程成功完成!")
                self.log(f"📧 注册邮箱: {self.email}")
                self.log(f"🔐 密码: {self.password}")
                self.log(f"🔑 API Key: {api_key}")

                # 保存API key
                save_api_key(self.email, api_key, self.password)
                return api_key
            else:
                raise Exception("邮件验证或API key获取失败")

        except Exception as e:
            self.log(f"❌ 完整自动化流程失败: {e}")
            return None

    def handle_email_verification_and_login(self):
        """处理邮件验证和登录，返回API key"""
        try:
            self.log("📧 通过邮箱后端查询验证邮件...")

            # 通过 provider 轮询验证邮件
            verification_link = self.provider.check_for_verification_email(self.email)

            if not verification_link:
                raise Exception("未找到验证邮件")

            self.log(f"✅ 找到验证链接: {verification_link}")

            # 在当前浏览器中访问验证链接
            self.log("🔗 在浏览器中访问验证链接...")
            self.page.goto(verification_link, wait_until='domcontentloaded', timeout=60000)
            try:
                self.page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass
            time.sleep(3)

            # 检查是否需要登录
            current_url = self.page.url
            page_content = self.page.content().lower()

            if "login" in current_url.lower() or "sign in" in page_content:
                self.log("🔑 需要登录 Tavily 账户...")
                if not self.login_to_tavily():
                    raise Exception("Tavily 登录失败")
                self.log("✅ Tavily 登录成功!")

            # 获取 API key
            self.log("🔑 获取 API key...")
            api_key = self.get_api_key()

            if api_key:
                self.log(f"🎉 成功获取 API key: {api_key}")
                # 清理邮件
                self.provider.cleanup(self.email)
                return api_key
            else:
                raise Exception("未能获取 API key")

        except Exception as e:
            self.log(f"❌ 邮件验证和登录失败: {e}")
            return None

    def login_to_tavily(self):
        """登录 Tavily 账户"""
        try:
            # 填写邮箱
            if not self.smart_fill('email_input', self.email):
                return False
            if not self.smart_click('continue_button'):
                return False
            time.sleep(2)
            # 填写密码
            if not self.smart_fill('password_input', self.password):
                return False
            if not self.smart_click('submit_button'):
                return False
            time.sleep(3)
            return True
        except Exception as e:
            self.log(f"❌ 登录失败: {e}")
            return False

    def get_api_key(self):
        """从 Tavily 仪表板获取 API key"""
        try:
            import re
            # 尝试直接导航到 API key 页面
            self.page.goto("https://app.tavily.com/home", wait_until='domcontentloaded', timeout=60000)
            try:
                self.page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass
            time.sleep(3)

            # 在页面中查找 API key (格式: tvly-xxx)
            page_text = self.page.content()
            api_key_match = re.search(r'tvly-[A-Za-z0-9\-_]{20,}', page_text)
            if api_key_match:
                return api_key_match.group(0)

            # 尝试点击显示 API key 的按钮
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
                        time.sleep(2)
                        page_text = self.page.content()
                        api_key_match = re.search(r'tvly-[A-Za-z0-9\-_]{20,}', page_text)
                        if api_key_match:
                            return api_key_match.group(0)
                except:
                    continue

            self.log("⚠️ 未在页面中找到 API key")
            return None

        except Exception as e:
            self.log(f"❌ 获取 API key 失败: {e}")
            return None

"""
配置文件 - 复制为 config.py 并填写你的信息
cp config.example.py config.py
"""

# 邮箱后端: "cloudflare" 或 "duckmail"
EMAIL_PROVIDER = "cloudflare"

# ═══ Cloudflare Email Worker (EMAIL_PROVIDER = "cloudflare" 时必填) ═══
EMAIL_DOMAIN = ""           # 你的域名，如 example.com
EMAIL_PREFIX = "tavily"     # 邮箱前缀，生成如 tavily-abc12345@example.com
EMAIL_API_URL = ""          # Email Worker URL，如 https://mail.example.com
EMAIL_API_TOKEN = ""        # Email Worker API Token

# ═══ DuckMail (EMAIL_PROVIDER = "duckmail" 时必填) ═══
DUCKMAIL_API_BASE = "https://api.duckmail.sbs"
DUCKMAIL_BEARER = ""        # DuckMail API Key (dk_xxx)
DUCKMAIL_DOMAIN = "duckmail.sbs"

# ═══ 验证码 ═══
# 解决方式: "browser" (免费) 或 "capsolver" (付费 API) 或 "turnstile-solver" (本地 API)
CAPTCHA_SOLVER = "browser"

# CapSolver (CAPTCHA_SOLVER = "capsolver" 时必填)
CAPSOLVER_API_KEY = ""      # 从 capsolver.com 获取

# Turnstile-Solver (CAPTCHA_SOLVER = "turnstile-solver" 时必填)
TURNSTILE_SOLVER_URL = "http://127.0.0.1:5000"  # 本地 Turnstile-Solver 地址

# ═══ 注册配置 ═══
DEFAULT_PASSWORD = "TavilyAuto123!"
API_KEYS_FILE = "api_keys.md"

# ═══ 等待时间（秒） ═══
WAIT_TIME_SHORT = 2
WAIT_TIME_MEDIUM = 5
WAIT_TIME_LONG = 10
EMAIL_CHECK_INTERVAL = 10
MAX_EMAIL_WAIT_TIME = 300   # 5分钟

# ═══ 浏览器 ═══
HEADLESS = False            # True = 后台运行
BROWSER_TIMEOUT = 30000     # 30秒
BROWSER_TYPE = "firefox"    # 回退浏览器类型（优先使用 patchright chromium）

# ═══ Proxy 自动上传 ═══
# 注册成功后自动将 API Key 上传到 Proxy 网关
PROXY_AUTO_UPLOAD = False
PROXY_URL = ""                  # Proxy 地址，如 http://localhost:9874
PROXY_ADMIN_PASSWORD = ""       # Proxy 管理密码

# ═══ Tavily ═══
TAVILY_HOME_URL = "https://app.tavily.com/home"
TAVILY_SIGNUP_URL = "https://app.tavily.com/home"

"""
配置文件模板 - 复制为 config.py 并填写你的信息
cp config.example.py config.py
"""

# === 邮箱后端 ===
# 可选: "cloudflare" 或 "duckmail"
EMAIL_PROVIDER = "cloudflare"

# --- Cloudflare Email Worker ---
EMAIL_DOMAIN = ""           # 你的域名, 如 example.com
EMAIL_PREFIX = "tavily"     # 邮箱前缀, 生成如 tavily-abc12345@example.com
EMAIL_API_URL = ""          # Email Worker URL, 如 https://mail.example.com
EMAIL_API_TOKEN = ""        # Email Worker API Token

# --- DuckMail ---
DUCKMAIL_API_BASE = "https://api.duckmail.sbs"
DUCKMAIL_BEARER = ""        # DuckMail API Key (dk_xxx)
DUCKMAIL_DOMAIN = "duckmail.sbs"

# === 验证码 ===
# 可选: "browser" (免费推荐) / "capsolver" (付费) / "turnstile-solver" (本地)
CAPTCHA_SOLVER = "browser"
CAPSOLVER_API_KEY = ""
TURNSTILE_SOLVER_URL = "http://127.0.0.1:5000"

# === 注册配置 ===
DEFAULT_PASSWORD = ""       # 留空 = 每次自动生成随机密码
COOLDOWN_SECONDS = 45       # 两次注册间隔 (秒), 可调低到30
MAX_THREADS = 2             # 最大并行线程数

# === 文件输出 ===
API_KEYS_FILE = "api_keys.md"   # 完整账户信息 (MD表格)
API_KEYS_TXT = "api_keys.txt"   # 纯 Key 列表 (一行一个)

# === 等待时间 (秒) ===
WAIT_TIME_SHORT = 1
WAIT_TIME_MEDIUM = 3
WAIT_TIME_LONG = 8
EMAIL_CHECK_INTERVAL = 8
MAX_EMAIL_WAIT_TIME = 180   # 3分钟

# === 浏览器 ===
HEADLESS = False            # True = 后台运行
BROWSER_TIMEOUT = 30000     # 毫秒
BROWSER_TYPE = "firefox"    # 回退浏览器 (优先使用 patchright chromium)

# === 代理网关 ===
PROXY_AUTO_UPLOAD = False
PROXY_URL = ""              # 如 https://tav.example.com 或 http://localhost:9874
PROXY_ADMIN_PASSWORD = ""
UPLOAD_RETRY = 3            # 上传失败重试次数

# === Tavily ===
TAVILY_HOME_URL = "https://app.tavily.com/home"
TAVILY_SIGNUP_URL = "https://app.tavily.com/home"

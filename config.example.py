"""
配置文件 - 复制为 config.py 并填写你的信息
cp config.example.py config.py
"""

# ═══════════════════════════════════════════════════
#  必填项（只需填这几项就能运行）
# ═══════════════════════════════════════════════════

# 邮箱后端: "cloudflare" 或 "duckmail"
EMAIL_PROVIDER = "cloudflare"

# Cloudflare 邮箱配置
EMAIL_DOMAIN = ""           # 你的域名，如 example.com
EMAIL_API_URL = ""          # Email Worker URL，如 https://mail.example.com
EMAIL_API_TOKEN = ""        # Email Worker API Token

# ═══════════════════════════════════════════════════
#  网关连接（填了自动上传 Key 到远程 Proxy）
# ═══════════════════════════════════════════════════

PROXY_AUTO_UPLOAD = False
PROXY_URL = ""              # 如 https://tav.example.com
PROXY_ADMIN_PASSWORD = ""   # Proxy 管理密码

# ═══════════════════════════════════════════════════
#  以下为可选项，一般不用改
# ═══════════════════════════════════════════════════

EMAIL_PREFIX = "tavily"     # 邮箱前缀

# DuckMail（仅 EMAIL_PROVIDER = "duckmail" 时需要）
DUCKMAIL_API_BASE = "https://api.duckmail.sbs"
DUCKMAIL_BEARER = ""
DUCKMAIL_DOMAIN = "duckmail.sbs"

# 验证码: "browser"(免费推荐) / "capsolver"(付费) / "turnstile-solver"(本地)
CAPTCHA_SOLVER = "browser"
CAPSOLVER_API_KEY = ""
TURNSTILE_SOLVER_URL = "http://127.0.0.1:5000"

# 注册
DEFAULT_PASSWORD = ""       # 留空 = 每次随机生成
API_KEYS_FILE = "api_keys.md"
API_KEYS_TXT = "api_keys.txt"

# 等待时间（秒）
WAIT_TIME_SHORT = 2
WAIT_TIME_MEDIUM = 5
WAIT_TIME_LONG = 10
EMAIL_CHECK_INTERVAL = 10
MAX_EMAIL_WAIT_TIME = 300

# 浏览器
HEADLESS = False
BROWSER_TIMEOUT = 30000
BROWSER_TYPE = "firefox"

# Tavily URL（一般不用改）
TAVILY_HOME_URL = "https://app.tavily.com/home"
TAVILY_SIGNUP_URL = "https://app.tavily.com/home"

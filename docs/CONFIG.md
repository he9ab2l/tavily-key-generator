# 配置说明

所有配置在 `config.py` 中。首次使用前需要从模板创建：

```bash
cp config.example.py config.py
```

## 必填配置

### 邮箱后端

```python
EMAIL_PROVIDER = "cloudflare"     # "cloudflare" 或 "duckmail"
EMAIL_DOMAIN = "example.com"      # 你的域名
EMAIL_API_URL = "https://mail.example.com"  # Email Worker 地址
EMAIL_API_TOKEN = "your-token"    # API Token
```

## 可选配置

### 注册参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DEFAULT_PASSWORD` | `""` (随机) | 注册密码，留空则每次随机生成 |
| `COOLDOWN_SECONDS` | `45` | 注册间隔（秒），最低建议30 |
| `MAX_THREADS` | `2` | 并行线程数，建议2-3 |

### 验证码

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CAPTCHA_SOLVER` | `"browser"` | 解码方式 |
| `CAPSOLVER_API_KEY` | `""` | CapSolver API Key |
| `TURNSTILE_SOLVER_URL` | `"http://127.0.0.1:5000"` | 本地解码服务地址 |

### 代理网关

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PROXY_AUTO_UPLOAD` | `False` | 注册后自动上传到网关 |
| `PROXY_URL` | `""` | 网关地址 |
| `PROXY_ADMIN_PASSWORD` | `""` | 网关管理密码 |
| `UPLOAD_RETRY` | `3` | 上传失败重试次数 |

### 等待时间

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `WAIT_TIME_SHORT` | `1` | 短等待 |
| `WAIT_TIME_MEDIUM` | `3` | 中等待 |
| `WAIT_TIME_LONG` | `8` | 长等待 |
| `EMAIL_CHECK_INTERVAL` | `8` | 邮件检查间隔 |
| `MAX_EMAIL_WAIT_TIME` | `180` | 邮件最大等待时间 |

### 浏览器

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `HEADLESS` | `False` | True=后台运行，False=可见模式 |
| `BROWSER_TIMEOUT` | `30000` | 浏览器超时（毫秒） |
| `BROWSER_TYPE` | `"firefox"` | 回退浏览器类型 |

## 配置示例

最小配置（只填必要项）：

```python
EMAIL_PROVIDER = "cloudflare"
EMAIL_DOMAIN = "heabl.top"
EMAIL_API_URL = "https://mail.heabl.top"
EMAIL_API_TOKEN = "your-jwt-token"
```

完整配置（含代理上传）：

```python
EMAIL_PROVIDER = "cloudflare"
EMAIL_DOMAIN = "heabl.top"
EMAIL_API_URL = "https://mail.heabl.top"
EMAIL_API_TOKEN = "your-jwt-token"

PROXY_AUTO_UPLOAD = True
PROXY_URL = "https://tav.heabl.top"
PROXY_ADMIN_PASSWORD = "your-password"

COOLDOWN_SECONDS = 30
MAX_THREADS = 3
```

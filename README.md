# Tavily Key Generator + API Proxy

自动批量注册 Tavily 账户获取 API Key，并通过网关代理统一管理和分发。

## 功能特性

- **自动注册** — 基于 patchright（反检测 Playwright）自动完成 Tavily 账户注册
- **Turnstile 验证码** — 内建浏览器自动解码，支持 CapSolver / Turnstile-Solver 作为备选
- **邮件验证** — 自动获取验证邮件并完成账户激活
- **API Key 获取** — 注册完成后自动提取 API Key
- **多线程** — 支持并行注册，带冷却间隔避免风控
- **API 代理网关** — Docker 部署，轮询分发多个 Key，Web 管理面板

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/heabl/tavily-key-generator.git
cd tavily-key-generator
pip install -r requirements.txt
patchright install chromium
```

### 2. 配置

```bash
cp config.example.py config.py
```

编辑 `config.py`，填写以下必要信息：

| 配置项 | 说明 |
|--------|------|
| `EMAIL_PROVIDER` | 邮箱后端：`cloudflare` 或 `duckmail` |
| `EMAIL_DOMAIN` | 你的域名（Cloudflare） |
| `EMAIL_API_URL` | Email Worker API 地址 |
| `EMAIL_API_TOKEN` | Email Worker API Token |
| `CAPTCHA_SOLVER` | 验证码方式：`browser`（推荐）/ `capsolver` / `turnstile-solver` |

### 3. 运行

```bash
python main.py
```

按提示输入注册数量和线程数即可开始自动注册。

## 验证码解决方案

| 方案 | 成本 | 说明 |
|------|------|------|
| `browser` | 免费 | patchright 内建反检测，浏览器内自动通过 Turnstile（推荐） |
| `capsolver` | ~$0.001/次 | CapSolver API，需填写 `CAPSOLVER_API_KEY` |
| `turnstile-solver` | 免费 | 本地 [Turnstile-Solver](https://github.com/Theyka/Turnstile-Solver) 服务 |

## 邮箱后端

### Cloudflare Email Worker

支持两种 API 风格：
- **标准 Worker**：`GET /messages?address=xxx`
- **临时邮箱系统**：`GET /api/emails?mailbox=xxx`（自动检测并适配）

### DuckMail

使用 [DuckMail](https://duckmail.sbs) 服务，填写 `DUCKMAIL_BEARER` 即可。

## API 代理网关

位于 `proxy/` 目录，通过 Docker 部署：

```bash
cd proxy/
cp .env.example .env
# 编辑 .env 设置 ADMIN_PASSWORD
docker compose up -d
```

访问 `http://localhost:9874` 进入管理面板。

### 功能
- 轮询分发多个 API Key
- Token 认证和配额控制
- 使用统计和用量监控
- 批量导入/导出 Key
- Web 管理控制台

### 自动上传

在 `config.py` 中开启：

```python
PROXY_AUTO_UPLOAD = True
PROXY_URL = "http://localhost:9874"
PROXY_ADMIN_PASSWORD = "your-password"
```

注册成功后 API Key 会自动上传到代理网关。

## 项目结构

```
├── main.py                      # 主入口，多线程注册
├── intelligent_tavily_automation.py  # 核心自动化逻辑
├── browser_solver.py            # 浏览器内 Turnstile 解码
├── capsolver_solver.py          # CapSolver API 解码
├── turnstile_api_solver.py      # Turnstile-Solver 适配器
├── utils.py                     # 工具函数（保存 Key、上传 Proxy）
├── config.example.py            # 配置模板
├── requirements.txt             # Python 依赖
├── email_providers/             # 邮箱后端
│   ├── base.py                  # 抽象基类
│   ├── cloudflare.py            # Cloudflare Email Worker
│   └── duckmail.py              # DuckMail
└── proxy/                       # API 代理网关
    ├── server.py                # FastAPI 服务
    ├── database.py              # SQLite 数据库
    ├── key_pool.py              # Key 轮询池
    ├── docker-compose.yml       # Docker 部署
    ├── Dockerfile
    └── templates/               # Web 管理面板
```

## 技术实现

- **patchright** — 反检测版 Playwright，绕过 Cloudflare Turnstile 自动化检测
- **Auth0 直达** — 直接调用 Auth0 authorize 端点，跳过 SPA 重定向
- **invisible Turnstile 支持** — 自动检测隐式验证码并等待自动验证完成
- **FastAPI + SQLite** — 轻量代理网关，Docker 一键部署

## 注意事项

- 首次 Turnstile 验证偶尔需要重试，属于正常行为
- 建议 `HEADLESS = False`（可见模式）以提高 Turnstile 通过率
- 多线程注册时建议 2-3 线程，过多可能触发风控
- API Key 保存在 `api_keys.md` 中

## License

MIT

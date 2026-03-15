# Tavily Key Generator

自动批量注册 Tavily 账户、提取 API Key，配合 Proxy 网关统一管理和分发。

## Features

- **自动注册** — patchright（反检测 Playwright）全流程自动化
- **随机密码** — 每个账户生成独立随机强密码，提高安全性
- **Turnstile 验证码** — 浏览器原生自动通过，支持 CapSolver / Turnstile-Solver 备选
- **邮件验证** — 自动获取验证邮件并完成激活
- **多线程并行** — 并发注册，带冷却间隔避免风控
- **双重保存** — API Key 同时保存到 `api_keys.txt`（纯 Key）和 `api_keys.md`（完整信息表格）
- **API Proxy 网关** — Docker 部署，轮询分发多 Key，Web 管理面板

## Quick Start

### 1. 安装

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

编辑 `config.py`：

| 配置项 | 说明 | 必填 |
|--------|------|:----:|
| `EMAIL_PROVIDER` | 邮箱后端：`cloudflare` 或 `duckmail` | Yes |
| `EMAIL_DOMAIN` | 你的域名（Cloudflare 后端） | Yes |
| `EMAIL_API_URL` | Email Worker API 地址 | Yes |
| `EMAIL_API_TOKEN` | Email Worker API Token | Yes |
| `DEFAULT_PASSWORD` | 留空 = 每次自动生成随机密码 | No |
| `CAPTCHA_SOLVER` | `browser`（推荐）/ `capsolver` / `turnstile-solver` | No |

### 3. 运行

```bash
python main.py
```

或使用一键启动脚本（Windows）：

```bash
start.bat
```

按提示输入注册数量和线程数即可。

## 数据保存

注册成功后数据双重保存：

| 文件 | 格式 | 说明 |
|------|------|------|
| `api_keys.txt` | 一行一个 Key | 方便程序直接读取 |
| `api_keys.md` | Markdown 表格 | 包含邮箱、密码、Key、时间 |

两个文件均已在 `.gitignore` 中排除，不会被推送到 GitHub。

## Captcha Solvers

| 方案 | 成本 | 说明 |
|------|------|------|
| `browser` | 免费 | patchright 反检测 + 浏览器内自动通过（推荐） |
| `capsolver` | ~$0.001/次 | [CapSolver](https://capsolver.com) API |
| `turnstile-solver` | 免费 | 本地 [Turnstile-Solver](https://github.com/Theyka/Turnstile-Solver) |

## Email Backends

**Cloudflare Email Worker** — 支持标准 Worker API 和临时邮箱系统 API，自动适配。

**DuckMail** — 使用 [DuckMail](https://duckmail.sbs) 临时邮箱服务，填写 `DUCKMAIL_BEARER` 即可。

## API Proxy Gateway

位于 `proxy/` 目录，通过 Docker 一键部署：

```bash
cd proxy
cp .env.example .env   # 编辑设置 ADMIN_PASSWORD
docker compose up -d
```

访问 `http://localhost:9874` 进入 Web 管理面板。

功能：
- 轮询分发多个 API Key
- Token 认证和配额控制（时/日/月）
- 使用统计和用量监控
- 批量导入/导出 Key
- 自动禁用失效 Key

在 `config.py` 中开启自动上传：

```python
PROXY_AUTO_UPLOAD = True
PROXY_URL = "http://localhost:9874"
PROXY_ADMIN_PASSWORD = "your-password"
```

## Project Structure

```
tavily-key-generator/
├── main.py                          # 主入口，多线程注册编排
├── intelligent_tavily_automation.py # 核心自动化引擎
├── utils.py                         # 工具函数（保存 Key、上传 Proxy）
├── config.example.py                # 配置模板
├── requirements.txt                 # Python 依赖
├── start.bat                        # Windows 一键启动
├── solvers/                         # 验证码解决器
│   ├── browser_solver.py            # 浏览器原生（免费）
│   ├── capsolver_solver.py          # CapSolver API
│   └── turnstile_api_solver.py      # Turnstile-Solver 适配器
├── email_providers/                 # 邮箱后端
│   ├── base.py                      # 抽象基类
│   ├── cloudflare.py                # Cloudflare Email Worker
│   └── duckmail.py                  # DuckMail
└── proxy/                           # API Proxy 网关
    ├── server.py                    # FastAPI 服务
    ├── database.py                  # SQLite 数据库
    ├── key_pool.py                  # Key 轮询池
    ├── docker-compose.yml           # Docker 部署
    ├── Dockerfile
    └── templates/console.html       # Web 管理面板
```

## Notes

- `HEADLESS = False`（可见模式）可提高 Turnstile 通过率
- 多线程建议 2-3 线程，过多可能触发风控
- 默认冷却间隔 45 秒，可在 `main.py` 中调整 `COOLDOWN`
- `config.py`、`api_keys.md`、`api_keys.txt` 均已加入 `.gitignore`

## License

MIT

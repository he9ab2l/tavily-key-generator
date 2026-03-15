# Tavily Key Generator

自动批量注册 Tavily 账户获取 API Key，通过代理网关统一管理和分发。

## 功能

- 自动注册 Tavily 账户（浏览器自动化）
- 自动通过 Cloudflare Turnstile 验证码
- 自动邮件验证 + 账户激活
- 自动提取 API Key 并保存
- 多线程并行注册，带冷却间隔
- Ctrl+C 优雅退出，数据不丢失
- API 代理网关（Docker 部署，Web 管理面板）
- 注册完成自动上传到代理网关

## 快速开始

### 1. 安装

```bash
git clone https://github.com/he9ab2l/tavily-key-generator.git
cd tavily-key-generator
```

Windows:
```
setup.bat
```

Linux/Mac:
```bash
chmod +x setup.sh && ./setup.sh
```

### 2. 配置

编辑 `config.py`，填写以下必要信息：

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `EMAIL_DOMAIN` | 你的域名 | 是 |
| `EMAIL_API_URL` | Email Worker 地址 | 是 |
| `EMAIL_API_TOKEN` | Email Worker Token | 是 |
| `PROXY_URL` | 代理网关地址 | 可选 |
| `PROXY_ADMIN_PASSWORD` | 网关密码 | 可选 |

详细配置说明见 [docs/CONFIG.md](docs/CONFIG.md)

### 3. 运行

```bash
python main.py
```

或双击 `run.bat`（Windows）。

按提示输入注册数量和线程数，回车开始。按 `Ctrl+C` 可随时停止，已完成的 Key 不会丢失。

## 验证码方案

| 方案 | 成本 | 说明 |
|------|------|------|
| `browser` | 免费 | patchright 内建反检测，自动通过（推荐） |
| `capsolver` | ~$0.001/次 | CapSolver API |
| `turnstile-solver` | 免费 | 本地 Turnstile-Solver 服务 |

## 邮箱后端

| 后端 | 说明 |
|------|------|
| `cloudflare` | Cloudflare Email Worker（推荐） |
| `duckmail` | DuckMail 临时邮箱服务 |

## 代理网关

位于 `proxy/` 目录，Docker 一键部署：

```bash
cd proxy/
cp .env.example .env
# 编辑 .env 设置管理密码
docker compose up -d
```

访问 `http://localhost:9874` 进入管理面板。

功能：
- 轮询分发多个 API Key
- Token 认证和配额管理
- 使用统计和监控
- 批量导入/导出 Key
- Web 控制台
- Key 有效性测试

在 `config.py` 中开启自动上传：

```python
PROXY_AUTO_UPLOAD = True
PROXY_URL = "https://your-domain.com"
PROXY_ADMIN_PASSWORD = "your-password"
```

## 数据存储

注册成功的 Key 保存在两个文件中（双重保存）：

| 文件 | 格式 | 用途 |
|------|------|------|
| `api_keys.md` | MD 表格 | 完整账户信息（邮箱+密码+Key+时间） |
| `api_keys.txt` | 纯文本 | 一行一个 Key，方便批量导入 |

## 项目结构

```
tavily-key-generator/
├── main.py                 # 主入口
├── automation.py           # 核心自动化逻辑
├── utils.py                # 文件保存、代理上传
├── logger.py               # 日志模块
├── config.example.py       # 配置模板
├── setup.bat / setup.sh    # 一键安装
├── run.bat / run.sh        # 一键运行
├── solvers/                # 验证码解决器
│   ├── browser_solver.py   # 浏览器解码（免费）
│   ├── capsolver_solver.py # CapSolver API
│   └── turnstile_api_solver.py
├── email_providers/        # 邮箱后端
│   ├── cloudflare.py       # Cloudflare Email Worker
│   └── duckmail.py         # DuckMail
├── proxy/                  # API 代理网关
│   ├── server.py           # FastAPI 服务
│   ├── database.py         # SQLite 数据库
│   ├── docker-compose.yml
│   └── templates/          # Web 管理面板
└── docs/                   # 文档
```

## 常见问题

**Q: 注册速度慢？**
- 默认间隔 45 秒（防风控），可在 `config.py` 中调整 `COOLDOWN_SECONDS`

**Q: Turnstile 验证失败？**
- 建议 `HEADLESS = False`（可见模式）
- patchright chromium 通过率最高

**Q: 上传到代理失败？**
- 检查 `PROXY_URL` 和 `PROXY_ADMIN_PASSWORD` 是否正确
- 确认服务器代理正在运行

**Q: 数据丢失？**
- 每注册成功一个 Key 立即写入文件
- Ctrl+C 退出会等待当前任务完成
- 双文件备份机制

## License

MIT

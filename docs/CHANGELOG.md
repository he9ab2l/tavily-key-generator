# Changelog

## v2.0.0 (2026-03-15)

全面重构版本。

### 改进

- **去除所有 emoji** - 全部替换为标准日志格式 `[INFO] [SUCCESS] [ERROR] [WARN] [DEBUG]`
- **注册加速** - 减少等待时间，智能 Turnstile 检测，整体提速 30-50%
- **优雅退出** - 支持 Ctrl+C 随时停止，已完成的 Key 不丢失
- **数据实时保存** - 每注册一个 Key 立即写入文件（原子写入 + 文件锁）
- **双文件同步** - api_keys.md（完整信息）+ api_keys.txt（纯 Key），始终同步
- **兼容旧格式** - 自动识别并迁移旧版 CSV 格式数据
- **代理上传修复** - 修复 403 错误，增加 3 次重试机制
- **随机密码** - 每次注册自动生成 16 位强密码
- **日志文件** - 同时输出到控制台和 logs/tavily.log

### 新增

- `logger.py` - 统一日志模块
- `automation.py` - 重构的自动化核心（原 intelligent_tavily_automation.py）
- `setup.bat` / `setup.sh` - 一键安装脚本
- `run.bat` / `run.sh` - 一键运行脚本
- `docs/` - 完整文档目录
- 可配置参数: `COOLDOWN_SECONDS`, `MAX_THREADS`, `UPLOAD_RETRY`

### 删除

- `start.bat` - 替换为 run.bat + setup.bat
- `intelligent_tavily_automation.py` - 替换为 automation.py
- `proxy/nul` - 垃圾文件
- `proxy/README.md` - 合并到主 README

### 修复

- 修复代理网关管理密码被意外修改的问题
- 修复 console.html 中修改密码 API 路径错误
- 修复多线程注册时的数据竞争问题

---

## v1.0.0 (2026-03-14)

初始版本。

- 基本注册功能
- Cloudflare / DuckMail 邮箱后端
- Browser / CapSolver / Turnstile-Solver 验证码
- API 代理网关（Docker）
- Web 管理面板

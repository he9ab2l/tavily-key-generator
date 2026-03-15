# 安装指南

## 系统要求

- Python 3.8+
- Windows / Linux / macOS
- 稳定的网络连接

## 一键安装

### Windows

```
git clone https://github.com/heabl/tavily-key-generator.git
cd tavily-key-generator
setup.bat
```

### Linux / macOS

```bash
git clone https://github.com/heabl/tavily-key-generator.git
cd tavily-key-generator
chmod +x setup.sh && ./setup.sh
```

## 手动安装

```bash
# 1. 克隆项目
git clone https://github.com/heabl/tavily-key-generator.git
cd tavily-key-generator

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装浏览器
patchright install chromium
# 或者: playwright install firefox

# 4. 创建配置文件
cp config.example.py config.py
# 编辑 config.py 填写你的信息
```

## 代理网关安装（可选）

需要 Docker 和 Docker Compose。

```bash
cd proxy/
cp .env.example .env
# 编辑 .env 设置 ADMIN_PASSWORD
docker compose up -d
```

访问 `http://localhost:9874`。

## 验证安装

```bash
python -c "from automation import TavilyAutomation; print('OK')"
```

如果输出 `OK`，安装成功。

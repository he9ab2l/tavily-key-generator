@echo off
chcp 65001 >nul
title Tavily Key Generator - 一键启动
color 0A

echo ══════════════════════════════════════════════════
echo   Tavily Key Generator 一键启动脚本
echo ══════════════════════════════════════════════════
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

:: ═══ 检查 Python ═══
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

:: ═══ 检查 config.py ═══
if not exist "config.py" (
    echo [提示] 未找到 config.py，从模板创建...
    copy config.example.py config.py >nul
    echo [提示] 请编辑 config.py 填写你的配置后重新运行此脚本
    notepad config.py
    pause
    exit /b 0
)

:: ═══ 安装依赖 ═══
echo [1/5] 检查 Python 依赖...
pip install -r requirements.txt -q 2>nul
echo       完成

:: ═══ 安装浏览器 ═══
echo [2/5] 检查 patchright 浏览器...
patchright install chromium >nul 2>&1
echo       完成

:: ═══ 启动 Docker Proxy ═══
echo [3/5] 启动 API Proxy 网关...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    if exist "proxy\docker-compose.yml" (
        if not exist "proxy\.env" (
            copy proxy\.env.example proxy\.env >nul
        )
        docker compose -f proxy\docker-compose.yml up -d --build >nul 2>&1
        if %errorlevel% equ 0 (
            echo       Proxy 已启动 http://localhost:9874
        ) else (
            echo       [跳过] Docker 未运行，请先启动 Docker Desktop
        )
    )
) else (
    echo       [跳过] 未安装 Docker，Proxy 网关不可用
)

:: ═══ 启动 Turnstile-Solver（可选） ═══
echo [4/5] 检查 Turnstile-Solver...
set "SOLVER_DIR="
if exist "%USERPROFILE%\Desktop\Turnstile-Solver\api_solver.py" set "SOLVER_DIR=%USERPROFILE%\Desktop\Turnstile-Solver"
if exist "%PROJECT_DIR%..\Turnstile-Solver\api_solver.py" set "SOLVER_DIR=%PROJECT_DIR%..\Turnstile-Solver"

if defined SOLVER_DIR (
    :: 检查是否已在运行
    powershell -Command "(Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -UseBasicParsing -TimeoutSec 2).StatusCode" >nul 2>&1
    if %errorlevel% equ 0 (
        echo       Turnstile-Solver 已在运行
    ) else (
        echo       启动 Turnstile-Solver...
        start /min "Turnstile-Solver" cmd /c "cd /d "%SOLVER_DIR%" && python api_solver.py --browser_type chromium --debug True"
        timeout /t 5 /nobreak >nul
        echo       Turnstile-Solver 已启动 http://127.0.0.1:5000
    )
) else (
    echo       [跳过] 未找到 Turnstile-Solver
)

:: ═══ 运行注册 ═══
echo [5/5] 启动 Tavily Key Generator...
echo.
echo ══════════════════════════════════════════════════
echo   所有服务已就绪，开始注册
echo ══════════════════════════════════════════════════
echo.

python main.py

echo.
echo ══════════════════════════════════════════════════
echo   运行结束
echo ══════════════════════════════════════════════════
pause

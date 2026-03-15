@echo off
chcp 65001 >nul 2>&1

if not exist config.py (
    echo   [ERROR] config.py not found. Run setup.bat first.
    pause
    exit /b 1
)

python main.py
pause

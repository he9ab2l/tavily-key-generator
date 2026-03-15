@echo off
chcp 65001 >nul 2>&1
echo.
echo   Tavily Key Generator - Setup
echo   ----------------------------
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo   [1/3] Installing dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo   [ERROR] pip install failed
    pause
    exit /b 1
)

echo   [2/3] Installing browser (patchright chromium)...
patchright install chromium
if %errorlevel% neq 0 (
    echo   [WARN] patchright not available, trying playwright...
    playwright install firefox
)

echo   [3/3] Checking config...
if not exist config.py (
    copy config.example.py config.py >nul
    echo   [INFO] config.py created from template
    echo   [INFO] Please edit config.py with your settings before running
    echo.
    notepad config.py
) else (
    echo   [INFO] config.py already exists
)

echo.
echo   Setup complete! Run: python main.py
echo.
pause

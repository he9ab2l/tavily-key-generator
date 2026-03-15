#!/bin/bash
echo ""
echo "  Tavily Key Generator - Setup"
echo "  ----------------------------"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python3 not found"
    exit 1
fi

echo "  [1/3] Installing dependencies..."
pip3 install -r requirements.txt -q

echo "  [2/3] Installing browser..."
patchright install chromium 2>/dev/null || playwright install firefox

echo "  [3/3] Checking config..."
if [ ! -f config.py ]; then
    cp config.example.py config.py
    echo "  [INFO] config.py created. Please edit it with your settings."
else
    echo "  [INFO] config.py exists"
fi

echo ""
echo "  Setup complete! Run: python3 main.py"
echo ""

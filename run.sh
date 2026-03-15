#!/bin/bash
if [ ! -f config.py ]; then
    echo "  [ERROR] config.py not found. Run setup.sh first."
    exit 1
fi
python3 main.py

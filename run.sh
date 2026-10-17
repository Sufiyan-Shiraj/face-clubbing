#!/usr/bin/env bash
set -e

echo "==================================================="
echo "Starting CatLog Desktop Shell"
echo "==================================================="

if [ ! -f ".venv/bin/python" ]; then
    echo "[INFO] Virtual environment not found. Setting up .venv..."
    if command -v uv &> /dev/null; then
        uv venv --python 3.11 .venv
        uv pip install -r requirements.txt
    else
        python3 -m venv .venv
        .venv/bin/pip install -r requirements.txt
    fi
fi

echo "[INFO] Running CatLog Desktop Shell..."
.venv/bin/python main.py "$@"

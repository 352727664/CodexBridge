#!/bin/bash
# CodexBridge — Start the proxy server
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  CodexBridge v2.0"
echo "=========================================="
echo ""

# Load .env if present
if [ -f .env ]; then
    echo "Loading environment variables from .env ..."
    set -a; source .env; set +a
    echo ""
fi

# Check config
if [ ! -f config.json ]; then
    if [ -f config.example.json ]; then
        cp config.example.json config.json
        echo "[CodexBridge] Created config.json from config.example.json"
        echo "[CodexBridge] Please edit config.json to fill in your API keys."
        echo ""
    else
        echo "Error: No config.json found!"
        exit 1
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Install deps if needed
if ! python3 -c "import fastapi, uvicorn, httpx" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "Starting CodexBridge..."
echo "  API: http://localhost:8787"
echo "  Health: http://localhost:8787/health"
echo "  Docs: http://localhost:8787/docs"
echo "=========================================="
echo ""

exec python3 proxy.py "$@"
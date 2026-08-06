#!/bin/bash
# Engine 7 startup script — xiaoke (Mac)
# Loads API keys from configs/.env.xiaoke, then starts engine7

cd "$(dirname "$0")"

# Kill existing engine for xiaoke-mac.json
PIDS=$(pgrep -f "xiaoke-mac.json.*dist/main.mjs" 2>/dev/null)
if [ -n "$PIDS" ]; then
  echo "[start] Killing existing engine (PID: $PIDS)..."
  echo "$PIDS" | xargs kill -9 2>/dev/null
  sleep 2
fi

echo "[start] Starting Engine 7 (xiaoke)..."
echo "[start] Config: configs/xiaoke-mac.json"
echo ""

# Load API keys from ~/.engine7-secrets (outside workspace, not packed by export)
if [ -f "$HOME/.engine7-secrets/xiaoke-mac.env" ]; then
  set -a
  . "$HOME/.engine7-secrets/xiaoke-mac.env"
  set +a
  echo "[start] Loaded API keys from ~/.engine7-secrets/xiaoke-mac.env"
fi

#node node_modules/engine7/dist/main.mjs --engine-config configs/xiaoke-mac.json
node $(npm root -g)/engine7/dist/main.mjs --engine-config configs/xiaoke-mac.json

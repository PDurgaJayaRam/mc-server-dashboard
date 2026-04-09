#!/bin/bash
set -e

echo "[DASHBOARD] === STARTING ==="
echo "[DASHBOARD] Checking Python..."
python3 --version

cd /

echo "[DASHBOARD] Starting gunicorn on port 5000..."
gunicorn --bind 0.0.0.0:5000 \
         --chdir / \
         --workers 1 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         dashboard:app &

GUNICORN_PID=$!
echo "[DASHBOARD] Gunicorn started with PID: $GUNICORN_PID"

sleep 5

if ps -p $GUNICORN_PID > /dev/null; then
    echo "[DASHBOARD] Dashboard is running!"
else
    echo "[DASHBOARD] ERROR: Dashboard failed to start!"
    exit 1
fi

echo "[DASHBOARD] Starting Minecraft Server..."
exec /start

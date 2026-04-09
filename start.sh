#!/bin/bash
echo "[DASHBOARD] === STARTING DASHBOARD ==="
echo "[DASHBOARD] Current user: $(whoami)"
echo "[DASHBOARD] PORT env: $PORT"
echo "[DASHBOARD] Default PORT: 5000"

PORT=${PORT:-5000}
echo "[DASHBOARD] Using PORT: $PORT"

echo "[DASHBOARD] Starting dashboard.py..."
python3 -u /dashboard.py &
DASHBOARD_PID=$!
echo "[DASHBOARD] Started with PID: $DASHBOARD_PID"

sleep 3

if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo "[DASHBOARD] Dashboard process is running"
else
    echo "[DASHBOARD] Dashboard process died! Checking for errors..."
    python3 -u /dashboard.py 2>&1 | head -20
fi

echo "[DASHBOARD] Handing over to Minecraft server..."
exec /start

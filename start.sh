#!/bin/bash
echo "[DASHBOARD] Starting Flask web server..."

PORT=${PORT:-5000}
echo "[DASHBOARD] Using PORT=$PORT, starting dashboard..."

python3 /dashboard.py 2>&1 | sed 's/^/[DASHBOARD] /' &
DASHBOARD_PID=$!

sleep 5

if ps -p $DASHBOARD_PID > /dev/null; then
    echo "[DASHBOARD] Dashboard process is running (PID: $DASHBOARD_PID)"
else
    echo "[DASHBOARD] Dashboard process died!"
fi

echo "[DASHBOARD] Handing over control to Minecraft server script..."
exec /start

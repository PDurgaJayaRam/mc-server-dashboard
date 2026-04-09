#!/bin/bash
echo "[DASHBOARD] Starting Flask web server with retry logic..."

MAX_RETRIES=10
RETRY_DELAY=3
PORT=${PORT:-5000}

echo "[DASHBOARD] Using PORT=$PORT"

for i in $(seq 1 $MAX_RETRIES); do
    echo "[DASHBOARD] Starting dashboard (attempt $i/$MAX_RETRIES)..."
    python3 /dashboard.py 2>&1 | sed 's/^/[DASHBOARD] /' &
    DASHBOARD_PID=$!
    
    sleep $RETRY_DELAY
    
    if curl -s http://localhost:$PORT/login > /dev/null 2>&1; then
        echo "[DASHBOARD] Dashboard started successfully on port $PORT"
        break
    else
        echo "[DASHBOARD] Dashboard not responding, retrying..."
        kill $DASHBOARD_PID 2>/dev/null
        sleep $RETRY_DELAY
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "[DASHBOARD] Failed to start after $MAX_RETRIES attempts, starting anyway..."
        python3 /dashboard.py 2>&1 | sed 's/^/[DASHBOARD] /' &
    fi
done

echo "[DASHBOARD] Handing over control to Minecraft server script..."
exec /start

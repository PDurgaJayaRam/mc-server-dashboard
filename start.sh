#!/bin/bash
echo "[DASHBOARD] Starting Flask internal web server..."

# Start dashboard and pipe all output to the main container log
# We use & to run in background
python3 /dashboard.py 2>&1 | sed 's/^/[DASHBOARD] /' &

echo "[DASHBOARD] Handing over control to Minecraft server script..."
# Use exec to ensure Minecraft becomes PID 1 and receives signals
exec /start

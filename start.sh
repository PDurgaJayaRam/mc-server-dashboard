#!/bin/bash
set -e

echo "[DASHBOARD] Starting Minecraft Dashboard on port 5000..."

# Start gunicorn dashboard
gunicorn --bind 0.0.0.0:5000 \
         --workers 2 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         dashboard:app &

echo "[DASHBOARD] Dashboard started!"

echo "[DASHBOARD] Starting Minecraft Server..."
exec /start

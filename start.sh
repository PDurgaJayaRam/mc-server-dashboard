#!/bin/bash
# Start Flask dashboard in background
python3 /dashboard.py &

# Start Minecraft server (original entrypoint)
exec /start

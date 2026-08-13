#!/bin/bash
# Pings both Render services to keep them from sleeping (free tier sleeps
# after 15 min idle). Run this in a loop, or schedule it with cron/launchd
# to fire every 10 minutes.
#
# One-off use:      ./scripts/keep-alive.sh
# Repeat every 10m:  watch -n 600 ./scripts/keep-alive.sh
# Or add to crontab: */10 * * * * /path/to/scripts/keep-alive.sh >> /tmp/keep-alive.log 2>&1

BACKEND_URL="https://career-advice.onrender.com/health"
FRONTEND_URL="https://career-mentor-3sce.onrender.com"

echo "[$(date)] Pinging backend..."
curl -sf --max-time 30 -o /dev/null -w "  backend:  %{http_code}\n" "$BACKEND_URL" || echo "  backend:  failed"

echo "[$(date)] Pinging frontend..."
curl -sf --max-time 30 -o /dev/null -w "  frontend: %{http_code}\n" "$FRONTEND_URL" || echo "  frontend: failed"

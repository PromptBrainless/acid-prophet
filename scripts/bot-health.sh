#!/usr/bin/env bash
set -euo pipefail

SERVICE="acid-prophet.service"
LOG="/srv/dj-stream/logs/health.log"
mkdir -p "$(dirname "$LOG")"

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if systemctl is-active --quiet "$SERVICE"; then
  echo "$ts OK service=$SERVICE" >> "$LOG"
  exit 0
fi

echo "$ts FAIL service=$SERVICE" >> "$LOG"

# Restart only after a deliberate health failure.
systemctl restart "$SERVICE" || true
sleep 3

if systemctl is-active --quiet "$SERVICE"; then
  echo "$ts RECOVERED service=$SERVICE" >> "$LOG"
  exit 0
fi

echo "$ts UNRECOVERED service=$SERVICE" >> "$LOG"
exit 2

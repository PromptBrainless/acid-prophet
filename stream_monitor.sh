#!/usr/bin/env bash
# Stream-Monitor: Prüft ob Stream läuft, alarmiert bei Ausfall
STREAM_URL="http://127.0.0.1:8000/stream"
BOT_SCRIPT="/srv/dj-stream/telegram_bot.py"
LOG_FILE="/srv/dj-stream/logs/monitor.log"

check_stream() {
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$STREAM_URL" 2>/dev/null)
    if [ "$http_code" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Stream läuft (HTTP $http_code)" >> "$LOG_FILE"
        return 0
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Stream DOWN (HTTP $http_code)" >> "$LOG_FILE"
        return 1
    fi
}

if ! check_stream; then
    # Sende Alarm via Telegram-Bot
    python3 -c "
import sys
sys.path.insert(0, '/srv/dj-stream')
from telegram_bot import send_message
send_message('🚨 ALARM: DJ-Stream ist offline! Port 8000 antwortet nicht.')
" 2>/dev/null
fi

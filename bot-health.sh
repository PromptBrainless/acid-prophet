#!/bin/bash
# bot-health.sh — Prüft Bot-Gesundheit und startet bei Bedarf neu

BOT_PID=$(pgrep -f "telegram_bot.py" | head -1)
LOG="/srv/dj-stream/logs/bot-health.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# 1) Prozess läuft?
if [ -z "$BOT_PID" ]; then
    log "❌ Bot läuft nicht — starte neu..."
    systemctl --user start dj-bot.service 2>/dev/null || {
        nohup /usr/bin/python3 /srv/dj-stream/telegram_bot.py > /srv/dj-stream/logs/bot-stdout.log 2>&1 &
        log "⚠️ systemd-Start fehlgeschlagen, Fallback: direkter Start (PID $!)"
    }
    sleep 3
    BOT_PID=$(pgrep -f "telegram_bot.py" | head -1)
    if [ -n "$BOT_PID" ]; then
        log "✅ Bot gestartet (PID $BOT_PID)"
    else
        log "❌ Bot-Start fehlgeschlagen"
    fi
else
    log "✅ Bot läuft (PID $BOT_PID)"
fi

# 2) Speicherverbrauch
if [ -n "$BOT_PID" ]; then
    MEM=$(ps -p "$BOT_PID" -o rss= 2>/dev/null | tr -d ' ')
    if [ -n "$MEM" ]; then
        MEM_MB=$((MEM / 1024))
        log "📊 Speicher: ${MEM_MB}MB"
        if [ "$MEM_MB" -gt 100 ]; then
            log "⚠️ Speicher über 100MB — prüfe auf Speicherleck"
        fi
    fi
fi

# 3) CPU Last
if [ -n "$BOT_PID" ]; then
    CPU=$(ps -p "$BOT_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    log "📊 CPU: ${CPU}%"
fi

#!/usr/bin/env bash
# YouTube RTMP Pipeline – STREAM_KEY erst eintragen wenn vorhanden
# Audio von Icecast + statisches Background + Overlay-fähig

set -euo pipefail

STREAM_KEY="${YOUTUBE_STREAM_KEY:-}"
ICECAST_URL="${ICECAST_URL:-http://127.0.0.1:8000/stream}"
BACKGROUND="${BACKGROUND:-/srv/dj-stream/overlays/background.jpg}"
# Fallback wenn kein Background-Bild
if [[ ! -f "$BACKGROUND" ]]; then
  BACKGROUND="/srv/dj-stream/youtube-background.jpg"
fi

if [[ -z "$STREAM_KEY" ]]; then
  echo "YOUTUBE_STREAM_KEY nicht gesetzt – Dry-Run / Testmodus"
  echo "Pipeline würde streamen nach: rtmp://a.rtmp.youtube.com/live2/<KEY>"
  echo "Teste lokalen Encode 10s…"
  ffmpeg -re -f lavfi -i "color=c=0x1a0033:s=1920x1080:r=30" \
    -i "$ICECAST_URL" \
    -t 10 \
    -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3500k -bufsize 6000k \
    -pix_fmt yuv420p -g 60 \
    -c:a aac -b:a 192k -ar 44100 \
    -f null - 2>&1 | tail -20
  exit 0
fi

# Produktion
ffmpeg -re \
  -loop 1 -i "$BACKGROUND" \
  -i "$ICECAST_URL" \
  -vf "scale=1920:1080,format=yuv420p" \
  -c:v libx264 -preset veryfast -b:v 3000k \
  -maxrate 3500k -bufsize 6000k \
  -g 60 -keyint_min 60 \
  -c:a aac -b:a 192k -ar 44100 \
  -f flv "rtmp://a.rtmp.youtube.com/live2/${STREAM_KEY}"

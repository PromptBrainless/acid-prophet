#!/bin/bash
# dj-youtube-stream.sh
# 24/7 YouTube Live Stream aus Icecast
# Nutzt vorhandenen DJ-Stream auf Port 8000

set -e

STREAM_KEY="${YOUTUBE_STREAM_KEY:-}"
RADIO_URL="${RADIO_URL:-http://localhost:8000/stream}"
IMAGE="${IMAGE:-/srv/dj-stream/youtube-background.jpg}"

if [ -z "$STREAM_KEY" ]; then
    echo "FEHLER: YOUTUBE_STREAM_KEY nicht gesetzt"
    exit 1
fi

echo "[$(date)] Starte YouTube Live Stream..."
echo "Stream-Key: ${STREAM_KEY:0:8}..."
echo "Radio URL: $RADIO_URL"
echo "Bild: $IMAGE"

while true; do
    ffmpeg \
      -hide_banner \
      -loglevel warning \
      -re \
      -loop 1 -i "$IMAGE" \
      -i "$RADIO_URL" \
      -vf "scale=1920:1080" \
      -c:v libx264 \
      -preset veryfast \
      -b:v 3000k \
      -maxrate 3500k \
      -bufsize 6000k \
      -pix_fmt yuv420p \
      -g 60 \
      -keyint_min 60 \
      -c:a aac \
      -b:a 192k \
      -ar 44100 \
      -f flv \
      "rtmp://a.rtmp.youtube.com/live2/$STREAM_KEY" || true

    echo "[$(date)] FFmpeg beendet. Neustart in 10 Sekunden..."
    sleep 10
done

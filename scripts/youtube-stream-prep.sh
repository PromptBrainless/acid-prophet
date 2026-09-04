#!/usr/bin/env bash
# youtube-stream-prep.sh
# Phase 6 – YouTube-Live-Vorbereitung OHNE Stream-Key
# Erzeugt Pipeline-Skript, systemd-Unit, Overlay-Loop und Checkliste.

set -euo pipefail

TARGET="${TARGET:-/srv/dj-stream}"
OVERLAY_DIR="$TARGET/overlays"
SCRIPTS="$TARGET/scripts"
SYSTEMD_USER="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$OVERLAY_DIR" "$SCRIPTS" "$TARGET/backups"

echo "=== Acid Prophet – YouTube Stream Prep (kein Key nötig) ==="

# 1. Overlay-Update-Loop
cat > "$SCRIPTS/overlay-loop.sh" << 'EOF'
#!/usr/bin/env bash
# Aktualisiert Overlay alle 8 Sekunden
cd /srv/dj-stream
source .venv/bin/activate 2>/dev/null || true
while true; do
  python3 -m app.overlay 2>/dev/null || python3 app/overlay.py 2>/dev/null || true
  sleep 8
done
EOF
chmod +x "$SCRIPTS/overlay-loop.sh"

# 2. FFmpeg-Pipeline-Template (Stream-Key als Platzhalter)
cat > "$SCRIPTS/dj-youtube-stream.sh" << 'EOF'
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
EOF
chmod +x "$SCRIPTS/dj-youtube-stream.sh"

# 3. systemd User Units (ohne Key – nur Overlay + vorbereiteter Stream-Service)
mkdir -p "$SYSTEMD_USER"

cat > "$SYSTEMD_USER/acid-overlay.service" << EOF
[Unit]
Description=Acid Prophet Overlay Updater
After=network.target

[Service]
Type=simple
WorkingDirectory=$TARGET
ExecStart=$SCRIPTS/overlay-loop.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

cat > "$SYSTEMD_USER/acid-youtube-stream.service" << EOF
[Unit]
Description=Acid Prophet YouTube Live Stream
After=network.target
# Startet nur wenn Key gesetzt ist – sonst Dry-Run

[Service]
Type=simple
WorkingDirectory=$TARGET
EnvironmentFile=-$TARGET/.env
ExecStart=$SCRIPTS/dj-youtube-stream.sh
Restart=on-failure
RestartSec=15

[Install]
WantedBy=default.target
EOF

# 4. Minimal-Background generieren falls keins existiert
if [[ ! -f "$OVERLAY_DIR/background.jpg" ]] && command -v convert &>/dev/null; then
  convert -size 1920x1080 "xc:#1a0033" -fill "#9D4EDD" -pointsize 72 \
    -gravity center -annotate 0 "ACID PROPHET" "$OVERLAY_DIR/background.jpg"
  echo "→ Placeholder-Background erzeugt"
elif [[ ! -f "$OVERLAY_DIR/background.jpg" ]]; then
  echo "Hinweis: Kein ImageMagick – Background manuell nach $OVERLAY_DIR/background.jpg legen"
fi

# 5. Checkliste
cat > "$TARGET/docs/YOUTUBE_GO_LIVE_CHECKLIST.md" << 'EOF'
# YouTube Go-Live Checkliste (Acid Prophet)

## Vor dem ersten Stream (ohne Key erledigt)

- [x] Overlay-Engine (`app/overlay.py`)
- [x] `overlays/current.txt` + `current.json` + `status.html`
- [x] Overlay-Loop-Script + systemd Unit
- [x] FFmpeg-Pipeline-Template (`scripts/dj-youtube-stream.sh`)
- [x] systemd Unit für Stream (wartet auf Key)

## Sobald Stream-Key da ist

1. Key in `.env` eintragen:
   ```
   YOUTUBE_STREAM_KEY=xxxx-xxxx-xxxx-xxxx
   ```
2. Optional in YouTube Studio:
   - Latenz: Normal oder Niedrig
   - Auflösung: 1080p
   - Bitrate: ~3000–3500 kbps Video + 192 kbps Audio
3. Services aktivieren:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now acid-overlay.service
   systemctl --user enable --now acid-youtube-stream.service
   ```
4. In OBS / YouTube Studio als Browser-Source:
   - URL: `file:///srv/dj-stream/overlays/status.html`
   - Breite 640, Höhe 220, transparenter Hintergrund
5. Test 2–3 Minuten, dann 24/7 lassen.

## Monitoring

```bash
journalctl --user -u acid-overlay.service -f
journalctl --user -u acid-youtube-stream.service -f
ls -la /srv/dj-stream/overlays/
```

## Rollback

```bash
systemctl --user disable --now acid-youtube-stream.service
systemctl --user disable --now acid-overlay.service
```
EOF

echo
echo "→ Overlay-Loop:     $SCRIPTS/overlay-loop.sh"
echo "→ Stream-Script:    $SCRIPTS/dj-youtube-stream.sh"
echo "→ Overlay Unit:     $SYSTEMD_USER/acid-overlay.service"
echo "→ Stream Unit:      $SYSTEMD_USER/acid-youtube-stream.service"
echo "→ Checkliste:       $TARGET/docs/YOUTUBE_GO_LIVE_CHECKLIST.md"
echo
echo "Aktivieren (Overlay jetzt, Stream später):"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now acid-overlay.service"
echo
echo "=== Prep fertig – kein Stream-Key benötigt ==="

#!/usr/bin/env bash
# Aktualisiert Overlay alle 8 Sekunden
cd /srv/dj-stream
source .venv/bin/activate 2>/dev/null || true
while true; do
  python3 -m app.overlay 2>/dev/null || python3 app/overlay.py 2>/dev/null || true
  sleep 8
done

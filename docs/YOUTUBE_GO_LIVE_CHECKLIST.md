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

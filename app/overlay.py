# /srv/dj-stream/app/overlay.py
"""
Phase 6 – YouTube Live Overlay (ohne Stream-Key)

Erzeugt:
- overlays/current.txt          → einfacher Text-Overlay (ffplayout / OBS Text source)
- overlays/current.json         → strukturierte Daten für Web-Overlay / Browser-Source
- overlays/status.html          → fertige, farbige HTML-Overlay-Seite (Browser Source)

Aktualisiert sich aus:
- SQLite app_state (energy, genre)
- Optional: aktueller Track aus tracks-Tabelle
- Community-Snapshot (falls voting.py vorhanden)

Kein YouTube-Key nötig. Nur lokale Dateien + optional ffplayout API.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app import db, energy, genres
from app.config import ROOT, OVERLAY_TEXT

log = logging.getLogger("acid-prophet.overlay")

OVERLAY_DIR = Path(ROOT) / "overlays"
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_TXT = OVERLAY_DIR / "current.txt"
CURRENT_JSON = OVERLAY_DIR / "current.json"
STATUS_HTML = OVERLAY_DIR / "status.html"
STYLE_CSS = OVERLAY_DIR / "overlay.css"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_state(track_path: Optional[str] = None) -> dict[str, Any]:
    """Sammelt alle Overlay-relevanten Daten."""
    e = db.get_energy()
    g = db.get_genre()
    info = genres.get_genre_info(g) or {}
    color = energy.energy_to_color(e)
    mood = energy.energy_to_mood(e)
    label = energy.energy_to_label(e)

    track = None
    if track_path:
        from app import track_intelligence as ti
        track = ti.get_track(track_path)
    else:
        # Letzten analysierten Track als Fallback
        try:
            from app import track_intelligence as ti
            recent = ti.list_tracks(limit=1)
            track = recent[0] if recent else None
        except Exception:
            track = None

    community = None
    try:
        from app import voting
        snap = voting.compute_community_snapshot(window_minutes=15)
        community = {
            "total_votes": snap.total_votes,
            "up": snap.up,
            "down": snap.down,
            "more_energy": snap.more_energy,
            "less_energy": snap.less_energy,
            "energy_pressure": snap.energy_pressure,
            "track_score": snap.track_score,
        }
    except Exception:
        pass

    return {
        "energy": e,
        "genre": g,
        "genre_display": genres.genre_display(g),
        "mood": mood,
        "label": label,
        "color": color,
        "bpm_range": f"{info.get('bpm_min', '?')}–{info.get('bpm_max', '?')}",
        "track": {
            "title": (track or {}).get("title"),
            "artist": (track or {}).get("artist"),
            "bpm": (track or {}).get("bpm"),
            "key": (track or {}).get("musical_key"),
            "camelot": (track or {}).get("camelot"),
            "energy": (track or {}).get("energy"),
        } if track else None,
        "community": community,
        "updated_at": _utc_now(),
    }


def render_text(state: dict[str, Any]) -> str:
    """Einfacher Text für OBS/ffplayout Text-Source."""
    lines = [
        f"ACID PROPHET  |  Energy {state['energy']}/10  |  {state['genre_display']}",
        f"Mood: {state['mood']}  ·  {state['bpm_range']} BPM",
    ]
    t = state.get("track") or {}
    if t.get("title"):
        artist = t.get("artist") or "Unknown"
        bpm = f" · {t['bpm']:.0f} BPM" if t.get("bpm") else ""
        key = f" · {t.get('camelot') or t.get('key') or ''}"
        lines.append(f"♪ {artist} – {t['title']}{bpm}{key}")
    c = state.get("community")
    if c and c.get("total_votes", 0) > 0:
        lines.append(
            f"Community: ▲{c['up']} ▼{c['down']}  ⚡{c['more_energy']} 🌙{c['less_energy']}"
        )
    return "\n".join(lines)


def render_html(state: dict[str, Any]) -> str:
    """Selbstständige HTML-Seite für Browser-Source (OBS / YouTube Studio)."""
    color = state["color"]
    # Kontrast-Textfarbe
    text_color = "#0a0a0a" if state["energy"] >= 9 else "#f0f0f0"

    track_html = ""
    t = state.get("track") or {}
    if t.get("title"):
        track_html = f"""
        <div class="track">
          <span class="label">NOW</span>
          <span class="title">{t.get('artist') or 'Unknown'} – {t['title']}</span>
          <span class="meta">{(f"{t['bpm']:.0f} BPM" if t.get('bpm') else '')} {(t.get('camelot') or '')}</span>
        </div>
        """

    community_html = ""
    c = state.get("community")
    if c and c.get("total_votes", 0) > 0:
        community_html = f"""
        <div class="community">
          ▲ {c['up']} &nbsp; ▼ {c['down']} &nbsp;
          ⚡ {c['more_energy']} &nbsp; 🌙 {c['less_energy']}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8"/>
  <meta http-equiv="refresh" content="8"/>
  <title>Acid Prophet Overlay</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap');
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      background: transparent;
      font-family: 'Rajdhani', system-ui, sans-serif;
      color: {text_color};
      overflow: hidden;
    }}
    .panel {{
      background: linear-gradient(135deg, {color}cc, {color}99);
      backdrop-filter: blur(8px);
      border: 1px solid {color};
      border-radius: 12px;
      padding: 14px 22px;
      margin: 12px;
      box-shadow: 0 0 24px {color}66;
      min-width: 420px;
      max-width: 640px;
    }}
    .brand {{
      font-family: 'Orbitron', sans-serif;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 0.18em;
      opacity: 0.85;
      margin-bottom: 6px;
    }}
    .energy {{
      font-family: 'Orbitron', sans-serif;
      font-size: 28px;
      font-weight: 700;
      line-height: 1.1;
    }}
    .genre {{
      font-size: 18px;
      font-weight: 600;
      margin-top: 2px;
    }}
    .mood {{
      font-size: 14px;
      opacity: 0.9;
      margin-top: 4px;
    }}
    .track {{
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid {text_color}33;
      font-size: 15px;
    }}
    .track .label {{
      font-size: 11px;
      letter-spacing: 0.12em;
      opacity: 0.7;
      margin-right: 8px;
    }}
    .track .meta {{
      display: block;
      font-size: 13px;
      opacity: 0.8;
      margin-top: 2px;
    }}
    .community {{
      margin-top: 10px;
      font-size: 14px;
      opacity: 0.85;
    }}
  </style>
</head>
<body>
  <div class="panel">
    <div class="brand">ACID PROPHET</div>
    <div class="energy">Energy {state['energy']}/10</div>
    <div class="genre">{state['genre_display']}</div>
    <div class="mood">{state['mood']} · {state['bpm_range']} BPM</div>
    {track_html}
    {community_html}
  </div>
</body>
</html>
"""


def write_overlay(track_path: Optional[str] = None) -> dict[str, str]:
    """Schreibt alle Overlay-Dateien. Returns Pfade."""
    state = collect_state(track_path)

    CURRENT_TXT.write_text(render_text(state), encoding="utf-8")
    CURRENT_JSON.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    STATUS_HTML.write_text(render_html(state), encoding="utf-8")

    # Optional: ffplayout Text-Overlay-Pfad (config)
    try:
        OVERLAY_TEXT.parent.mkdir(parents=True, exist_ok=True)
        if OVERLAY_TEXT != CURRENT_TXT:
            OVERLAY_TEXT.write_text(render_text(state), encoding="utf-8")
    except Exception:
        pass

    log.info("Overlay updated: energy=%s genre=%s", state["energy"], state["genre"])
    return {
        "txt": str(CURRENT_TXT),
        "json": str(CURRENT_JSON),
        "html": str(STATUS_HTML),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    paths = write_overlay()
    print(json.dumps({"ok": True, "paths": paths}, indent=2))


if __name__ == "__main__":
    main()

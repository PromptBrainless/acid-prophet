# /srv/dj-stream/learning/analyze_voting.py
"""
Erweiterung für learning/analyze.py
Analysiert Voting-Muster und schreibt strukturierte Signale
nach reports/ und optional nach memory/pending/.

Aufruf:
  python3 -m learning.analyze_voting
  oder aus learning-loop.sh
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pfad-Anpassung je nach Deployment
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import voting, db

log = logging.getLogger("acid-prophet.analyze_voting")


def analyze() -> dict[str, Any]:
    snapshot = voting.compute_community_snapshot(window_minutes=30)
    profile = voting.build_community_profile(limit=300)

    signals: list[dict[str, Any]] = []

    # Energy-Bias
    if snapshot.total_votes >= 5:
        if snapshot.energy_pressure >= 0.6:
            signals.append({
                "type": "energy_bias",
                "direction": "up",
                "strength": snapshot.energy_pressure,
                "message": "Community drückt klar auf höhere Energy",
                "suggested_action": "energy +1 oder Genre nach oben",
            })
        elif snapshot.energy_pressure <= -0.6:
            signals.append({
                "type": "energy_bias",
                "direction": "down",
                "strength": abs(snapshot.energy_pressure),
                "message": "Community will klar runter",
                "suggested_action": "energy -1 oder Genre nach unten",
            })

    # Track-Score
    if (snapshot.up + snapshot.down) >= 5:
        if snapshot.track_score >= 0.75:
            signals.append({
                "type": "track_love",
                "score": snapshot.track_score,
                "message": "Aktueller Track wird stark geliked",
            })
        elif snapshot.track_score <= 0.3:
            signals.append({
                "type": "track_hate",
                "score": snapshot.track_score,
                "message": "Aktueller Track wird stark gedisliked – Skip empfohlen",
            })

    # Genre-Dominanz
    if profile.get("preferred_genre") and profile.get("votes_analyzed", 0) >= 20:
        signals.append({
            "type": "genre_preference",
            "genre": profile["preferred_genre"],
            "message": f"Langzeit-Präferenz: {profile['preferred_genre']}",
        })

    # Peak-Times
    peaks = profile.get("peak_hours_utc") or []
    if peaks:
        signals.append({
            "type": "peak_activity",
            "hours": peaks,
            "message": "Höchste Voting-Aktivität in diesen UTC-Stunden",
        })

    result = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": {
            "window_minutes": snapshot.window_minutes,
            "total_votes": snapshot.total_votes,
            "energy_pressure": snapshot.energy_pressure,
            "track_score": snapshot.track_score,
            "dominant_genre": snapshot.dominant_genre,
            "suggested_energy": snapshot.suggested_energy,
        },
        "profile_summary": {
            "votes_analyzed": profile.get("votes_analyzed"),
            "preferred_energy": profile.get("preferred_energy"),
            "preferred_genre": profile.get("preferred_genre"),
        },
        "signals": signals,
        "signal_count": len(signals),
    }
    return result


def write_report(result: dict[str, Any], reports_dir: Path | None = None) -> Path:
    if reports_dir is None:
        reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = reports_dir / f"voting-signals-{ts}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    latest = reports_dir / "voting-signals-latest.json"
    latest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Voting analysis written to %s (%s signals)", path, result["signal_count"])
    return path


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    result = analyze()
    path = write_report(result)
    print(json.dumps({"ok": True, "path": str(path), "signals": result["signal_count"]}, indent=2))


if __name__ == "__main__":
    main()

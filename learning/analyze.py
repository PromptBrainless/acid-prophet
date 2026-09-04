#!/usr/bin/env python3
"""Findet einfache, wiederholbare Muster ohne LLM."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/srv/dj-stream")
SIGNALS = sorted((ROOT / "reports").glob("signals-*.json"))[-1]
LESSONS = ROOT / "memory" / "lessons"
PENDING = ROOT / "memory" / "pending"


def main():
    if not SIGNALS.exists():
        print("No signals found")
        return
    data = json.loads(SIGNALS.read_text())
    lessons = []

    votes = data.get("votes", [])
    if votes:
        c = Counter(v["vote"] for v in votes)
        if c.get("more_energy", 0) >= 5 and c.get("more_energy", 0) > c.get("less_energy", 0) * 2:
            lessons.append({
                "id": f"energy-bias-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                "title": "Community will höhere Energy",
                "rule": "Wenn more_energy >> less_energy in 24h → Default-Energy +1 (max 10)",
                "confidence": 0.7,
                "source": "votes",
            })

    errors = data.get("errors", [])
    if len(errors) >= 3:
        lessons.append({
            "id": f"error-spike-{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
            "title": "Fehlerhäufung erkannt",
            "rule": "Bei ≥3 ERROR-Zeilen in kurzer Zeit → Health-Check verschärfen + Alert",
            "confidence": 0.8,
            "source": "logs",
        })

    PENDING.mkdir(parents=True, exist_ok=True)
    for les in lessons:
        path = PENDING / f"{les['id']}.json"
        path.write_text(json.dumps(les, indent=2, ensure_ascii=False))
        print("Pending lesson:", path)


if __name__ == "__main__":
    main()

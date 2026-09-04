#!/usr/bin/env python3
"""
Optional: Aus Conversation / Diffs eine Lesson extrahieren.
Kann von /refine oder vom Timer aufgerufen werden.
Schreibt NUR nach memory/pending/ – nie direkt aktiv.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/srv/dj-stream")
PENDING = ROOT / "memory" / "pending"


def make_lesson(title: str, rule: str, source: str, confidence: float = 0.6):
    PENDING.mkdir(parents=True, exist_ok=True)
    lid = f"refine-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    data = {
        "id": lid,
        "title": title,
        "rule": rule,
        "confidence": confidence,
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (PENDING / f"{lid}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(lid)


if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "Manual refine"
    rule = sys.argv[2] if len(sys.argv) > 2 else "TODO"
    source = sys.argv[3] if len(sys.argv) > 3 else "manual"
    make_lesson(title, rule, source)

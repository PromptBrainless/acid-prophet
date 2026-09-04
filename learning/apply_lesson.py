#!/usr/bin/env python3
"""Verschiebt freigegebene Lessons nach memory/lessons und aktualisiert index."""
from __future__ import annotations
import json, shutil
from pathlib import Path
import sys

ROOT = Path("/srv/dj-stream")
PENDING = ROOT / "memory" / "pending"
LESSONS = ROOT / "memory" / "lessons"
INDEX = ROOT / "memory" / "index.json"


def main(lesson_id: str | None = None):
    LESSONS.mkdir(parents=True, exist_ok=True)
    files = list(PENDING.glob("*.json"))
    if lesson_id:
        files = [f for f in files if f.stem == lesson_id]
    index = json.loads(INDEX.read_text()) if INDEX.exists() else {"lessons": []}
    for f in files:
        data = json.loads(f.read_text())
        target = LESSONS / f.name
        shutil.move(str(f), str(target))
        index["lessons"].append(data)
        print("Applied:", target)
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

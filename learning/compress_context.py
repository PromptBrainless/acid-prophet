#!/usr/bin/env python3
"""Erzeugt eine kompakte Kontext-Zusammenfassung."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/srv/dj-stream")
MEM = ROOT / "memory" / "index.json"
STATE = ROOT / "data" / "acid_prophet.db"


def load_lessons(max_n: int = 15):
    if not MEM.exists():
        return []
    data = json.loads(MEM.read_text())
    return data.get("lessons", [])[-max_n:]


def current_state():
    try:
        import sqlite3
        con = sqlite3.connect(STATE)
        rows = dict(con.execute("SELECT key, value FROM app_state").fetchall())
        con.close()
        return rows
    except Exception:
        return {}


def build_compressed_prompt() -> str:
    lessons = load_lessons()
    state = current_state()
    lines = [
        "=== COMPRESSED CONTEXT ===",
        f"ts: {datetime.now(timezone.utc).isoformat()}",
        f"energy: {state.get('energy', '?')}",
        f"genre: {state.get('genre', '?')}",
        "",
        "ACTIVE LESSONS (must respect):",
    ]
    for les in lessons:
        lines.append(f"- [{les.get('confidence', 0):.1f}] {les.get('title')}: {les.get('rule')}")
    lines.append("")
    lines.append("Keep replies short. Prefer tools over long reasoning.")
    lines.append("=== END COMPRESSED ===")
    return "\n".join(lines)


if __name__ == "__main__":
    text = build_compressed_prompt()
    out = ROOT / "reports" / "compressed-context.txt"
    out.write_text(text)
    print(text)

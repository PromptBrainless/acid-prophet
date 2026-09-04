#!/usr/bin/env python3
"""Sammelt Signale fürs Lernen: Logs, Votes, Fehler, Diffs."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path("/srv/dj-stream")
OUT = ROOT / "reports" / f"signals-{datetime.now(timezone.utc).strftime('%Y%m%d-%H')}.json"


def recent_votes(hours: int = 24):
    db = ROOT / "data" / "acid_prophet.db"
    if not db.exists():
        return []
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    rows = con.execute(
        "SELECT vote, energy_at_vote, genre_at_vote, created_at FROM votes WHERE created_at >= ?",
        (since,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def recent_errors():
    log = ROOT / "logs" / "bot.log"
    if not log.exists():
        return []
    lines = log.read_text(errors="ignore").splitlines()[-200:]
    return [l for l in lines if "ERROR" in l or "Exception" in l]


def health_restarts():
    log = ROOT / "logs" / "health.log"
    if not log.exists():
        return []
    return [l for l in log.read_text().splitlines()[-50:] if "FAIL" in l or "RECOVERED" in l]


def main():
    data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "votes": recent_votes(),
        "errors": recent_errors(),
        "health": health_restarts(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

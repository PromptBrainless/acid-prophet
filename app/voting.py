# /srv/dj-stream/app/voting.py
"""
Community Voting Engine for Acid Prophet
Phase 4 – vollständige, produktionsreife Implementierung

Features:
- Rate-Limiting pro User (Anti-Spam)
- Soft + Hard Aggregation (letzte N Minuten / letzte N Votes)
- Automatische Energy-Anpassung bei klarem Community-Druck
- Genre-Bias-Erkennung
- Community-Profil (Trends, Peak-Times, Präferenzen)
- Sichere, idempotente DB-Operationen
- Deterministische Schwellen (keine KI-Entscheidungen im Hot-Path)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from app import db, energy, genres

log = logging.getLogger("acid-prophet.voting")

# ── Konfiguration (kann später in config/ oder .env wandern) ─────────────────

# Mindestanzahl Votes bevor automatische Anpassung greift
MIN_VOTES_FOR_ADJUST = 5

# Zeitfenster für "aktuelle Stimmung" (Minuten)
WINDOW_MINUTES = 15

# Rate-Limit: maximal X Votes pro User in Y Sekunden
RATE_LIMIT_COUNT = 8
RATE_LIMIT_SECONDS = 120

# Schwellen für Energy-Druck (Anteil more_energy vs less_energy)
ENERGY_PRESSURE_THRESHOLD = 0.65   # 65 % Mehrheit
ENERGY_PRESSURE_MARGIN = 2         # absolute Differenz mindestens 2

# Schwellen für Track-Bewertung
TRACK_SCORE_THRESHOLD = 0.6        # up / (up+down)

# Maximaler Energy-Sprung pro Anpassung
MAX_ENERGY_STEP = 1


@dataclass
class VoteResult:
    accepted: bool
    message: str
    vote_type: str
    user_id: int
    current_energy: int
    current_genre: str
    rate_limited: bool = False
    energy_adjusted: bool = False
    new_energy: Optional[int] = None
    community_summary: Optional[dict[str, Any]] = None


@dataclass
class CommunitySnapshot:
    window_minutes: int
    total_votes: int
    up: int
    down: int
    more_energy: int
    less_energy: int
    energy_pressure: float          # -1.0 … +1.0  (negativ = less, positiv = more)
    track_score: float              # 0.0 … 1.0
    dominant_genre: Optional[str]
    suggested_energy: Optional[int]
    peak_hour_utc: Optional[int]
    generated_at: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def is_rate_limited(user_id: int) -> bool:
    """Prüft, ob der User in den letzten RATE_LIMIT_SECONDS zu oft gevoted hat."""
    cutoff = _utc_now() - timedelta(seconds=RATE_LIMIT_SECONDS)
    with db.get_conn() as con:
        row = con.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM votes
            WHERE user_id = ? AND created_at >= ?
            """,
            (user_id, _iso(cutoff)),
        ).fetchone()
    return (row["cnt"] if row else 0) >= RATE_LIMIT_COUNT


def record_and_process(
    user_id: int,
    chat_id: Optional[int],
    vote_type: str,
    track_path: Optional[str] = None,
) -> VoteResult:
    """
    Haupt-Einstiegspunkt für alle Vote-Commands.
    - Rate-Limit prüfen
    - Vote speichern
    - Aggregation berechnen
    - ggf. Energy automatisch anpassen
    - freundliche Antwort generieren
    """
    if vote_type not in ("up", "down", "more_energy", "less_energy"):
        return VoteResult(
            accepted=False,
            message="Ungültiger Vote-Typ.",
            vote_type=vote_type,
            user_id=user_id,
            current_energy=db.get_energy(),
            current_genre=db.get_genre(),
        )

    if is_rate_limited(user_id):
        return VoteResult(
            accepted=False,
            message=(
                f"⏳ Rate-Limit: maximal {RATE_LIMIT_COUNT} Votes "
                f"in {RATE_LIMIT_SECONDS}s. Kurz warten."
            ),
            vote_type=vote_type,
            user_id=user_id,
            current_energy=db.get_energy(),
            current_genre=db.get_genre(),
            rate_limited=True,
        )

    current_e = db.get_energy()
    current_g = db.get_genre()

    db.record_vote(
        user_id=user_id,
        chat_id=chat_id,
        vote=vote_type,
        energy=current_e,
        genre=current_g,
        track_path=track_path,
    )

    snapshot = compute_community_snapshot(window_minutes=WINDOW_MINUTES)
    adjusted = False
    new_e = current_e

    # Automatische Energy-Anpassung nur bei ausreichend Signalen
    if snapshot.total_votes >= MIN_VOTES_FOR_ADJUST and snapshot.suggested_energy is not None:
        suggested = snapshot.suggested_energy
        if suggested != current_e:
            step = max(-MAX_ENERGY_STEP, min(MAX_ENERGY_STEP, suggested - current_e))
            new_e = energy.clamp_energy(current_e + step)
            if new_e != current_e:
                db.set_energy(new_e)
                adjusted = True
                log.info(
                    "Energy auto-adjusted %s → %s (pressure=%.2f, votes=%s)",
                    current_e, new_e, snapshot.energy_pressure, snapshot.total_votes,
                )

    # Menschliche Antwort bauen
    msg = _build_reply(vote_type, adjusted, current_e, new_e, snapshot)

    return VoteResult(
        accepted=True,
        message=msg,
        vote_type=vote_type,
        user_id=user_id,
        current_energy=current_e,
        current_genre=current_g,
        energy_adjusted=adjusted,
        new_energy=new_e if adjusted else None,
        community_summary=asdict(snapshot),
    )


def compute_community_snapshot(window_minutes: int = WINDOW_MINUTES) -> CommunitySnapshot:
    """Aggregiert die letzten Votes im Zeitfenster."""
    cutoff = _utc_now() - timedelta(minutes=window_minutes)
    with db.get_conn() as con:
        rows = con.execute(
            """
            SELECT vote, genre_at_vote, created_at
            FROM votes
            WHERE created_at >= ?
            ORDER BY created_at DESC
            """,
            (_iso(cutoff),),
        ).fetchall()

    counts = {"up": 0, "down": 0, "more_energy": 0, "less_energy": 0}
    genre_counts: dict[str, int] = {}
    hour_counts: dict[int, int] = {}

    for r in rows:
        v = r["vote"]
        if v in counts:
            counts[v] += 1
        g = r["genre_at_vote"]
        if g:
            genre_counts[g] = genre_counts.get(g, 0) + 1
        try:
            hour = datetime.fromisoformat(r["created_at"]).hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        except Exception:
            pass

    total = sum(counts.values())
    more = counts["more_energy"]
    less = counts["less_energy"]
    up = counts["up"]
    down = counts["down"]

    # Energy-Pressure: -1 … +1
    energy_total = more + less
    if energy_total > 0:
        pressure = (more - less) / energy_total
    else:
        pressure = 0.0

    # Track-Score
    track_total = up + down
    track_score = (up / track_total) if track_total > 0 else 0.5

    dominant = None
    if genre_counts:
        dominant = max(genre_counts, key=genre_counts.get)

    peak_hour = None
    if hour_counts:
        peak_hour = max(hour_counts, key=hour_counts.get)

    # Suggested Energy
    current = db.get_energy()
    suggested = None
    if energy_total >= MIN_VOTES_FOR_ADJUST:
        if pressure >= ENERGY_PRESSURE_THRESHOLD and (more - less) >= ENERGY_PRESSURE_MARGIN:
            suggested = energy.clamp_energy(current + 1)
        elif pressure <= -ENERGY_PRESSURE_THRESHOLD and (less - more) >= ENERGY_PRESSURE_MARGIN:
            suggested = energy.clamp_energy(current - 1)

    return CommunitySnapshot(
        window_minutes=window_minutes,
        total_votes=total,
        up=up,
        down=down,
        more_energy=more,
        less_energy=less,
        energy_pressure=round(pressure, 3),
        track_score=round(track_score, 3),
        dominant_genre=dominant,
        suggested_energy=suggested,
        peak_hour_utc=peak_hour,
        generated_at=_iso(_utc_now()),
    )


def build_community_profile(limit: int = 200) -> dict[str, Any]:
    """
    Längerfristiges Community-Profil (für Learning-Loop und Overlay).
    Schreibt nichts – nur Analyse.
    """
    with db.get_conn() as con:
        rows = con.execute(
            """
            SELECT vote, energy_at_vote, genre_at_vote, created_at
            FROM votes
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    if not rows:
        return {
            "votes_analyzed": 0,
            "message": "Noch zu wenige Votes für ein Profil.",
            "generated_at": _iso(_utc_now()),
        }

    energy_pref: dict[int, int] = {}
    genre_pref: dict[str, int] = {}
    vote_type_counts: dict[str, int] = {}
    hourly: dict[int, int] = {}

    for r in rows:
        e = r["energy_at_vote"]
        energy_pref[e] = energy_pref.get(e, 0) + 1
        g = r["genre_at_vote"] or "unknown"
        genre_pref[g] = genre_pref.get(g, 0) + 1
        vote_type_counts[r["vote"]] = vote_type_counts.get(r["vote"], 0) + 1
        try:
            h = datetime.fromisoformat(r["created_at"]).hour
            hourly[h] = hourly.get(h, 0) + 1
        except Exception:
            pass

    preferred_energy = max(energy_pref, key=energy_pref.get) if energy_pref else None
    preferred_genre = max(genre_pref, key=genre_pref.get) if genre_pref else None
    peak_hours = sorted(hourly.items(), key=lambda x: -x[1])[:3]

    return {
        "votes_analyzed": len(rows),
        "preferred_energy": preferred_energy,
        "preferred_genre": preferred_genre,
        "genre_distribution": dict(sorted(genre_pref.items(), key=lambda x: -x[1])),
        "energy_distribution": dict(sorted(energy_pref.items())),
        "vote_type_counts": vote_type_counts,
        "peak_hours_utc": [{"hour": h, "count": c} for h, c in peak_hours],
        "generated_at": _iso(_utc_now()),
    }


def _build_reply(
    vote_type: str,
    adjusted: bool,
    old_e: int,
    new_e: int,
    snap: CommunitySnapshot,
) -> str:
    """Freundliche, psychedelische, aber knappe Antwort."""
    icons = {
        "up": "▲",
        "down": "▼",
        "more_energy": "⚡",
        "less_energy": "🌙",
    }
    icon = icons.get(vote_type, "•")

    base = {
        "up": f"{icon} Upvote registriert",
        "down": f"{icon} Downvote registriert",
        "more_energy": f"{icon} Mehr Energy-Druck registriert",
        "less_energy": f"{icon} Weniger Energy-Druck registriert",
    }.get(vote_type, "Vote registriert")

    parts = [base]

    if snap.total_votes > 0:
        parts.append(
            f"Community ({snap.window_minutes} min): "
            f"▲{snap.up} ▼{snap.down}  ⚡{snap.more_energy} 🌙{snap.less_energy}"
        )

    if adjusted:
        mood = energy.energy_to_mood(new_e)
        parts.append(f"→ Energy angepasst: *{old_e}* → *{new_e}/10* ({mood})")
    elif snap.suggested_energy and snap.suggested_energy != old_e:
        parts.append(
            f"Community tendiert zu Energy {snap.suggested_energy}/10 "
            f"(noch {MIN_VOTES_FOR_ADJUST - snap.total_votes} Signale nötig)"
        )

    return "\n".join(parts)


def export_profile_to_reports() -> Path:
    """Schreibt aktuelles Community-Profil nach reports/ (für Learning-Loop)."""
    from pathlib import Path
    from app.config import BASE_DIR  # erwartet BASE_DIR in config

    profile = build_community_profile()
    reports = Path(BASE_DIR) / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    ts = _utc_now().strftime("%Y%m%d-%H%M%S")
    path = reports / f"community-profile-{ts}.json"
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    # auch als "latest"
    (reports / "community-profile-latest.json").write_text(
        json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path

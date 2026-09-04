# /srv/dj-stream/app/genres.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

from app.config import GENRES_JSON

# Ordered control list matching the Electronic Music Map (top → bottom, left → right)
GENRE_ORDER = [
    # Atmospheric
    "ambient", "drone", "chillout", "downtempo",
    # House
    "deep_house", "organic_house", "afro_house", "house",
    "progressive_house", "tech_house", "melodic_house",
    # Trance
    "progressive_trance", "trance", "uplifting_trance",
    # Techno
    "minimal_techno", "detroit_techno", "techno", "melodic_techno",
    "hard_techno", "schranz",
    # Psy
    "goa_trance", "psytrance", "full_on", "darkpsy", "hi_tech_psy",
    # Bass
    "dubstep", "future_bass", "trap", "drum_and_bass", "neurofunk",
    # Hard Dance
    "hardstyle", "rawstyle", "hardcore", "frenchcore",
]


def load_genres() -> dict[str, Any]:
    if not GENRES_JSON.exists():
        return {}
    return json.loads(GENRES_JSON.read_text(encoding="utf-8"))


def get_genre_info(genre_id: str) -> Optional[dict[str, Any]]:
    data = load_genres()
    return data.get(genre_id)


def next_genre(current: str, delta: int = 1) -> str:
    try:
        idx = GENRE_ORDER.index(current)
    except ValueError:
        idx = GENRE_ORDER.index("psytrance")
    new_idx = max(0, min(len(GENRE_ORDER) - 1, idx + delta))
    return GENRE_ORDER[new_idx]


def genre_display(genre_id: str) -> str:
    info = get_genre_info(genre_id)
    if info:
        return info.get("display", genre_id)
    return genre_id


def validate_catalog() -> list[str]:
    """Return list of problems found in the genre catalog."""
    problems = []
    data = load_genres()
    for gid, info in data.items():
        for field in ("display", "parent", "energy", "bpm_min", "bpm_max"):
            if field not in info:
                problems.append(f"{gid}: missing {field}")
        if "energy" in info and not (1 <= info["energy"] <= 10):
            problems.append(f"{gid}: energy out of range")
    missing = set(data.keys()) - set(GENRE_ORDER)
    if missing:
        problems.append(f"Not in GENRE_ORDER: {sorted(missing)}")
    extra = set(GENRE_ORDER) - set(data.keys())
    if extra:
        problems.append(f"In GENRE_ORDER but not in JSON: {sorted(extra)}")
    return problems

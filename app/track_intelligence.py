# /srv/dj-stream/app/track_intelligence.py
"""
Phase 5 – Track Intelligence
Nutzt mixxx-analyzer (falls installiert) + Fallback über mutagen/ffprobe.

Ziel:
- BPM, Key, Camelot, LUFS, Intro/Outro
- Energy-Schätzung (1–10) aus BPM + Genre-Hints
- Mood-Heuristik
- Persistenz in SQLite-Tabelle `tracks`
- Batch-Scan eines Track-Verzeichnisses
- Sichere, idempotente Updates

Dependencies (optional):
  pip install mixxx-analyzer mutagen
  # ffprobe kommt mit FFmpeg
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app import db, genres, energy
from app.config import ROOT

log = logging.getLogger("acid-prophet.track_intelligence")

# Standard-Track-Pfad (anpassbar via Env oder Argument)
DEFAULT_TRACK_DIR = Path(ROOT) / "tracks"
if not DEFAULT_TRACK_DIR.exists():
    DEFAULT_TRACK_DIR = Path("/srv/data/dj-tracks")

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".aiff"}


@dataclass
class TrackMeta:
    path: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    bpm: Optional[float] = None
    musical_key: Optional[str] = None
    camelot: Optional[str] = None
    loudness_lufs: Optional[float] = None
    energy: Optional[int] = None
    energy_confidence: float = 0.0
    mood: Optional[str] = None
    genre: Optional[str] = None
    intro_secs: Optional[float] = None
    outro_secs: Optional[float] = None
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "unknown"  # mixxx | mutagen | ffprobe | heuristic


# ── Analyzer-Backends ────────────────────────────────────────────────────────

def _has_mixxx_analyzer() -> bool:
    try:
        import mixxx_analyzer  # noqa: F401
        return True
    except ImportError:
        return False


def analyze_with_mixxx(path: Path) -> Optional[TrackMeta]:
    """Primäres Backend – mixxx-analyzer (QueenMary BPM/Key + ebur128)."""
    try:
        from mixxx_analyzer import analyze
        r = analyze(str(path))
        meta = TrackMeta(
            path=str(path),
            bpm=r.bpm,
            musical_key=r.key,
            camelot=r.camelot,
            loudness_lufs=r.lufs,
            intro_secs=getattr(r, "intro_secs", None),
            outro_secs=getattr(r, "outro_secs", None),
            source="mixxx",
        )
        # Tags aus Datei nachladen
        tags = _read_tags_mutagen(path)
        if tags:
            meta.title = tags.get("title") or meta.title
            meta.artist = tags.get("artist") or meta.artist
            meta.album = tags.get("album") or meta.album
            meta.genre = tags.get("genre") or meta.genre
        return meta
    except Exception as e:
        log.warning("mixxx-analyzer failed for %s: %s", path, e)
        return None


def _read_tags_mutagen(path: Path) -> dict[str, Any]:
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(path)
        if f is None:
            return {}
        tags = {}
        # Einheitliche Felder
        mapping = {
            "title": ["TIT2", "title", "\xa9nam"],
            "artist": ["TPE1", "artist", "\xa9ART"],
            "album": ["TALB", "album", "\xa9alb"],
            "genre": ["TCON", "genre", "\xa9gen"],
            "bpm": ["TBPM", "bpm"],
        }
        for key, candidates in mapping.items():
            for c in candidates:
                if c in f:
                    val = f[c]
                    if isinstance(val, list):
                        val = val[0]
                    tags[key] = str(val)
                    break
        return tags
    except Exception:
        return {}


def analyze_with_ffprobe(path: Path) -> Optional[TrackMeta]:
    """Fallback: nur Tags + Dauer, kein BPM/Key."""
    if not shutil.which("ffprobe"):
        return None
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ]
        out = subprocess.check_output(cmd, text=True, timeout=30)
        data = json.loads(out)
        fmt = data.get("format", {})
        tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
        meta = TrackMeta(
            path=str(path),
            title=tags.get("title"),
            artist=tags.get("artist"),
            album=tags.get("album"),
            genre=tags.get("genre"),
            source="ffprobe",
        )
        if "TBPM" in tags or "bpm" in tags:
            try:
                meta.bpm = float(tags.get("bpm") or tags.get("tbpm"))
            except (TypeError, ValueError):
                pass
        return meta
    except Exception as e:
        log.warning("ffprobe failed for %s: %s", path, e)
        return None


def analyze_file(path: Path) -> TrackMeta:
    """Wählt bestes verfügbares Backend."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    meta = None
    if _has_mixxx_analyzer():
        meta = analyze_with_mixxx(path)
    if meta is None:
        meta = analyze_with_ffprobe(path)
    if meta is None:
        tags = _read_tags_mutagen(path)
        meta = TrackMeta(
            path=str(path),
            title=tags.get("title"),
            artist=tags.get("artist"),
            album=tags.get("album"),
            genre=tags.get("genre"),
            source="mutagen",
        )
        if tags.get("bpm"):
            try:
                meta.bpm = float(tags["bpm"])
            except ValueError:
                pass

    # Energy + Mood heuristisch anreichern
    enrich_energy_mood(meta)
    return meta


# ── Energy / Mood Heuristik ──────────────────────────────────────────────────

def bpm_to_energy_band(bpm: Optional[float]) -> tuple[int, float]:
    """
    Grobe Energy-Schätzung aus BPM.
    Returns (energy 1-10, confidence 0-1)
    """
    if bpm is None or bpm <= 0:
        return 7, 0.2
    # Typische Electronic-Bereiche
    bands = [
        (0, 90, 1, 0.7),
        (90, 110, 2, 0.75),
        (110, 118, 3, 0.7),
        (118, 124, 4, 0.8),
        (124, 128, 5, 0.8),
        (128, 135, 6, 0.75),
        (135, 142, 7, 0.8),
        (142, 150, 8, 0.85),
        (150, 160, 9, 0.85),
        (160, 300, 10, 0.9),
    ]
    for lo, hi, e, conf in bands:
        if lo <= bpm < hi:
            return e, conf
    return 7, 0.3


def enrich_energy_mood(meta: TrackMeta) -> None:
    """Schreibt energy, energy_confidence, mood, ggf. genre aus Katalog."""
    e_from_bpm, conf = bpm_to_energy_band(meta.bpm)

    # Genre aus Katalog matchen (fuzzy)
    catalog_genre = None
    catalog_energy = None
    if meta.genre:
        g_lower = meta.genre.lower().replace(" ", "_").replace("-", "_")
        info = genres.get_genre_info(g_lower)
        if info:
            catalog_genre = g_lower
            catalog_energy = info.get("energy")
        else:
            # Teilstring-Match
            for gid in genres.GENRE_ORDER:
                if gid in g_lower or g_lower in gid:
                    catalog_genre = gid
                    info = genres.get_genre_info(gid)
                    if info:
                        catalog_energy = info.get("energy")
                    break

    if catalog_energy is not None:
        # Katalog + BPM mischen
        meta.energy = int(round((catalog_energy + e_from_bpm) / 2))
        meta.energy_confidence = min(0.95, conf + 0.15)
        meta.genre = catalog_genre or meta.genre
    else:
        meta.energy = e_from_bpm
        meta.energy_confidence = conf

    meta.energy = energy.clamp_energy(meta.energy or 7)

    # Mood aus Energy-Map
    meta.mood = energy.energy_to_mood(meta.energy)


# ── Persistenz ───────────────────────────────────────────────────────────────

def save_to_db(meta: TrackMeta) -> None:
    """Upsert in tracks-Tabelle."""
    with db.get_conn() as con:
        con.execute(
            """
            INSERT INTO tracks(
                path, title, artist, album, bpm, musical_key, camelot,
                loudness_lufs, energy, energy_confidence, mood, genre, analyzed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
                title=excluded.title,
                artist=excluded.artist,
                album=excluded.album,
                bpm=excluded.bpm,
                musical_key=excluded.musical_key,
                camelot=excluded.camelot,
                loudness_lufs=excluded.loudness_lufs,
                energy=excluded.energy,
                energy_confidence=excluded.energy_confidence,
                mood=excluded.mood,
                genre=excluded.genre,
                analyzed_at=excluded.analyzed_at
            """,
            (
                meta.path, meta.title, meta.artist, meta.album,
                meta.bpm, meta.musical_key, meta.camelot,
                meta.loudness_lufs, meta.energy, meta.energy_confidence,
                meta.mood, meta.genre, meta.analyzed_at,
            ),
        )


def get_track(path: str) -> Optional[dict[str, Any]]:
    with db.get_conn() as con:
        row = con.execute("SELECT * FROM tracks WHERE path = ?", (path,)).fetchone()
        return dict(row) if row else None


def list_tracks(limit: int = 100) -> list[dict[str, Any]]:
    with db.get_conn() as con:
        rows = con.execute(
            "SELECT * FROM tracks ORDER BY analyzed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Batch ────────────────────────────────────────────────────────────────────

def scan_directory(
    directory: Path | str = DEFAULT_TRACK_DIR,
    force: bool = False,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """
    Scannt Verzeichnis, analysiert fehlende oder force-neu.
    Returns Summary.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return {"ok": False, "error": f"Not a directory: {directory}"}

    files = sorted(
        p for p in directory.rglob("*")
        if p.suffix.lower() in AUDIO_EXTENSIONS and p.is_file()
    )
    if limit:
        files = files[:limit]

    analyzed = 0
    skipped = 0
    errors = 0
    results = []

    for path in files:
        existing = get_track(str(path))
        if existing and not force:
            skipped += 1
            continue
        try:
            meta = analyze_file(path)
            save_to_db(meta)
            analyzed += 1
            results.append({
                "path": meta.path,
                "bpm": meta.bpm,
                "key": meta.musical_key,
                "camelot": meta.camelot,
                "energy": meta.energy,
                "source": meta.source,
            })
            log.info("Analyzed %s → BPM=%s Key=%s Energy=%s", path.name, meta.bpm, meta.camelot, meta.energy)
        except Exception as e:
            errors += 1
            log.error("Failed %s: %s", path, e)

    return {
        "ok": True,
        "directory": str(directory),
        "total_files": len(files),
        "analyzed": analyzed,
        "skipped": skipped,
        "errors": errors,
        "sample": results[:10],
        "mixxx_available": _has_mixxx_analyzer(),
    }


def tracks_matching_energy(energy_level: int, limit: int = 20) -> list[dict[str, Any]]:
    """Für Playlist-Logik: Tracks in der Nähe der gewünschten Energy."""
    with db.get_conn() as con:
        rows = con.execute(
            """
            SELECT * FROM tracks
            WHERE energy BETWEEN ? AND ?
            ORDER BY ABS(energy - ?), analyzed_at DESC
            LIMIT ?
            """,
            (max(1, energy_level - 1), min(10, energy_level + 1), energy_level, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def tracks_matching_genre(genre_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with db.get_conn() as con:
        rows = con.execute(
            """
            SELECT * FROM tracks
            WHERE genre = ? OR genre LIKE ?
            ORDER BY analyzed_at DESC
            LIMIT ?
            """,
            (genre_id, f"%{genre_id}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

# /srv/dj-stream/app/config.py
from __future__ import annotations
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):  # type: ignore
        pass

ROOT = Path("/srv/dj-stream")
load_dotenv(ROOT / ".env")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DB_PATH = Path(os.getenv("DJ_STREAM_DB", str(ROOT / "data" / "acid_prophet.db")))
TIMEZONE = os.getenv("DJ_STREAM_TIMEZONE", "Europe/Berlin")
FFPLAYOUT_API = os.getenv("FFPLAYOUT_API", "http://127.0.0.1:8787")
FFPLAYOUT_TOKEN = os.getenv("FFPLAYOUT_TOKEN", "")
FFPLAYOUT_CHANNEL = int(os.getenv("FFPLAYOUT_CHANNEL", "1"))

GENRES_JSON = ROOT / "config" / "genres.json"
COLORS_JSON = ROOT / "config" / "colors.json"
OVERLAY_TEXT = ROOT / "overlays" / "current.txt"
LOG_DIR = ROOT / "logs"

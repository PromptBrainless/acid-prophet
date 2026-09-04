#!/usr/bin/env bash
# scan-tracks.sh – Phase 5 Track Intelligence Batch
# Usage:
#   bash scripts/scan-tracks.sh [/path/to/tracks] [--force] [--limit N]

set -euo pipefail
cd /srv/dj-stream 2>/dev/null || cd "$(dirname "$0")/.."

DIR="${1:-/srv/data/dj-tracks}"
FORCE=""
LIMIT=""

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE="--force"; shift ;;
    --limit) LIMIT="--limit $2"; shift 2 ;;
    *) shift ;;
  esac
done

source .venv/bin/activate 2>/dev/null || true

python3 - << PY
from pathlib import Path
from app.track_intelligence import scan_directory, _has_mixxx_analyzer
import json

directory = Path("$DIR")
force = bool("$FORCE")
limit = None
limit_str = "$LIMIT".replace("--limit ", "").strip()
if limit_str:
    try:
        limit = int(limit_str)
    except ValueError:
        pass

print("mixxx-analyzer available:", _has_mixxx_analyzer())
result = scan_directory(directory, force=force, limit=limit)
print(json.dumps(result, indent=2, ensure_ascii=False))
PY

#!/usr/bin/env bash
set -euo pipefail
cd /srv/dj-stream
python3 learning/collect.py
python3 learning/analyze.py
python3 -m learning.analyze_voting || true
echo "Learning loop done $(date -u -Iseconds)"

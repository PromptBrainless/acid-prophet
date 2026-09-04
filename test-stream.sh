#!/usr/bin/env bash
set -euo pipefail
echo "=== Stream-Test ==="
echo "1. Icecast HTTP Header:"
curl -s --max-time 3 -I http://127.0.0.1:8000/stream | head -10
echo ""
echo "2. Erste 1KB Stream-Daten:"
curl -s --max-time 3 http://127.0.0.1:8000/stream | head -c 1024 | xxd | head -20
echo ""
echo "3. Aktiver Icecast-Prozess:"
ps aux | grep icecast_server | grep -v grep
echo ""
echo "4. Port-Listener:"
ss -ltnp | grep ':8000'

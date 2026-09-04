# Acid Prophet Changelog

## 2026-09-04 — Learning System Integration

Change:
- Self-improving loop: collect → analyze → pending → apply
- Deterministic pattern detection (energy bias, error spikes)
- Context compression (compress_context.py)
- systemd timer: acid-learning.timer (6h interval)
- Memory index: memory/index.json
- refine.py for manual lessons

Reason: Automatic learning without external API, restart-safe

Files:
- learning/{collect,analyze,refine,compress_context,apply_lesson}.py
- scripts/learning-loop.sh
- systemd/acid-learning.{service,timer}
- memory/{lessons,pending}/, memory/index.json
- LEARNING.md

Tests:
- collect.py writes signals JSON
- analyze.py writes pending lessons
- timer active (systemctl status)

Rollback:
- systemctl --user disable --now acid-learning.timer
- rm -rf /srv/dj-stream/learning /srv/dj-stream/memory

## 2026-09-04 — Phase 1 + Genre Map Integration

Change:
- SQLite state engine (app_state, votes, tracks, missions)
- /start, /status, /energy, /genre +1/-1
- /upvote, /downvote, /moreenergy, /lessenergy
- Complete Electronic Music Map as genres.json (BPM, Energy, Mood, Origin, Traits)
- Energy 1–10 color + mood mapping aligned with the map
- systemd service + health timer
- Health check script with auto-recovery

Reason: Execution brief Phase 0–2 + official Electronic Music Map

Files:
- app/config.py, db.py, energy.py, genres.py, bot.py
- config/genres.json
- scripts/bot-health.sh
- systemd/*

Tests:
- py_compile
- import + db smoke
- genre catalog validation

Rollback:
- Restore from backups/prechange-*.tar.gz

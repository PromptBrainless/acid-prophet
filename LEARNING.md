# LEARNING SYSTEM — Acid Prophet

Automatische Lernschleife ohne manuellen Eingriff.
Collect → Analyze → Pending → Apply → Compress.

## Architektur

Trigger → Collector → Analyzer → Learner → Validator → Applicator

## Verzeichnisstruktur

```
memory/
├── lessons/      # freigegebene Lessons
├── pending/      # wartet auf Freigabe
└── index.json    # schnelle Übersicht
learning/
├── collect.py
├── analyze.py
├── refine.py
├── compress_context.py
└── apply_lesson.py
scripts/
└── learning-loop.sh
systemd/
├── acid-learning.service
└── acid-learning.timer
```

## Trigger

- Timer: 6h (OnBootSec=10min, OnUnitActiveSec=6h)
- /refine → refine.py
- Health FAIL → collect.py
- 50 Votes → analyze.py

## Kontext-Kompression

Stufen:
0 Normal
1 > 40% Tool-Outputs kürzen
2 > 60% Conversation summary
3 > 80% Goals + Tasks + letzte 6 Turns + Memory-Index

Aufruf: python3 learning/compress_context.py

## Sicherheit

- Learning-Scripts schreiben nie Secrets
- Keine Änderung an .env
- Lessons nur in pending/, Apply nur manuell

# MEMORY.md — Acid Prophet Memory Rules

## Retrieval-Regeln
1. Immer laden: `memory/index.json` (klein) + aktuelle `app_state` aus SQLite
2. Bei Bedarf: passende Lessons nach Keyword / Source / Tag suchen
3. Nie: ganze `episodes/` oder Roh-Logs in den Prompt laden
4. Optional später: Embeddings nur für Lesson-Suche, nicht für State

## Schreib-Regeln
| Speicher | Wer schreibt | Wann |
|----------|--------------|------|
| `pending/` | KI oder `analyze.py` | Nach Collect/Refine |
| `lessons/` | nur `apply_lesson.py` | Nach Approve |
| `index.json` | nur `apply_lesson.py` oder Curator-Script | Nach Apply/Archive |
| SQLite State | Bot / Services | Laufzeit |
| `episodes/` | `compress_context.py` oder `/refine` | Nach Session oder `/compress` |

## Vergessen / Aufräumen
- Lessons mit Confidence < 0.4 nach 30 Tagen → `memory/archived/`
- Doppelte Regeln mergen (Curator-Script)
- `index.json` nie > ~50 aktive Lessons ohne Review

## Kontext-Kompression
- Aufruf: `python3 /srv/dj-stream/learning/compress_context.py`
- Stufe 0: Normal
- Stufe 1: Tool-Outputs kürzen
- Stufe 2: Conversation-Summary
- Stufe 3: Goals + Tasks + Lessons + letzte 6 Turns

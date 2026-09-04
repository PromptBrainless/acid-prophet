# Phase 4 – Community Voting (vollständig)

**Datum:** 2026-09-04  
**Status:** Produktionsreif, drop-in ready  
**Einsatzgebiet:** Der nächste kritische Baustein nach Energy + Genre

---

## Warum dieses Einsatzgebiet?

| Priorität | Begründung |
|-----------|------------|
| 1. Stabilität | Votes waren bereits in der DB – nur die Logik fehlte |
| 2. Community-Feeling | Ohne Feedback und Aggregation fühlt sich Voting tot an |
| 3. Learning-Loop | Voting-Daten sind das wichtigste Signal für den Analyzer |
| 4. Energy-Autonomie | Der Bot kann jetzt *selbst* auf Crowd-Druck reagieren |
| 5. Roadmap | MASTER_EXECUTION.md Phase 6 (Community Voting) war als nächstes markiert |

Ohne funktionierendes Voting bleiben Track-Intelligence und YouTube-Overlay halbblind.

---

## Was wurde geliefert

### 1. `app/voting.py` – komplette Voting-Engine

- **Rate-Limiting** (8 Votes / 120 s pro User) → Anti-Spam
- **Zeitfenster-Aggregation** (Standard 15 min)
- **Energy-Pressure-Berechnung** (−1.0 … +1.0)
- **Automatische Energy-Anpassung** bei klarem Mehrheits-Druck (≥ 65 % + Mindest-Differenz)
- **Maximaler Schritt ±1** pro Anpassung (kein Springen)
- **Community-Snapshot** + **Langzeit-Profil**
- **Export** nach `reports/community-profile-*.json`
- Deterministisch, keine KI im Hot-Path, keine Secrets

### 2. `app/bot_voting_handlers.py` – fertige Telegram-Handler

- `/upvote`, `/downvote`, `/moreenergy`, `/lessenergy`
- Neuer Command: `/community` → Live-Snapshot + Langzeit-Präferenzen
- Freundliche, knappe, psychedelische Antworten mit Live-Zahlen

### 3. `learning/analyze_voting.py` – Learning-Integration

- Analysiert Energy-Bias, Track-Love/Hate, Genre-Präferenz, Peak-Times
- Schreibt strukturierte Signale nach `reports/voting-signals-*.json`
- Kann direkt in `scripts/learning-loop.sh` eingebunden werden

### 4. Konfigurations-Konstanten (oben in `voting.py`)

Alle Schwellen sind klar benannt und leicht anpassbar:

```python
MIN_VOTES_FOR_ADJUST = 5
WINDOW_MINUTES = 15
RATE_LIMIT_COUNT = 8
RATE_LIMIT_SECONDS = 120
ENERGY_PRESSURE_THRESHOLD = 0.65
ENERGY_PRESSURE_MARGIN = 2
MAX_ENERGY_STEP = 1
```

---

## Integration in 4 Schritten

### Schritt 1 – Dateien kopieren

```bash
cd /srv/dj-stream

# Backup
tar -czf backups/pre-phase4-$(date +%Y%m%d-%H%M).tar.gz app/ learning/ scripts/

# Neue Dateien
cp /path/to/improvements/app/voting.py          app/
cp /path/to/improvements/app/bot_voting_handlers.py app/
cp /path/to/improvements/learning/analyze_voting.py learning/
```

### Schritt 2 – `bot.py` anpassen

Alte Handler ersetzen (oder die neuen importieren):

```python
# oben
from app import voting
from app.bot_voting_handlers import upvote, downvote, moreenergy, lessenergy, community

# in main()
app.add_handler(CommandHandler("upvote", upvote))
app.add_handler(CommandHandler("downvote", downvote))
app.add_handler(CommandHandler("moreenergy", moreenergy))
app.add_handler(CommandHandler("lessenergy", lessenergy))
app.add_handler(CommandHandler("community", community))   # NEU
```

Die alten `upvote`/`downvote`/… Funktionen in `bot.py` können gelöscht werden.

### Schritt 3 – Learning-Loop erweitern

In `scripts/learning-loop.sh` ergänzen:

```bash
# nach collect.py / analyze.py
python3 -m learning.analyze_voting || true
```

### Schritt 4 – Testen & Restart

```bash
# Syntax-Check
python3 -c "from app import voting; print('OK')"

# Service neu starten
systemctl --user restart acid-prophet.service
journalctl --user -u acid-prophet.service -f
```

Telegram-Tests:
1. `/upvote` → sollte "▲ Upvote registriert" + Community-Zahlen zeigen
2. Mehrfach schnell voten → Rate-Limit-Meldung
3. 5+ `moreenergy` in kurzer Zeit → Energy steigt um 1
4. `/community` → Snapshot + Präferenzen

---

## Sicherheits- & Design-Prinzipien (eingehalten)

| Prinzip | Umsetzung |
|---------|-----------|
| Keine Secrets | Voting schreibt nur in `votes`-Tabelle und `reports/` |
| Deterministisch | Alle Schwellen hardcodiert, keine LLM-Entscheidung im Vote-Pfad |
| Idempotent | Mehrfaches Voten desselben Users ist erlaubt, aber rate-limited |
| Rollback | Alte Handler bleiben im Git; Backup vor dem Copy |
| AGENTS.md | KI schreibt weiterhin nur nach `memory/pending/` |
| Stabilität vor Features | Energy-Schritt max ±1, Mindest-Votes erforderlich |

---

## Erwartetes Verhalten

| Situation | Reaktion |
|-----------|----------|
| Einzelner Upvote | Nur Bestätigung + aktuelle Zahlen |
| 5+ more_energy mit >65 % Mehrheit | Energy +1, Mood-Anzeige |
| Spam (9 Votes in 2 min) | Rate-Limit-Meldung, kein DB-Eintrag |
| Starke Downvotes | Track-Score sinkt → späteres Skip-Signal |
| `/community` | Live-Fenster + Langzeit-Präferenz |

---

## Nächste sinnvolle Schritte (nach Phase 4)

1. **Track-Path an Votes binden** (sobald Track-Intelligence läuft)
2. **Overlay** liest `community-profile-latest.json` und `voting-signals-latest.json`
3. **Genre-Auto-Shift** analog zur Energy-Anpassung (optional, vorsichtig)
4. **Mission-System** an Vote-Counts koppeln (Boss-Event etc.)

---

## Dateien in diesem Paket

```
acid-prophet-improvements/
├── app/
│   ├── voting.py                 # Kern-Engine
│   └── bot_voting_handlers.py    # Telegram-Handler
├── learning/
│   └── analyze_voting.py         # Learning-Integration
├── docs/
│   └── PHASE4_VOTING_COMPLETE.md # Diese Datei
└── scripts/
    └── (optional) patch-bot.sh
```

---

**Fazit:** Phase 4 ist jetzt vollständig, sicher und bereit zum Einspielen.  
Der Bot hört der Crowd endlich zu und reagiert kontrolliert.  
Stabilität und Learning-Loop profitieren sofort.

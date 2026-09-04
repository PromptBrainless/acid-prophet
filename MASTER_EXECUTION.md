# ACID PROPHET LIVE
## MASTER EXECUTION FILE
### Autonome Projektsteuerung für Agenten, Entwickler und KI-Systeme

Version: 1.0
Priorität: KRITISCH
Ziel: Maximale Eigenständigkeit des Agenten bei minimalem menschlichem Eingriff

---

# PROJEKTZIEL

Entwicklung eines vollständig autonomen 24/7 Psytrance-/Electronic-Music-Streaming-Systems mit:

- Telegram Bot
- Energy-System
- Mood-System
- Genre-Hierarchie
- Voting-System
- KI-Persönlichkeit
- YouTube Livestream
- Visual Overlay
- Metadaten-System
- Community Interaktion

Der Agent soll selbstständig:
- analysieren
- priorisieren
- recherchieren
- dokumentieren
- validieren
- implementieren
- testen
- Fehler beheben

ohne Rückfragen, solange keine kritische Entscheidung erforderlich ist.

---

# AGENTENREGELN

## Regel 1

Immer zuerst prüfen:

- Läuft der Bot?
- Ist der Token gültig?
- Sind Services aktiv?
- Existieren notwendige Dateien?

Wenn Nein:

STOP.

Sofort Fehlerbehebung priorisieren.

---

## Regel 2

Keine neuen Features entwickeln solange:

- /start nicht funktioniert
- Telegram API Fehler bestehen
- systemd Service instabil ist

---

## Regel 3

Jede Änderung dokumentieren in:

/srv/dj-stream/CHANGELOG.md

Format:

Datum
Änderung
Grund
Auswirkung

---

## Regel 4

Vor jeder Implementierung:

1. Bestehenden Code analysieren
2. Architektur dokumentieren
3. Abhängigkeiten prüfen
4. Sicherheitsrisiken bewerten
5. Erst dann implementieren

---

# PHASE 1
## KRITISCHE BLOCKER

Priorität = MAXIMUM

---

### Aufgabe 1

Token Persistenz

Ziel:

Telegram Token darf niemals verloren gehen.

Prüfen:

- systemd Environment
- .env Datei
- Rechte
- Ownership
- Restart Verhalten

Liefern:

- Fehlerursache
- Lösung
- Testprotokoll

Erfolgskriterium:

5 Neustarts überstehen.

---

### Aufgabe 2

/start Reparatur

Ziel:

Bot antwortet zuverlässig.

Prüfen:

- Polling
- Handler
- Telegram API
- Logging
- Token

Erfolgskriterium:

10 erfolgreiche Testaufrufe.

---

### Aufgabe 3

Monitoring

Anlegen:

bot-health.sh

Prüft:

- Prozess läuft
- Telegram erreichbar
- Speicherverbrauch
- CPU Last

Bei Fehler:

Auto-Restart.

---

# PHASE 2
## ENERGY ENGINE

Abhängigkeit:

Bot läuft stabil.

---

### /energy <1-10>

Implementieren:

1 = Ambient
2 = Chillout
3 = Downtempo
4 = Deep House
5 = House
6 = Progressive House
7 = Trance
8 = Techno
9 = Psytrance
10 = Hard Dance

---

Speichern:

current_energy.json

Beispiel:

{
 "energy":8,
 "updated":"timestamp"
}

---

### Agentenrecherche

Für jedes Genre erfassen:

- BPM
- Energy
- Stimmung
- Farbcode
- Untergenre
- Herkunft
- Beschreibung

Ausgabe:

genres.json

---

# PHASE 3
## FARBSYSTEM

Farbmatrix

1 #001F3F
2 #006D77
3 #2A9D8F
4 #52B788
5 #F4D35E
6 #F4A261
7 #E76F51
8 #D62828
9 #9D4EDD
10 #FFFFFF

---

Agent soll prüfen:

- Lesbarkeit
- Kontrast
- Accessibility
- Streamtauglichkeit

---

# PHASE 4
## GENRE HIERARCHY

Befehl:

/genre +1
/genre -1

Logik:

Ambient
→ Chillout
→ Downtempo
→ Deep House
→ House
→ Progressive House
→ Trance
→ Techno
→ Psytrance
→ Hard Dance

Automatisch:

Energy mitführen.

---

# PHASE 5
## TRACK INTELLIGENCE

Agent soll recherchieren:

Für jeden Track:

- BPM
- Camelot
- Genre
- Energy
- Mood
- Tonart
- Künstler
- Label

Speichern:

track_metadata.json

---

Agent bewertet:

Danceability
Intensity
Psychedelic Factor
Darkness Factor

Skala:

1-10

---

# PHASE 6
## COMMUNITY VOTING

Befehle:

/upvote
/downvote

Zusätzlich:

/moreenergy
/lessenergy

---

Agent analysiert:

letzte 50 Votes

Erkennt:

- Trends
- Peak Times
- Genre Präferenzen

Erstellt:

community_profile.json

---

# PHASE 7
## KI PERSÖNLICHKEIT

Name:

Acid Prophet

Charakter:

- Psychedelisch
- Freundlich
- Mystisch
- Humorvoll
- Nicht toxisch

---

Antworten basieren auf:

- aktuellem Genre
- aktueller Energy
- Uhrzeit
- Community Stimmung

---

# PHASE 8
## YOUTUBE OVERLAY

Vorbereitung bereits ohne API Key.

Agent entwickelt:

overlay.py

Anzeige:

- Track
- BPM
- Energy
- Genre
- Mood
- Viewer Votes

---

Farben automatisch aus Energy System.

---

# PHASE 9
## 24/7 STREAM

systemd Service

Anforderungen:
- Auto Restart
- Crash Recovery
- Logging
- Monitoring

---

Agent erstellt:

stream.service

---

# PHASE 10
## SELBSTANALYSE

Alle 60 Minuten:

Agent bewertet:

- Fehler
- Performance
- Nutzeraktivität
- Speicherverbrauch
- Abstürze

Generiert:

status_report.md

---

# AUTONOME RECHERCHEAUFGABEN

Agent soll eigenständig recherchieren:

1. Best Practices Telegram Bots
2. FFmpeg Streaming
3. YouTube Live Anforderungen
4. Psytrance Genre Taxonomie
5. Voting-Systeme
6. Stream Automatisierung
7. Musik-Metadatenstandards
8. Community Engagement Systeme

Für jede Recherche:

- Quellen
- Bewertung
- Empfehlung
- Aufwand
- Risiko

Dokumentieren.

---

# ENTSCHEIDUNGSMATRIX

Bei Konflikten:

1. Stabilität
2. Sicherheit
3. Wartbarkeit
4. Automatisierung
5. Neue Features

immer in dieser Reihenfolge.

---

# DEFINITION OF DONE

Projekt gilt als fertig wenn:

✓ Telegram Bot stabil

✓ Token persistent

✓ Energy System aktiv

✓ Genre System aktiv

✓ Voting aktiv

✓ Track Intelligence aktiv

✓ Overlay aktiv

✓ YouTube Stream aktiv

✓ Monitoring aktiv

✓ Dokumentation vollständig

✓ Neustart ohne Datenverlust möglich

✓ 72 Stunden fehlerfreier Dauerbetrieb

ENDE DER MASTER EXECUTION FILE

# 🎧 The Crowd Controls The AI DJ
## Projektidee · Umsetzung · Architektur

---

## 1. Projektvision

### Kernkonzept
Ein 24/7 YouTube-Live-Stream, der von der Community gesteuert wird. Eine KI erstellt und spielt Musik live — die Zuschauer beeinflussen permanent das Geschehen über Chat, Abstimmungen und Kanal-Mitgliedschaften.

### Markenname
**"The Crowd Controls The AI DJ"**

### Positionierung
- Zwischen DJ-Set, Twitch-Plays-Pokémon und KI-Konzert
- Permanenter Livestream, niemals exakt gleich
- Community erlebt direkten Einfluss auf das Konzert
- Viral-Potenzial durch einzigartige Interaktion

---

## 2. Interaktionslevel

### Ebene 1: Direkter Einfluss auf die Musik
- **BPM-Steuerung**: Chat schreibt +BPM/-BPM, Abstimmung alle 60s, Bereich 80–180
- **Genre-Morphing**: Voting zwischen Techno, Trance, Drum & Bass, House, Synthwave, Hardstyle
- **Stimmungssystem**: Emojis verändern Harmonien/Sounds
  - 😈 = düster, 🚀 = euphorisch, 🌊 = chillig, 🔥 = aggressiv, 🌈 = verspielt

### Ebene 2: Crowd Events
- **Boss Event**: 500 Stimmen nötig, Musik wird episch, Tempo steigt
- **Chaos Mode**: Zufällige Sounds, Rhythmuswechsel, verrückte Drops
- **Time Travel**: Musik klingt wie 1980er/1990er/2000er/2050

### Ebene 3: KI als Persönlichkeit
- KI spricht mit dem Publikum
- Beispiel: "Ihr habt das Tempo schon wieder auf 165 BPM erhöht. Seid ihr komplett wahnsinnig?"
- Virtueller DJ-Charakter entsteht

### Ebene 4: Community gegen Community
- Teams: Team Melodie, Team Bass, Team Tempo, Team Chaos
- Live-Fraktionen kämpfen gegeneinander
- Punkte und Vorteile freischalten

### Ebene 5: KI-Musik als Spiel
- Missionen: "Halte BPM 10 Minuten über 150", "Perfekten Übergang erreichen", "Song mit 3 Genres bauen"
- Bei Erfolg: neue Sounds/Visuals

### Ebene 6: Monetarisierung
- Super Chats: Songnamen bestimmen, Instrument hinzufügen, Solopart aktivieren, KI-Stimme sprechen lassen
- Kein Pay-to-Win-Effekt

### Ebene 6b: KI-DJ-Planet (Premium-Idee)
- 24/7 Stream mit virtueller Welt
- Hohe BPM → Vulkanaktivität steigt
- Chillige Musik → Pflanzen wachsen
- Aggressive Musik → Gewitter
- Musik und Welt beeinflussen sich gegenseitig

---

## 3. Technische Architektur

### 3.1 Systemübersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    HOMESERVER (100.69.81.38)                 │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  Telegram Bot │◄────►│  Icecast     │                     │
│  │  (Python)     │      │  Server      │                     │
│  │  Port 8000    │      │  Port 8000   │                     │
│  └──────┬───────┘      └──────┬───────┘                     │
│         │                     │                              │
│         │                     ▼                              │
│         │              ┌──────────────┐                      │
│         │              │  FFmpeg      │                      │
│         │              │  Crossfade   │                      │
│         │              │  MP3 320kbps │                      │
│         │              └──────┬───────┘                      │
│         │                     │                              │
│         └────────────────────►│                              │
│                                ▼                              │
│                    ┌──────────────────┐                      │
│                    │  YouTube RTMP    │                      │
│                    │  (später)        │                      │
│                    └──────────────────┘                      │
│                                                              │
│  Tracks: /srv/data/dj-tracks/ (26 MP3s, Psytrance/Goa)     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Komponenten

#### A. Telegram Bot (`/srv/dj-stream/telegram_bot.py`)
**Status**: ✅ Laufend (PID 1558835, systemd user service)

**Features**:
- `/start` — Begrüßung mit KI-Persönlichkeit
- `/help` — Zeigt alle Commands
- `/status` — Aktueller Track + BPM + Genre + Stimmung
- `/vote` — Startet Voting mit 3 zufälligen Tracks (30s Laufzeit)
- `/bpm <80-180>` — Setzt BPM direkt
- `/bpm +10 / -10` — Erhöht/senkt BPM
- `/genre <name>` — Wechselt Genre (10 Genres)
- `/mood <name>` — Setzt Stimmung
- `/skip` — Überspringt aktuellen Track
- `/random` — Zeigt 3 Zufallstracks
- `/next` — Nächster Track
- `/search <begriff>` — Sucht in Track-Datenbank
- `/queue` — Zeigt Queue
- `/fav` — Favorisiert aktuellen Track
- `/favorites` — Zeigt Favoriten
- `/volume <0-100>` — Setzt Lautstärke
- `/crossfade <sekunden>` — Setzt Crossfade-Dauer
- `/sleep` — Pause/Play
- `/record` — Aufnahme

**Architektur**:
- Polling-basiert (`getUpdates` alle 30s)
- JSON-Logbuch: `/srv/dj-stream/logs/bot-decisions.json`
- Chat-ID gespeichert in `/srv/dj-stream/chat_id.txt`
- Queue in `/srv/dj-stream/queue.txt`
- Favoriten in `/srv/dj-stream/favorites.txt`

**Persönlichkeit**:
- Dynamische Sprüche je nach Aktion
- Zufällige Emojis/Flairs
- Deutsche Ansprache
- Reagiert auf Voting, BPM-Änderungen, Genre-Wechsel

#### B. Icecast Server (`/srv/dj-stream/icecast_server.py`)
**Status**: ✅ Funktionsfähig (Port 8000, HTTP 200)

**Konfiguration**:
- Genre: `Psytrance/Goa/Progressive`
- Bitrate: 320 kbps
- Track-Verzeichnis: `/srv/data/dj-tracks/` (26 MP3s)
- Stream-URL: `http://127.0.0.1:8000/stream`
- Mount: `/stream`
- Content-Type: `audio/mpeg`

**Features**:
- Automatisches Abspielen aller Tracks in Endlosschleife
- FFmpeg-basiert mit `acrossfade=d=5:c1=tri:c2=tri`
- Loudness-Normalisierung: `loudnorm=I=-16:TP=-1.5:LRA=11`
- Logging in `/srv/dj-stream/logs/icecast.log`

#### C. YouTube Integration (Vorbereitung)
**Status**: ⏳ Wartet auf Stream-Key (24h-Aktivierung)

**Dateien**:
- `/srv/dj-stream/dj-youtube-stream.sh` — FFmpeg-Pipeline (Icecast → YouTube RTMP)
- `/srv/dj-stream/youtube-background.jpg` — 1920x1080 Background für Stream
- `/home/jesus/dj-youtube.service` — systemd Service
- `/home/jesus/docker-compose-youtube.yml` — Docker Compose
- `/home/jesus/homeserver-youtube-live-24h.ics` — Kalendertermin
- Google Calendar Link für 04.09.2026 03:00 MESZ

**Stream-Befehl**:
```bash
ffmpeg -re -loop 1 -i /srv/dj-stream/youtube-background.jpg \
  -i http://localhost:8000/stream \
  -vf "scale=1920:1080" \
  -c:v libx264 -preset veryfast -b:v 3000k \
  -maxrate 3500k -bufsize 6000k \
  -pix_fmt yuv420p -g 60 -keyint_min 60 \
  -c:a aac -b:a 192k -ar 44100 \
  -f flv rtmp://a.rtmp.youtube.com/live2/STREAM_KEY
```

#### D. FFmpeg Pipeline
**Status**: ✅ Funktionsfähig

**Crossfade**:
- Dauer: 5 Sekunden
- Kurven: Triangular (`tri`)
- Lautheits-Normalisierung aktiv

**Prozesse**:
- Haupt-FFmpeg: Liest von Icecast, encodiert zu MP3 320kbps
- YouTube-FFmpeg: Liest von Icecast + Background-Image, streamt zu RTMP

---

## 4. Dateistruktur

```
/srv/dj-stream/
├── telegram_bot.py              # Hauptbot (454 Zeilen, ~16 KB)
├── icecast_server.py            # Icecast Server
├── run_bot.sh                   # Wrapper für Bot mit Env-Var
├── dj-youtube-stream.sh         # YouTube Stream-Skript
├── youtube-background.jpg       # 1920x1080 Background
├── chat_id.txt                  # Gespeicherte Telegram Chat-ID
├── queue.txt                    # Track-Queue
├── favorites.txt                # Favoriten
├── logs/
│   ├── bot-decisions.json       # Bot-Entscheidungslog
│   └── icecast.log              # Icecast-Log
└── (Symlink) /srv/dj-stream/tracks → /srv/data/dj-tracks/

/srv/data/dj-tracks/
└── 26 MP3-Dateien (Psytrance/Goa/Progressive, 320kbps)

/home/jesus/.config/systemd/user/
└── dj-bot.service               # systemd User Service

/home/jesus/
├── dj-youtube.service           # systemd System Service
├── docker-compose-youtube.yml   # Docker Compose
└── homeserver-youtube-live-24h.ics  # Kalendertermin
```

---

## 5. Konfiguration

### 5.1 Bot-Konfiguration
- **Token**: `8990811371:AAEVLBgIe4iN9SmBWA3gT3lNw4DCSzL0x0w` (in systemd-Umgebungsvariable)
- **Chat-ID**: `5385489929`
- **Service**: `dj-bot.service` (systemd user)
- **Auto-Restart**: Ja (RestartSec=10s)

### 5.2 Icecast-Konfiguration
- **Port**: 8000
- **Genre**: Psytrance/Goa/Progressive
- **Bitrate**: 320 kbps
- **Tracks**: 26 MP3s in `/srv/data/dj-tracks/`

### 5.3 FFmpeg-Einstellungen
- **Crossfade**: 5 Sekunden, triangular
- **Loudness**: I=-16, TP=-1.5, LRA=11
- **Audio-Codec**: libmp3lame, 320kbps, 44100Hz
- **Video** (YouTube): libx264, 3000k, 1920x1080, 60fps

### 5.4 Genres
1. Psytrance
2. Progressive
3. Techno
4. Trance
5. Drum & Bass
6. House
7. Synthwave
8. Hardstyle
9. Minimal
10. Darkpsy

---

## 6. Technischer Stack

| Komponente | Technologie | Status |
|---|---|---|
| Bot | Python 3.11, stdlib (urllib, json, subprocess) | ✅ Laufend |
| Streaming | FFmpeg 8.0.1, Icecast | ✅ Laufend |
| Audio-Format | MP3 320kbps | ✅ Fix |
| Metadata | ffprobe (subprocess) | ✅ Implementiert |
| Logging | JSON Lines (bot-decisions.json) | ✅ Aktiv |
| Service-Management | systemd (user + system) | ✅ Konfiguriert |
| Video-Encoding | libx264, veryfast preset | ✅ Bereit |
| Container | FFmpeg in Pipeline | ✅ Aktiv |

---

## 7. Inspirationsquellen

### Projekte
1. **kckDeepak/AI-DJ-Mixing-System** — BPM/Key-Analyse mit Librosa
2. **apollo-agents** — Agenten-basiert
3. **Deej-AI** — KI-DJ Konzept
4. **Liquidsoap** — Radio-Automation (verworfen: kein MP3-Encoder)
5. **AzuraCast** — Webradio-Management

### Top-Learnings
- Librosa für BPM/Key-Analyse
- EQ-Filterung während Crossfades
- JSON-Setlist-Export mit Voting-History
- Verbessertes Fallback-System
- Voting-basierte Track-Empfehlungen

---

## 8. Ausstehende Aufgaben

### Sofort (vor YouTube)
- [ ] YouTube Stream-Key eintragen
- [ ] YouTube Service starten
- [ ] Ersten Testlauf durchführen
- [ ] Bot `/start` Antwort verifizieren

### Kurzfristig (Phase 1)
- [ ] `/vote` Befehl testen mit echten Tracks
- [ ] BPM/Genre-Änderungen in FFmpeg-Pipeline integrieren
- [ ] Metadata-Anzeige optimieren
- [ ] Bot-Logbuch auswerten

### Mittelfristig (Phase 2)
- [ ] Chat-Commands (ohne Slash) implementieren
- [ ] Emoji-Stimmungsanalyse
- [ ] KI-Persönlichkeit Textmodul erweitern
- [ ] JSON-Entscheidungslog erweitern

### Langfristig (Phase 3+)
- [ ] YouTube 24/7 Betrieb
- [ ] Watchdog-Service
- [ ] Boss Event (500 Votes)
- [ ] Chaos Mode
- [ ] Time Travel (Dekaden-Filter)
- [ ] Community vs Community
- [ ] Super Chat Integration
- [ ] KI-DJ-Planet (virtuelle Welt)

---

## 9. Bekannte Einschränkungen

1. **Token-Problematik**: Shell maskiert `***` in Befehlen → Token nur über systemd-Umgebungsvariable
2. **Parallelbetrieb**: Nur 1 Bot-Instanz erlaubt (Telegram API 409 Conflict)
3. **Lokaler Stream**: Sekundär zu YouTube
4. **Kein lokales Backup**: Nur Skripte vorhanden
5. **Root-LV 91% voll**: Muss beobachtet werden
6. **Docker-Netzwerke**: 20+ Netzwerke, können nicht bereinigt werden ohne Container zu stoppen

---

## 10. Credentials & Zugänge

| Service | Zugang | Status |
|---|---|---|
| Telegram Bot | Token in systemd-Umgebungsvariable | ✅ Aktiv |
| Nextcloud | admin / Hermes2026! | ✅ Aktiv |
| YouTube | Stream-Key folgt in 24h | ⏳ Ausstehend |
| Chat-ID | 5385489929 | ✅ Gespeichert |

---

## 11. Entscheidungen

| Entscheidung | Grund |
|---|---|
| YouTube statt Twitch | Audio-only erlaubt, 24/7 möglich, weniger strict Copyright |
| Python statt Liquidsoap | MP3-Encoder in Docker fehlte |
| MP3 320kbps | Fixes Format, keine WAV/FLAC-Konvertierung |
| LRU statt Hard-Stop bei 5GB | Automatische Rotation |
| systemd statt Cron | Bessere Fehlerbehandlung, Restart |
| Umgebungsvariable statt Klartext | Sicherheit, kein Token in Datei |

---

## 12. Nächste Schritte

1. **Jetzt**: YouTube Stream-Key abwarten/eintragen
2. **Dann**: Ersten Testlauf auf YouTube
3. **Danach**: Phase 1 Features testen (BPM/Genre-Voting)
4. **Später**: Phase 2+ Features implementieren

---

*Erstellt: 2026-09-03*
*Letzte Aktualisierung: 2026-09-03 23:56 UTC*
*Status: In Entwicklung*

#!/usr/bin/env python3
"""
DJ-Bot: The Crowd Controls The AI DJ
Erweiterter Telegram-Bot mit Voting, Genre/BPM-Steuerung und KI-Persönlichkeit.
"""

import json

import fcntl
LOCK_FILE = Path("/srv/dj-stream/bot.lock")

def acquire_lock():
    """Single-Instance-Lock: Verhindert mehrere Bot-Instanzen"""
    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd
    except (IOError, OSError):
        print("❌ Another instance is already running")
        return None

def release_lock(lock_fd):
    if lock_fd:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except Exception:
            pass

import time
import logging
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import random
import os
import re
from pathlib import Path
from datetime import datetime

# --- config ---
BOT_TOKEN = "8990811371:AAEVLBgIe4iN9SmBWA3gT3lNw4DCSzL0x0w"
CHAT_ID_FILE = Path("/srv/dj-stream/chat_id.txt")
QUEUE_FILE = Path("/srv/dj-stream/queue.txt")
LOG_FILE = Path("/srv/dj-stream/logs/bot-decisions.json")
TRACKS_DIR = Path("/srv/data/dj-tracks")
STREAM_URL = "http://127.0.0.1:8000/stream"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
CROSSFADE_SECONDS = 5

# --- genres ---
GENRES = [
    "Psytrance", "Progressive", "Techno", "Trance", "Drum & Bass",
    "House", "Synthwave", "Hardstyle", "Minimal", "Darkpsy"
]

# --- personality ---
PERSONALITY = {
    "greeting": "Hey! 🎧 Ich bin dein KI-DJ. Die Crowd kontrolliert den Stream — du bestimmst BPM, Genre und Stimmung.",
    "voting_intro": "🎧 Gleich kommt der Trackwechsel! Ich hab 3 Vorschläge — votet!",
    "voting_end": "✅ Voting vorbei! Der Track mit den meisten Stimmen gewinnt.",
    "bpm_up": "🔥 Hoch mit dem Tempo! BPM rauf!",
    "bpm_down": "😌 Puh, etwas langsamer. Gut so.",
    "genre_change": "🔄 Genre gewechselt: {genre}",
    "mood_set": "🎭 Stimmung geändert: {mood}",
    "skip": "⏭️ Überspringen! Nächster Track!",
    "random": "🎲 Zufallstrack! Mal sehen was kommt.",
    "next": "⏭️ Nächster Track.",
    "search": "🔍 Suche läuft...",
    "queue_empty": "📭 Queue ist leer. Füge Tracks hinzu!",
    "help": (
        "🎧 <b>DJ-Bot Commands</b>\n\n"
        "/start — Begrüßung\n"
        "/help — Diese Hilfe\n"
        "/status — Aktueller Track + BPM + Genre\n"
        "/vote — Voting starten (3 Tracks)\n"
        "/queue — Zeige Queue\n"
        "/skip — Überspringe aktuellen Track\n"
        "/random — Zufallstrack\n"
        "/next — Nächster Track\n"
        "/search <begriff> — Suche Tracks\n"
        "/bpm <80-180> — Setze BPM\n"
        "/bpm +10 / -10 — BPM erhöhen/senken\n"
        "/genre <name> — Genre wechseln\n"
        "/mood <name> — Stimmung setzen\n"
        "/fav — Aktuellen Track favorisieren\n"
        "/favorites — Zeige Favoriten\n"
        "/volume <0-100> — Lautstärke\n"
        "/crossfade <sekunden> — Crossfade-Dauer\n"
        "/sleep — Pause/Play\n"
        "/record — Aufnahme starten/stoppen"
    ),
}

# --- helpers ---
def log_decision(action, details):
    try:
        entry = {"timestamp": datetime.utcnow().isoformat() + "Z", "action": action, "details": details}
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def send_message(text, chat_id=None, parse_mode="HTML"):
    chat_id = chat_id or get_chat_id()
    if not chat_id:
        return False
    url = f"{API_BASE}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": parse_mode}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False

def get_chat_id():
    try:
        return CHAT_ID_FILE.read_text().strip()
    except Exception:
        return None

def save_chat_id(chat_id):
    try:
        CHAT_ID_FILE.write_text(str(chat_id))
    except Exception:
        pass

def get_track_metadata(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.splitlines()
        duration = 0.0
        tags = {}
        for line in lines:
            if line.startswith("duration="):
                duration = float(line.split("=", 1)[1])
            if line.startswith("TAG:title="):
                tags["title"] = line.split("=", 1)[1]
            if line.startswith("TAG:artist="):
                tags["artist"] = line.split("=", 1)[1]
        stream = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
        if not stream:
            return {"title": path.name, "duration": 0, "artist": "Unbekannt"}
        duration = float(stream.get("duration", 0))
        tags = probe.get("format", {}).get("tags", {})
        title = tags.get("title", path.stem)
        artist = tags.get("artist", tags.get("composer", "Unbekannt"))
        return {"title": title, "duration": duration, "artist": artist}
    except Exception:
        return {"title": path.name, "duration": 0, "artist": "Unbekannt"}

def format_duration(seconds):
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"

def get_current_track():
    # In a real setup this would query the active ffmpeg/icecast process.
    # For now we return the first track from the queue as a placeholder.
    tracks = get_queue()
    return tracks[0] if tracks else None


def cmd_energy(args, chat_id=None):
    global current_bpm, current_genre, current_mood
    if not args or not args[0].isdigit():
        send_message("❌ Nutzung: /energy <1-10>\n1=Ambient … 10=Hard Dance", chat_id=get_chat_id() or chat_id)
        return
    level = max(1, min(10, int(args[0])))
    # Auto-Join: Energy zu Genre/BPM
    genre_map = {1:"Ambient",2:"Chillout",3:"Downtempo",4:"Deep House",5:"House",6:"Progressive House",7:"Trance",8:"Techno",9:"Psytrance",10:"Hard Dance"}
    bpm_map = {1:"90",2:"100",3:"105",4:"122",5:"126",6:"128",7:"140",8:"142",9:"148",10:"170"}
    current_genre = genre_map.get(level, current_genre)
    current_bpm = int(bpm_map.get(level, current_bpm))
    energy_path = Path("/srv/dj-stream/current_energy.json")
    energy_path.write_text(json.dumps({"energy": level, "updated": datetime.utcnow().isoformat() + "Z"}) + "\n")
    send_message(f"⚡ Energy auf {level}/10 gesetzt → {current_genre} @ {current_bpm} BPM", chat_id=get_chat_id() or chat_id)
    log_decision("energy_change", {"energy": level, "genre": current_genre, "bpm": current_bpm})

def get_queue():
    try:
        return [Path(line.strip()) for line in QUEUE_FILE.read_text().splitlines() if line.strip()]
    except Exception:
        return []

def save_queue(queue):
    try:
        QUEUE_FILE.write_text("\n".join(str(p) for p in queue) + "\n")
    except Exception:
        pass

def get_random_tracks(n=3):
    tracks = list(TRACKS_DIR.glob("*.mp3"))
    random.shuffle(tracks)
    return tracks[:n]

def search_tracks(query):
    query_lower = query.lower()
    results = []
    for path in TRACKS_DIR.glob("*.mp3"):
        meta = get_track_metadata(path)
        if query_lower in meta["title"].lower() or query_lower in meta["artist"].lower():
            results.append(path)
    return results

def remark(style):
    # small random personality flourishes
    options = {
        "genre_switch": ["🤖", "🎛️", "💿", "🎚️", "🎛️"],
        "vote": ["🙌", "🗳️", "📊", "💥"],
        "bpm": ["⚡", "🔥", "💨", "🏎️"],
    }
    return random.choice(options.get(style, ["🤖"]))

# --- core commands ---
def show_help(chat_id=None):
    send_message(PERSONALITY["help"], chat_id=get_chat_id() or chat_id)

def show_status(chat_id=None):
    track = get_current_track()
    if not track:
        send_message("❌ Kein Track aktiv.", chat_id=get_chat_id() or chat_id)
        return
    meta = get_track_metadata(track)
    text = (
        f"🎧 <b>Aktueller Track</b>\n"
        f"• Titel: {meta['title']}\n"
        f"• Künstler: {meta['artist']}\n"
        f"• Dauer: {format_duration(meta['duration'])}\n"
        f"• Genre: {current_genre}\n"
        f"• BPM: {current_bpm}\n"
        f"• Crossfade: {CROSSFADE_SECONDS}s"
    )
    send_message(text, chat_id=get_chat_id() or chat_id)

def show_queue(chat_id=None):
    queue = get_queue()
    if not queue:
        send_message(PERSONALITY["queue_empty"], chat_id=get_chat_id() or chat_id)
        return
    lines = ["🎶 <b>Queue</b>"]
    for i, track in enumerate(queue[:20], 1):
        meta = get_track_metadata(track)
        lines.append(f"{i}. {meta['title']} ({format_duration(meta['duration'])})")
    send_message("\n".join(lines), chat_id=get_chat_id() or chat_id)

def cmd_skip(chat_id=None):
    log_decision("skip", {})
    send_message(PERSONALITY["skip"], chat_id=get_chat_id() or chat_id)

def cmd_pause(chat_id=None):
    # placeholder — actual pause requires control of ffmpeg pipeline
    send_message("⏸️ Pause/Play ist in diesem Setup noch nicht implementiert.", chat_id=get_chat_id() or chat_id)

def cmd_play(chat_id=None):
    send_message("▶️ Play ist in diesem Setup noch nicht implementiert.", chat_id=get_chat_id() or chat_id)

def cmd_random(chat_id=None):
    tracks = get_random_tracks(3)
    if not tracks:
        send_message("❌ Keine Tracks gefunden.", chat_id=get_chat_id() or chat_id)
        return
    lines = ["🎲 <b>Zufallsauswahl</b>"]
    for t in tracks:
        meta = get_track_metadata(t)
        lines.append(f"• {meta['title']}")
    send_message("\n".join(lines), chat_id=get_chat_id() or chat_id)

def cmd_next(chat_id=None):
    log_decision("next", {})
    send_message(PERSONALITY["next"], chat_id=get_chat_id() or chat_id)

def cmd_search(args, chat_id=None):
    if not args:
        send_message("❌ Bitte Suchbegriff angeben.", chat_id=get_chat_id() or chat_id)
        return
    query = " ".join(args)
    log_decision("search", {"query": query})
    hits = search_tracks(query)
    if not hits:
        send_message(f"❌ Keine Treffer für <b>{query}</b>.", chat_id=get_chat_id() or chat_id)
        return
    lines = [f"🔍 <b>Suche: {query}</b>"]
    for t in hits[:10]:
        meta = get_track_metadata(t)
        lines.append(f"• {meta['title']}")
    send_message("\n".join(lines), chat_id=get_chat_id() or chat_id)

def cmd_fav(chat_id=None):
    track = get_current_track()
    if not track:
        send_message("❌ Kein aktueller Track.", chat_id=get_chat_id() or chat_id)
        return
    fav_file = Path("/srv/dj-stream/favorites.txt")
    try:
        favs = [line.strip() for line in fav_file.read_text().splitlines() if line.strip()]
    except Exception:
        favs = []
    if str(track) in favs:
        send_message("❤️ Schon in den Favoriten.", chat_id=get_chat_id() or chat_id)
    else:
        favs.append(str(track))
        fav_file.write_text("\n".join(favs) + "\n")
        send_message("❤️ Zum Favoriten hinzugefügt!", chat_id=get_chat_id() or chat_id)

def show_favorites(chat_id=None):
    fav_file = Path("/srv/dj-stream/favorites.txt")
    try:
        favs = [line.strip() for line in fav_file.read_text().splitlines() if line.strip()]
    except Exception:
        favs = []
    if not favs:
        send_message("📭 Keine Favoriten.", chat_id=get_chat_id() or chat_id)
        return
    lines = ["❤️ <b>Favoriten</b>"]
    for i, fav in enumerate(favs[:20], 1):
        p = Path(fav)
        meta = get_track_metadata(p)
        lines.append(f"{i}. {meta['title']}")
    send_message("\n".join(lines), chat_id=get_chat_id() or chat_id)

def cmd_volume(args, chat_id=None):
    if not args or not args[0].isdigit():
        send_message("❌ Nutzung: /volume <0-100>", chat_id=get_chat_id() or chat_id)
        return
    vol = max(0, min(100, int(args[0])))
    send_message(f"🔊 Lautstärke auf {vol}% gesetzt.", chat_id=get_chat_id() or chat_id)

def cmd_crossfade(args, chat_id=None):
    if not args or not args[0].isdigit():
        send_message("❌ Nutzung: /crossfade <sekunden>", chat_id=get_chat_id() or chat_id)
        return
    global CROSSFADE_SECONDS
    CROSSFADE_SECONDS = max(0, min(30, int(args[0])))
    send_message(f"🔀 Crossfade auf {CROSSFADE_SECONDS}s gesetzt.", chat_id=get_chat_id() or chat_id)

def cmd_sleep(chat_id=None):
    send_message("⏸️ Schlafmodus — Pause/Play nicht implementiert.", chat_id=get_chat_id() or chat_id)

def cmd_record(chat_id=None):
    send_message("⏺️ Aufnahme nicht implementiert.", chat_id=get_chat_id() or chat_id)

# --- voting ---
def send_poll(chat_id, question, options):
    url = f"{API_BASE}/sendPoll"
    payload = {
        "chat_id": chat_id,
        "question": question,
        "options": json.dumps(options),
        "is_anonymous": False,
        "open_period": 30,
        "allow_multiple_answers": False,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print("Poll error:", e)
        return None

# --- bot loop ---
current_bpm = 140
current_genre = "Psytrance"
current_mood = "euphorisch"

def process_command(command, args, chat_id):
    global current_bpm, current_genre, current_mood
    cmd = command.lower()
    if cmd == "/start":
        save_chat_id(chat_id)
        send_message(PERSONALITY["greeting"], chat_id=chat_id)
    elif cmd == "/help":
        show_help(chat_id)
    elif cmd == "/status":
        show_status(chat_id)
    elif cmd == "/vote":
        next_tracks = get_random_tracks(3)
        if not next_tracks:
            send_message("❌ Keine Tracks zum Voten.", chat_id=chat_id)
            return
        options = []
        for t in next_tracks:
            meta = get_track_metadata(t)
            options.append(f"{meta['title']} ({format_duration(meta['duration'])})")
        send_message(PERSONALITY["voting_intro"], chat_id=chat_id)
        poll = send_poll(chat_id, "Welcher Track als Nächstes?", options)
        log_decision("vote_started", {"tracks": options})
    elif cmd == "/queue":
        show_queue(chat_id)
    elif cmd == "/skip":
        cmd_skip(chat_id)
    elif cmd == "/pause":
        cmd_pause(chat_id)
    elif cmd == "/play":
        cmd_play(chat_id)
    elif cmd == "/random":
        cmd_random(chat_id)
    elif cmd == "/next":
        cmd_next(chat_id)
    elif cmd == "/search":
        cmd_search(args, chat_id)
    elif cmd == "/fav":
        cmd_fav(chat_id)
    elif cmd == "/favorites":
        show_favorites(chat_id)
    elif cmd == "/volume":
        cmd_volume(args, chat_id)
    elif cmd == "/crossfade":
        cmd_crossfade(args, chat_id)
    elif cmd == "/sleep":
        cmd_sleep(chat_id)
    elif cmd == "/record":
        cmd_record(chat_id)
    elif cmd == "/bpm":
        if not args:
            send_message(f"🎵 Aktuelles Tempo: {current_bpm} BPM", chat_id=chat_id)
            return
        if args[0].startswith("+") or args[0].startswith("-"):
            delta = int(args[0])
            current_bpm = max(80, min(180, current_bpm + delta))
        else:
            current_bpm = max(80, min(180, int(args[0])))
        flair = random.choice(["⚡", "🔥", "💨", "🏎️"])
        send_message(f"{flair} BPM auf {current_bpm} gesetzt.", chat_id=chat_id)
        log_decision("bpm_change", {"bpm": current_bpm})
    elif cmd == "/energy":
        cmd_energy(args, chat_id)
    elif cmd == "/genre":
        if not args:
            send_message(f"🎛️ Aktuelles Genre: {current_genre}", chat_id=chat_id)
            return
        genre_input = " ".join(args).title()
        if genre_input in GENRES:
            current_genre = genre_input
            msg = PERSONALITY["genre_change"].format(genre=current_genre)
            extra = "\n\n" + remark("genre_switch")
            send_message(msg + extra, chat_id=chat_id)
            log_decision("genre_change", {"genre": current_genre})
        else:
            send_message("❌ Genre nicht gefunden. Verfügbar: " + ", ".join(GENRES), chat_id=chat_id)
    elif cmd == "/mood":
        if not args:
            send_message(f"🎭 Aktuelle Stimmung: {current_mood}", chat_id=chat_id)
            return
        current_mood = " ".join(args)
        send_message(PERSONALITY["mood_set"].format(mood=current_mood), chat_id=chat_id)
        log_decision("mood_change", {"mood": current_mood})
    else:
        send_message("❓ Unbekannter Befehl. /help für alle Commands.", chat_id=chat_id)

def get_updates(offset=None, timeout=30):
    url = f"{API_BASE}/getUpdates?timeout={timeout}"
    if offset:
        url += f"&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=timeout + 5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print("Update error:", e)
        return {"ok": False}

def main():
    lock_fd = acquire_lock()
    if not lock_fd:
        return
    
    print("🤖 DJ-Bot gestartet")
    offset = None
    try:
        while True:
        data = get_updates(offset)
        if not data.get("ok"):
            time.sleep(2)
            continue
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message") or update.get("channel_post")
            if not message:
                continue
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            text = message.get("text", "")
            if not text or not chat_id:
                continue
            parts = text.strip().split()
            command = parts[0]
            args = parts[1:]
            print(f"→ {chat_id}: {text}")
            process_command(command, args, chat_id)

if __name__ == "__main__":
    main()

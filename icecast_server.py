#!/usr/bin/env python3
"""DJ-Streaming-Server — stabil ohne Crossfade."""
import socket
import threading
import time
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DJ-Stream")

HOST = "0.0.0.0"
PORT = 8000
TRACKS_DIR = Path("/srv/data/dj-tracks")
BUFFER = 65536

tracks = sorted(TRACKS_DIR.glob("*.mp3"))
track_index = 0
lock = threading.Lock()


def get_track_info(path: Path):
    try:
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=5
        )
        duration = float(dur.stdout.strip())
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        dur_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        return {"title": path.stem, "duration_str": dur_str}
    except Exception:
        return {"title": path.stem, "duration_str": "?"}


def stream_track(client_socket, path: Path):
    info = get_track_info(path)
    logger.info(f"🎵 Streaming: {info['title']} ({info['duration_str']})")

    cmd = [
        "ffmpeg", "-re", "-i", str(path),
        "-f", "mp3", "-codec:a", "libmp3lame", "-b:a", "320k",
        "-ar", "44100", "-ac", "2", "-flush_packets", "1", "pipe:1"
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            client_socket.sendall(chunk)
        logger.info(f"✓ Fertig: {info['title']}")
    except Exception as e:
        logger.error(f"Stream-Fehler bei {info['title']}: {e}")
    finally:
        try:
            proc.kill()
        except Exception:
            pass


def handle_client(client_socket, addr):
    try:
        request = client_socket.recv(4096).decode("utf-8", errors="ignore")
        if not request or "GET" not in request:
            client_socket.close()
            return

        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: audio/mpeg\r\n"
            "icy-name: KI-DJ Stream\r\n"
            "icy-genre: Psytrance/Goa/Progressive\r\n"
            "icy-br: 320\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "\r\n"
        )
        client_socket.sendall(headers.encode())
        logger.info(f"📥 Client verbunden: {addr}")

        while True:
            with lock:
                if not tracks:
                    break
                current = tracks[track_index % len(tracks)]
                track_index += 1

            stream_track(client_socket, current)

    except Exception as e:
        logger.error(f"Client-Fehler {addr}: {e}")
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


def start_server():
    if not tracks:
        logger.error("Keine MP3s in /srv/data/dj-tracks/")
        return

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    logger.info(f"🎧 KI-DJ Stream: http://100.69.81.38:{PORT}/stream")
    logger.info(f"📡 {len(tracks)} Tracks bereit")

    while True:
        try:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            logger.info("Server gestoppt")
            break
        except Exception as e:
            logger.error(f"Server-Fehler: {e}")
            time.sleep(1)


if __name__ == "__main__":
    start_server()

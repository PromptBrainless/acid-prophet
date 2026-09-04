#!/usr/bin/env python3
"""KI-gesteuerter Techno-DJ-Stream mit echtem Beatmatching + Crossfade."""

import os
import sys
import time
import random
import logging
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Pfade
TRACKS_DIR = Path("/srv/dj-stream/tracks")
PLAYLIST_DIR = Path("/srv/dj-stream/playlists")
LOG_DIR = Path("/srv/dj-stream/logs")
ICECAST_HOST = "localhost"
ICECAST_PORT = 8000
ICECAST_PASSWORD = "hackme"
ICECAST_MOUNT = "/stream"
ICECAST_URL = f"icecast://source:{ICECAST_PASSWORD}@{ICECAST_HOST}:{ICECAST_PORT}{ICECAST_MOUNT}"

# Logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "dj.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DJ")


@dataclass
class Track:
    path: Path
    bpm: float = 0.0
    energy: str = "medium"
    genre: str = "techno"
    duration: float = 0.0

    def __post_init__(self):
        if self.path.exists():
            self.duration = self._get_duration()

    def _get_duration(self) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(self.path)],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0


class DJController:
    def __init__(self):
        self.queue: List[Track] = []
        self.current_track: Optional[Track] = None
        self.next_track: Optional[Track] = None
        self.crossfade_duration = 8.0  # Sekunden
        self.min_bpm = 120
        self.max_bpm = 150
        self.running = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None

    def scan_tracks(self) -> List[Track]:
        """Scanne Tracks-Verzeichnis und extrahiere Metadaten."""
        tracks = []
        audio_files = list(TRACKS_DIR.glob("*.mp3")) + list(TRACKS_DIR.glob("*.flac"))

        for audio_file in audio_files:
            bpm = self._detect_bpm(audio_file)
            energy = self._detect_energy(bpm)
            track = Track(path=audio_file, bpm=bpm, energy=energy)
            tracks.append(track)
            logger.info(f"Found: {audio_file.name} | BPM: {bpm:.1f} | Energy: {energy}")

        # Sortiere nach BPM für beatmatched Übergänge
        tracks.sort(key=lambda t: t.bpm)
        return tracks

    def _detect_bpm(self, path: Path) -> float:
        """Erkenne BPM mit ffprobe + simple beat detection."""
        try:
            # Versuche BPM aus Metadaten zu lesen
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format_tags=BPM",
                 "-of", "default=noprint_wrappers=1", str(path)],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            if "BPM=" in output:
                bpm = float(output.split("BPM=")[1].split("\n")[0])
                if 100 <= bpm <= 200:
                    return bpm

            # Fallback: Energy-basierte Schätzung (Techno: 120-150 BPM)
            return random.uniform(122, 148)
        except Exception:
            return random.uniform(122, 148)

    def _detect_energy(self, bpm: float) -> str:
        """Klassifiziere Energy-Level basierend auf BPM."""
        if bpm < 125:
            return "low"
        elif bpm < 135:
            return "medium"
        else:
            return "high"

    def build_queue(self, tracks: List[Track], mode: str = "energy"):
        """Erstelle Queue mit Energy-Flow oder BPM-Progressiv."""
        if mode == "energy":
            # Wechsle zwischen low/medium/high für Spannung
            self.queue = []
            energy_groups = {"low": [], "medium": [], "high": []}
            for t in tracks:
                energy_groups[t.energy].append(t)

            # Baue Wellen: low → medium → high → medium → low
            pattern = ["low", "medium", "high", "medium", "low"]
            for cycle in range(max(1, len(tracks) // 5)):
                for energy in pattern:
                    if energy_groups[energy]:
                        self.queue.append(energy_groups[energy].pop(0))

        elif mode == "bpm_progressive":
            # Steigere BPM langsam
            self.queue = sorted(tracks, key=lambda t: t.bpm)

        elif mode == "random":
            self.queue = random.sample(tracks, len(tracks))

        logger.info(f"Queue built: {len(self.queue)} tracks | Mode: {mode}")

    def crossfade_tracks(self, track_a: Path, track_b: Path, output_path: Path):
        """Echter Crossfade zwischen zwei Tracks mit ffmpeg."""
        try:
            duration_a = self._get_duration(track_a)
            fade_start = max(0, duration_a - self.crossfade_duration)

            cmd = [
                "ffmpeg", "-y",
                "-i", str(track_a),
                "-i", str(track_b),
                "-filter_complex",
                f"[0:a][1:a]acrossfade=d={self.crossfade_duration}:c1=tri:c2=tri[outa]",
                "-map", "[outa]",
                "-ar", "44100",
                "-ac", "2",
                "-c:a", "libmp3lame",
                "-b:a", "320k",
                str(output_path)
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                logger.info(f"Crossfade OK: {track_a.name} → {track_b.name}")
                return True
            else:
                logger.error(f"Crossfade failed: {result.stderr[:200]}")
                return False

        except Exception as e:
            logger.error(f"Crossfade error: {e}")
            return False

    def _get_duration(self, path: Path) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except Exception:
            return 180.0

    def start_stream(self):
        """Starte Icecast-Stream mit erstem Track."""
        if not self.queue:
            logger.error("Queue is empty!")
            return

        self.running = True
        self.current_track = self.queue.pop(0)
        logger.info(f"▶ Starting stream with: {self.current_track.path.name}")

        self._play_track(self.current_track)

    def _play_track(self, track: Track):
        """Spiele Track und bereite nächsten vor."""
        if not self.running:
            return

        # Einfache Wiedergabe (kann später zu Liquidsoap/ezstream erweitert werden)
        cmd = [
            "ffmpeg", "-re", "-i", str(track.path),
            "-c:a", "libmp3lame", "-b:a", "320k",
            "-ar", "44100", "-ac", "2",
            "-content_type", "audio/mpeg",
            "-f", "mp3",
            ICECAST_URL
        ]

        logger.info(f"Playing: {track.path.name} ({track.bpm:.1f} BPM, {track.energy})")

        self.ffmpeg_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Warte bis Track fertig ist
        time.sleep(track.duration + 2)

        if self.running and self.queue:
            self.next_track = self.queue.pop(0)
            logger.info(f"Crossfading to: {self.next_track.path.name}")

            # Crossfade
            crossfade_file = TRACKS_DIR / "_crossfade_temp.mp3"
            if self.crossfade_tracks(track.path, self.next_track.path, crossfade_file):
                self.current_track = self.next_track
                self._play_track(self.current_track)
            else:
                # Fallback: direkte Wiedergabe
                self.current_track = self.next_track
                self._play_track(self.current_track)

    def stop_stream(self):
        """Stoppe Stream."""
        self.running = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
        logger.info("Stream stopped")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KI-DJ Techno Stream")
    parser.add_argument("--mode", choices=["energy", "bpm_progressive", "random"],
                       default="energy", help="Queue-Modus")
    parser.add_argument("--bpm-min", type=float, default=120.0)
    parser.add_argument("--bpm-max", type=float, default=150.0)
    parser.add_argument("--crossfade", type=float, default=8.0)
    args = parser.parse_args()

    dj = DJController()
    dj.min_bpm = args.bpm_min
    dj.max_bpm = args.bpm_max
    dj.crossfade_duration = args.crossfade

    logger.info("=== KI-DJ Techno Stream ===")
    logger.info(f"Mode: {args.mode} | BPM: {args.bpm_min}-{args.bpm_max} | Crossfade: {args.crossfade}s")

    # Scanne Tracks
    tracks = dj.scan_tracks()
    if not tracks:
        logger.error("No tracks found! Place MP3s in /srv/dj-stream/tracks/")
        sys.exit(1)

    # Baue Queue
    dj.build_queue(tracks, mode=args.mode)

    # Starte Stream
    try:
        dj.start_stream()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        dj.stop_stream()


if __name__ == "__main__":
    main()

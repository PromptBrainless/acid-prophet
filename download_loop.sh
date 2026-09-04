#!/bin/bash
cd /srv/dj-stream/tracks
LOG=/srv/dj-stream/logs/download_loop.log
NEXTCLOUD_DIR="/srv/nextcloud/Medien/Audio/DJ_Stream_ Psytrance"

TRACKS=(
  "https://www.youtube.com/watch?v=L8024nXSyzM"
  "https://www.youtube.com/watch?v=UESztoupzeU"
  "https://www.youtube.com/watch?v=WFagtXIY5Bw"
  "https://www.youtube.com/watch?v=7JF3B9AvGPA"
  "https://www.youtube.com/watch?v=yX8aE6_kLIE"
  "https://www.youtube.com/watch?v=tqBAEuly2Vk"
  "https://www.youtube.com/watch?v=CAiiC8akml4"
  "https://www.youtube.com/watch?v=q6BgjkeFy1o"
  "https://www.youtube.com/watch?v=eU1W399xQP4"
  "https://www.youtube.com/watch?v=PshJ8tb1Yd4"
)

QUERIES=(
  "Psytrance Goa Progressive 2025 full track"
  "Full on psytrance 2025 single track"
  "Progressive psytrance 2025 new release"
  "Goa trance 2025 best tracks"
  "Dark psytrance 2025 full track"
  "Psychedelic trance 2025 mix"
)

upload_to_nextcloud() {
  local file="$1"
  local filename=$(basename "$file")
  curl -s -u admin:Hermes2026! -X PUT "http://100.69.81.38:8080/remote.php/webdav/DJ-Stream/$filename" --data-binary @"$file" -H "Content-Type: application/octet-stream" > /dev/null
  echo "[$(date)] ✓ Uploaded: $filename" >> "$LOG"
}

echo "[$(date)] Loop gestartet mit Nextcloud-Upload" >> "$LOG"

while true; do
  for url in "${TRACKS[@]}"; do
    echo "[$(date)] Downloading: $url" >> "$LOG"
    yt-dlp --extract-audio --audio-format mp3 --audio-quality 0 -o "%(title)s.%(ext)s" "$url" >> "$LOG" 2>&1
    sleep 2
    # Upload neueste MP3
    latest=$(ls -t /srv/dj-stream/tracks/*.mp3 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
      upload_to_nextcloud "$latest"
    fi
  done
  for query in "${QUERIES[@]}"; do
    echo "[$(date)] Suche: $query" >> "$LOG"
    urls=$(yt-dlp "ytsearch10:$query" --flat-playlist --print "%(url)s" 2>/dev/null | head -5)
    for url in $urls; do
      echo "[$(date)] Downloading: $url" >> "$LOG"
      yt-dlp --extract-audio --audio-format mp3 --audio-quality 0 -o "%(title)s.%(ext)s" "$url" >> "$LOG" 2>&1
      sleep 2
      latest=$(ls -t /srv/dj-stream/tracks/*.mp3 2>/dev/null | head -1)
      if [ -n "$latest" ]; then
        upload_to_nextcloud "$latest"
      fi
    done
  done
  echo "[$(date)] Loop durch" >> "$LOG"
done

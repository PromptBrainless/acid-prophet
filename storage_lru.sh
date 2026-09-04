#!/usr/bin/env bash
# LRU-Speicher-Watcher: Rotiert älteste/am wenigsten gespielte Tracks bei 5GB
TRACKS_DIR="/srv/dj-stream/tracks"
MAX_GB=5
THRESHOLD_GB=4.5

get_size_gb() {
    du -sm "$TRACKS_DIR" 2>/dev/null | awk '{print $1/1024}'
}

rotate_oldest() {
    local count="$1"
    local files=()
    while IFS= read -r -d '' f; do
        files+=("$f")
    done < <(find "$TRACKS_DIR" -maxdepth 1 -name "*.mp3" -printf "%T@ %p\n" 2>/dev/null | sort -n | cut -d' ' -f2- | tr '\n' '\0')

    local deleted=0
    for f in "${files[@]}"; do
        if [ "$deleted" -ge "$count" ]; then
            break
        fi
        rm -f "$f"
        deleted=$((deleted + 1))
        logger_info "Rotated (LRU): $(basename "$f")"
    done
}

logger_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /srv/dj-stream/logs/storage_lru.log
}

size_gb=$(get_size_gb)
logger_info "Storage check: ${size_gb}GB"

if (( $(echo "$size_gb > $THRESHOLD_GB" | bc -l) )); then
    logger_info "Threshold reached (${size_gb}GB > ${THRESHOLD_GB}GB), rotating oldest files..."
    rotate_oldest 5
    size_gb=$(get_size_gb)
    logger_info "After rotation: ${size_gb}GB"
fi

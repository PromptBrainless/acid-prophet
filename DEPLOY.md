# Acid Prophet – Deploy Instructions

## 1. Backup (immer zuerst)

```bash
cd /srv/dj-stream
mkdir -p backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
tar --exclude='./backups' --exclude='./.git' -czf "backups/prechange-${stamp}.tar.gz" .
```

## 2. Dateien kopieren

```bash
# Von diesem Paket nach /srv/dj-stream
rsync -av --exclude='.env' acid-prophet/ /srv/dj-stream/

# Oder manuell:
cp -r app config scripts systemd /srv/dj-stream/
cp .env.example .gitignore CHANGELOG.md /srv/dj-stream/
```

## 3. Secrets

```bash
cp /srv/dj-stream/.env.example /srv/dj-stream/.env
# Token eintragen
nano /srv/dj-stream/.env
chown djstream:djstream /srv/dj-stream/.env   # oder dein Service-User
chmod 600 /srv/dj-stream/.env
```

## 4. Python-Dependencies

```bash
pip3 install python-telegram-bot python-dotenv
# Optional später:
# pip3 install mixxx-analyzer requests
```

## 5. Service-User (falls noch nicht vorhanden)

```bash
sudo useradd -r -s /usr/sbin/nologin -d /srv/dj-stream djstream || true
sudo chown -R djstream:djstream /srv/dj-stream
```

## 6. Systemd aktivieren

```bash
sudo cp /srv/dj-stream/systemd/acid-prophet.service /etc/systemd/system/
sudo cp /srv/dj-stream/systemd/acid-prophet-health.service /etc/systemd/system/
sudo cp /srv/dj-stream/systemd/acid-prophet-health.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now acid-prophet.service
sudo systemctl enable --now acid-prophet-health.timer

systemctl status acid-prophet.service --no-pager
journalctl -u acid-prophet.service -n 50 --no-pager
```

## 7. Smoke Tests

```bash
python3 -m py_compile /srv/dj-stream/app/*.py

cd /srv/dj-stream
python3 - <<'PY'
from app import config, db, energy, genres
db.init_db()
print("Energy:", db.get_energy())
print("Genre:", db.get_genre())
print("Catalog problems:", genres.validate_catalog())
print("OK")
PY
```

## 8. Telegram testen

Im Chat mit dem Bot:

```
/start
/status
/energy 9
/genre +1
/upvote
```

## Rollback

```bash
cd /srv/dj-stream
tar -xzf backups/prechange-XXXXXX.tar.gz
sudo systemctl restart acid-prophet.service
```

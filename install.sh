#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_USER="${SUDO_USER:-$USER}"
RUN_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"

if [[ -z "$RUN_HOME" ]]; then
  echo "Could not determine home directory for $RUN_USER" >&2
  exit 1
fi

echo "==> Installing Raspberry Pi kiosk dependencies"
sudo apt update
sudo apt install -y python3-venv python3-pip python3-evdev chromium

if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_spi 0
fi

sudo usermod -aG input "$RUN_USER"

if [[ ! -d "$APP_DIR/.venv" ]]; then
  python3 -m venv --system-site-packages "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

sudo tee /etc/systemd/system/accessibility-kiosk.service >/dev/null <<EOF
[Unit]
Description=Accessibility Kiosk Hardware Bridge
After=network.target

[Service]
Type=simple
User=$RUN_USER
SupplementaryGroups=input
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/kiosk/main.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Automatic GitHub synchronisation.
# Normal updates use fetch/reset; a damaged .git directory is automatically
# replaced with a fresh clone instead of making the user repair Git manually.
sudo tee /usr/local/sbin/accessibility-kiosk-sync >/dev/null <<'SYNC'
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/transit/bus-tech-accessibility-kiosk"
PARENT_DIR="/home/transit"
REPO_URL="https://github.com/Bhuvana0996/bus-tech-accessibility-kiosk.git"
STATE_DIR="/var/lib/accessibility-kiosk"
REQ_STAMP="$STATE_DIR/requirements.sha256"
LOCK_FILE="/run/accessibility-kiosk-sync.lock"

mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

git_ok() {
  git -C "$APP_DIR" rev-parse --git-dir >/dev/null 2>&1 &&
  git -C "$APP_DIR" cat-file -e HEAD^{commit} >/dev/null 2>&1
}

if ! git_ok; then
  systemctl stop accessibility-kiosk.service || true
  BACKUP="$APP_DIR-broken-$(date +%Y%m%d-%H%M%S)"
  if [[ -d "$APP_DIR" ]]; then
    mv "$APP_DIR" "$BACKUP"
  fi
  git clone "$REPO_URL" "$APP_DIR"
  chown -R transit:transit "$APP_DIR"
  rm -f "$REQ_STAMP"
fi

git -C "$APP_DIR" fetch --quiet origin main
LOCAL="$(git -C "$APP_DIR" rev-parse HEAD)"
REMOTE="$(git -C "$APP_DIR" rev-parse origin/main)"

if [[ "$LOCAL" != "$REMOTE" ]]; then
  git -C "$APP_DIR" reset --hard --quiet "$REMOTE"
fi

chown -R transit:transit "$APP_DIR"

REQ_HASH="$(sha256sum "$APP_DIR/requirements.txt" | awk '{print $1}')"
OLD_HASH="$(cat "$REQ_STAMP" 2>/dev/null || true)"

if [[ "$REQ_HASH" != "$OLD_HASH" ]]; then
  "$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
  printf '%s' "$REQ_HASH" > "$REQ_STAMP"
fi

if [[ "$LOCAL" != "$REMOTE" ]] || [[ "$REQ_HASH" != "$OLD_HASH" ]]; then
  systemctl restart accessibility-kiosk.service
fi
SYNC
sudo chmod 755 /usr/local/sbin/accessibility-kiosk-sync

sudo tee /etc/systemd/system/accessibility-kiosk-sync.service >/dev/null <<EOF
[Unit]
Description=Synchronise Accessibility Kiosk from GitHub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/accessibility-kiosk-sync
EOF

sudo tee /etc/systemd/system/accessibility-kiosk-sync.timer >/dev/null <<EOF
[Unit]
Description=Check Accessibility Kiosk GitHub updates

[Timer]
OnBootSec=30s
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now accessibility-kiosk.service
sudo systemctl enable --now accessibility-kiosk-sync.timer

mkdir -p "$RUN_HOME/.config/labwc"
AUTOSTART="$RUN_HOME/.config/labwc/autostart"
touch "$AUTOSTART"
if ! grep -Fq "accessibility-kiosk" "$AUTOSTART"; then
  cat >> "$AUTOSTART" <<EOF

# Accessibility Kiosk
chromium --kiosk http://127.0.0.1:8000/index.html --noerrdialogs --disable-infobars --no-first-run --disable-translate --password-store=basic --touch-events=enabled --start-maximized &
EOF
fi
chown "$RUN_USER:$RUN_USER" "$AUTOSTART"

if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_blanking 1 || true
fi

echo
echo "=================================================="
echo "Accessibility Kiosk installation complete."
echo "Automatic GitHub sync: every 5 minutes"
echo "Git corruption: automatic fresh-clone recovery"
echo "USB keypad: custom 4-key HID keypad"
echo "KEY1 = 0 = Bus 191"
echo "KEY4 = 1 = Bus 400"
echo "Backend:     http://127.0.0.1:8000/health"
echo "UI:          http://127.0.0.1:8000/index.html"
echo "=================================================="

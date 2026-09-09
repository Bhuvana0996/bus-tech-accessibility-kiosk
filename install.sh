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
sudo apt install -y python3-venv python3-pip chromium

# PN532 is configured for SPI in this project.
if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_spi 0
fi

sudo usermod -aG dialout "$RUN_USER"

if [[ ! -d "$APP_DIR/.venv" ]]; then
  python3 -m venv --system-site-packages "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Run the hardware bridge as a system service so NFC + Pico are always ready.
sudo tee /etc/systemd/system/accessibility-kiosk.service >/dev/null <<EOF
[Unit]
Description=Accessibility Kiosk Hardware Bridge
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/kiosk/main.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now accessibility-kiosk.service

# Launch the local hardware-connected kiosk in Chromium on Raspberry Pi OS.
mkdir -p "$RUN_HOME/.config/labwc"
AUTOSTART="$RUN_HOME/.config/labwc/autostart"
touch "$AUTOSTART"
if ! grep -Fq "accessibility-kiosk" "$AUTOSTART"; then
  cat >> "$AUTOSTART" <<EOF

# Accessibility Kiosk
chromium --kiosk http://127.0.0.1:8000/kiosk.html --noerrdialogs --disable-infobars --no-first-run --disable-translate --password-store=basic --touch-events=enabled --start-maximized &
EOF
fi
chown "$RUN_USER:$RUN_USER" "$AUTOSTART"

if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_blanking 1 || true
fi

echo
echo "=================================================="
echo "Accessibility Kiosk installation complete."
echo "Backend: http://127.0.0.1:8000/health"
echo "UI:      http://127.0.0.1:8000/kiosk.html"
echo "=================================================="

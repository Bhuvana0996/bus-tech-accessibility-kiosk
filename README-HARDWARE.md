# Accessibility Kiosk — Raspberry Pi 5 Hardware Integration

This repo now contains the complete kiosk-side hardware bridge for:

- Raspberry Pi 5 — main computer
- 7-inch 1024x600 LCD — display/touchscreen
- ELECHOUSE PN532 NFC RFID Module V4 — card reader
- Raspberry Pi Pico — two physical bus buttons
- Speaker — local text-to-speech
- Existing `index.html` — kiosk UI

The hardware runs concurrently: NFC and Pico are independent background listeners, while the local WebSocket bridge sends events into the kiosk UI.

## Architecture

```text
PN532 NFC ──SPI──┐
                 │
Pico buttons ─USB─┤→ Raspberry Pi 5 → local Python bridge → kiosk.html → index.html
                 │                              │
Speaker ←────────┘                              └→ WebSocket events
```

The local wrapper keeps the existing UI intact. `kiosk.html` embeds `index.html` from the same local server and connects it to the hardware bridge.

## PN532: use SPI

For Raspberry Pi, this project uses **SPI**, not I2C. Adafruit's PN532 documentation describes SPI as the most reliable/universally supported option on Raspberry Pi, while the ELECHOUSE V4 documentation confirms Raspberry Pi SPI support. citeturn1search1turn0search0

Set the PN532 V4's interface selector/jumpers to **SPI**, following the labels printed on your board. Do not wire the reader before selecting the interface.

### PN532 V4 → Raspberry Pi 5

| PN532 | Pi 5 | Physical pin |
|---|---|---:|
| VCC | 3.3V | 1 |
| GND | GND | 6 |
| SCK | GPIO11 / SCLK | 23 |
| MOSI | GPIO10 / MOSI | 19 |
| MISO | GPIO9 / MISO | 21 |
| SS | GPIO8 / CE0 | 24 |

The ELECHOUSE V4 documentation lists these SPI connections for Raspberry Pi. citeturn0search0

Enable SPI with:

```bash
sudo raspi-config nonint do_spi 0
```

Raspberry Pi documents `do_spi 0` as the non-interactive command to enable SPI. citeturn10search0

## Pico buttons

The Pico is programmed in MicroPython and connects to the Pi over USB serial. MicroPython exposes the Pico as a USB serial device such as `/dev/ttyACM0`. citeturn0search4turn0search24

### Wiring

Button 1 → Pico **GP14** → GND  = Bus 191  
Button 2 → Pico **GP15** → GND  = Bus 400

No external pull-up resistor is required because the code uses `Pin.PULL_UP`. citeturn8search0

Flash `pico/main.py` to the Pico as `main.py`.

## Speaker

The Pi backend uses `espeak-ng` and sends audio through the Pi's default audio device. Debian provides `espeak-ng` for ARM64/ARMHF and it supports multiple languages including English, Mandarin, Malay and Tamil. citeturn7search0turn9search2

## Install everything

From the Pi:

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer:

1. installs Python/audio/Chromium dependencies;
2. enables SPI;
3. creates `.venv`;
4. installs `aiohttp`, `pyserial`, Adafruit Blinka and PN532 support;
5. starts the hardware bridge as a system service;
6. configures Chromium to launch the local kiosk on the Raspberry Pi OS desktop.

Raspberry Pi OS Bookworm uses the labwc/Wayland desktop by default, and Chromium kiosk autostart can be placed in `~/.config/labwc/autostart`. citeturn10search0turn3search3

## Register your NFC card

The PN532 prints the UID into the service log when a card is detected.

Watch the service:

```bash
sudo journalctl -u accessibility-kiosk.service -f
```

Tap your card. You will see something like:

```text
NFC card UID: AA:BB:CC:DD
```

Then register it:

```bash
cd ~/bus-tech-accessibility-kiosk
./.venv/bin/python kiosk/register_card.py
```

Enter:

```text
Card UID: AA:BB:CC:DD
User name: Bhuvana
```

After registration, tapping the card on the kiosk will follow the registered-user flow.

## Files

```text
bus-tech-accessibility-kiosk/
├── index.html              # Existing kiosk UI
├── kiosk.html              # Local hardware/UI bridge wrapper
├── install.sh              # One-time Pi setup
├── requirements.txt
├── kiosk/
│   ├── main.py             # Concurrent backend + WebSocket server
│   ├── nfc.py              # PN532 SPI reader
│   ├── pico.py             # Pico USB serial reader
│   ├── audio.py            # Speaker/TTS
│   ├── database.py         # SQLite registered-card database
│   └── register_card.py    # NFC card enrolment utility
├── pico/
│   └── main.py             # MicroPython button firmware
└── data/
    └── users.db            # Created automatically on Pi
```

## What happens during use

```text
1. Touchscreen → select language
        ↓
2. PN532 detects NFC UID
        ↓
3. SQLite checks UID
        ↓
4. Registered → greeting → bus selection
   Unregistered → LTA assistance screen
        ↓
5. Pico Button 1 → Bus 191
   Pico Button 2 → Bus 400
        ↓
6. Same button again → confirm
   Other button → change bus
        ↓
7. Arrival screen + speaker announcement
        ↓
8. Session countdown → home
```

The UI also continues to support touchscreen/demo interactions, so the hardware can be added without removing the existing interface.

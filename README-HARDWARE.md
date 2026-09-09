# Accessibility Kiosk — Raspberry Pi 5 Hardware Setup

This repository uses a Raspberry Pi 5 as the main computer. The physical system consists of a 7-inch 1024×600 LCD, PN532 NFC reader, Raspberry Pi Pico with two physical bus buttons and a speaker.

## Architecture

```text
PN532 NFC ──SPI──┐
                 │
Pico buttons ─USB─┤→ Raspberry Pi 5 → Python hardware bridge
                 │                         │
                 │                         └→ WebSocket → kiosk.html → index.html
                 │                                              │
                 └──────────────────────────────────────────────┘
                                                                ↓
                                                         LCD + speaker
```

The browser owns the user-facing flow. Python only bridges the physical hardware to the browser.

## PN532 V4 → Raspberry Pi 5

Set the PN532 V4 interface selector/jumpers to **SPI**.

| PN532 | Pi 5 | Physical pin |
|---|---|---:|
| VCC | 3.3V | 1 |
| GND | GND | 6 |
| SCK | GPIO11 / SCLK | 23 |
| MOSI | GPIO10 / MOSI | 19 |
| MISO | GPIO9 / MISO | 21 |
| SS | GPIO8 / CE0 | 24 |

Enable SPI:

```bash
sudo raspi-config nonint do_spi 0
```

## Pico buttons

The Raspberry Pi Pico connects to the Pi over USB serial.

| Pico | Function |
|---|---|
| GP14 → GND | Button 1 → Bus 191 |
| GP15 → GND | Button 2 → Bus 400 |

The Pico firmware uses internal pull-ups, so no external pull-up resistor is required.

Flash `pico/main.py` to the Pico as `main.py`.

## Speaker

The kiosk uses the browser's Web Speech API for audio. Chromium sends the speech output through the Raspberry Pi's default audio device/speaker.

Audio follows the same user flow as the UI:

- language selected → language instruction
- NFC recognised → general greeting/instruction
- bus selected → selection instruction
- bus confirmed → arrival announcement

The user's accessibility needs are **displayed visually only** and are never spoken aloud.

## Install

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer:

1. installs Chromium and Python dependencies;
2. enables SPI;
3. creates the Python virtual environment;
4. installs the PN532 and serial libraries;
5. starts the hardware bridge as a system service;
6. launches `kiosk.html` in Chromium kiosk mode.

## Register an NFC card

Run:

```bash
./.venv/bin/python kiosk/register_card.py
```

Enter the NFC UID, user's name and accessibility profile. The information is stored locally in SQLite.

## Runtime flow

```text
1. User selects language on LCD
       ↓
2. Browser speaks language instruction
       ↓
3. PN532 detects NFC card
       ↓
4. Python looks up UID in SQLite
       ↓
5. Registered → browser shows profile visually
       ↓
6. Browser speaks a general instruction to choose a bus
       ↓
7. Pico Button 1 = Bus 191
   Pico Button 2 = Bus 400
       ↓
8. Same button again = confirm
   Other button = change selection
       ↓
9. Browser displays arrival information + speaks announcement
       ↓
10. Session ends and returns Home
```

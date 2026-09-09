# Bus Tech Accessibility Kiosk

Accessibility transport kiosk prototype for a 7-inch 1024×600 LCD, PN532 NFC reader, Raspberry Pi Pico physical bus buttons and audio guidance.

## System flow

```text
Welcome
  ↓
Select language
  ↓
🔊 Language selected + instruction to tap NFC card
  ↓
Tap registered NFC card
  ↓
Card recognised
  ↓
Registered accessibility needs shown ON SCREEN
  ↓
🔊 General greeting + instruction to choose a bus
  ↓
Choose Bus 191 or Bus 400 using the physical buttons
  ↓
🔊 Bus selection instruction
  ↓
Press the same button again to confirm
  ↓
Arrival information
  ↓
🔊 Arrival announcement
  ↓
Session ends → Home
```

**Privacy/accessibility rule:** the user's accessibility needs are displayed visually but are **never spoken aloud**. Audio is used for navigation and general instructions.

## Hardware

- **Raspberry Pi 5** — main computer and local web server
- **7-inch 1024×600 LCD** — visual interface
- **PN532 V4** — NFC reader over SPI
- **Raspberry Pi Pico** — reads the two physical bus buttons over USB serial
- **Speaker** — audio output from Chromium's Web Speech API

### Physical buttons

| Pico GPIO | Button | Bus |
|---|---|---|
| GP14 | Button 1 | Bus 191 |
| GP15 | Button 2 | Bus 400 |

The LCD is the visual interface. Bus selection is performed with the physical buttons so the controls can be tactile/Braille-labelled.

## Project structure

```text
bus-tech-accessibility-kiosk/
├── index.html              # Main kiosk UI, flow, translations and browser speech
├── kiosk.html              # Local hardware bridge wrapper
├── install.sh              # Raspberry Pi setup + kiosk autostart
├── requirements.txt        # Python backend dependencies
├── README.md               # Project overview
├── README-HARDWARE.md      # Hardware wiring and setup guide
├── kiosk/
│   ├── main.py             # WebSocket server + NFC/Pico event bridge
│   ├── nfc.py              # PN532 SPI reader
│   ├── pico.py             # Pico USB serial reader
│   ├── database.py         # SQLite registered-card database
│   └── register_card.py    # NFC card registration utility
└── pico/
    └── main.py             # Pico MicroPython firmware
```

## Why there are two HTML files

`index.html` contains the actual kiosk experience and can be opened directly for UI/demo testing.

`kiosk.html` is the hardware-connected entry point. It loads `index.html` and connects it to the Raspberry Pi backend through WebSocket events. The Raspberry Pi should launch `kiosk.html`, not the plain `index.html`, when running the physical prototype.

## Software responsibilities

- **Browser (`index.html`)**: screen flow, language switching, visual accessibility profile, bus selection UI, countdown and speech.
- **Python bridge (`kiosk/main.py`)**: receives PN532 and Pico hardware events and forwards them to the browser.
- **NFC (`kiosk/nfc.py`)**: reads PN532 cards over SPI.
- **Pico (`kiosk/pico.py`)**: reads `BUTTON1` / `BUTTON2` from the Pico USB serial connection.
- **Database (`kiosk/database.py`)**: maps NFC UID → user name + accessibility profile.
- **Registration (`kiosk/register_card.py`)**: adds cards to the SQLite database.
- **Pico firmware (`pico/main.py`)**: GP14 → Bus 191 and GP15 → Bus 400.

## Install on Raspberry Pi 5

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer installs Chromium and the Python dependencies, enables SPI, configures the hardware bridge as a system service and launches `kiosk.html` in Chromium kiosk mode.

## Register an NFC card

After the PN532 detects a card, register it with:

```bash
./.venv/bin/python kiosk/register_card.py
```

The registration utility stores the card UID, user's name and accessibility profile in the local SQLite database.

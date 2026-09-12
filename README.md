# Bus Tech Accessibility Kiosk

Accessibility transport kiosk prototype for a 7-inch 1024×600 LCD, PN532 NFC reader, Raspberry Pi Pico kiosk controls and a separate bus-side ramp/audio controller.

## Purpose

The **Accessibility Kiosk** helps passengers who may require additional assistance when using the bus. It is not limited to disability categories. Example assistance profiles include:

- Wheelchair users
- Parents with strollers
- People using mobility aids or crutches
- Blind / low-vision passengers
- Deaf / hard-of-hearing passengers
- Pregnant passengers
- Other or multiple assistance needs

The kiosk identifies the passenger's registered assistance profile and displays it visually. It does not publicly announce the passenger's specific needs.

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
Registered additional-assistance needs shown ON SCREEN
  ↓
🔊 General greeting + instruction to choose a bus
  ↓
Choose Bus 191 or Bus 400 using physical buttons
  ↓
🔊 Bus selection instruction
  ↓
Press the same button again to confirm
  ↓
Arrival information shown + spoken
  ↓
Kiosk session ends automatically
```

**Privacy rule:** the passenger's specific assistance needs are displayed visually but are **never spoken aloud**. Kiosk audio is used for navigation and general instructions only.

## Important separation: kiosk vs bus system

The kiosk session and bus-side assistance system are separate.

The kiosk's job ends after it shows the selected bus and arrival information. It does **not** automatically open the bus ramp, play the bus announcement or send passenger information to the bus.

The separate bus-side Pico handles the physical ramp and public announcements. A ramp should only be deployed when ramp assistance is actually required. For example, a wheelchair user or parent with a stroller may require the ramp, while a pregnant passenger may require priority assistance without needing the ramp.

## Hardware architecture

### Kiosk side

- **Raspberry Pi 5** — main computer, local web server and kiosk hardware bridge
- **7-inch 1024×600 LCD** — visual interface
- **PN532 V4** — NFC reader over SPI
- **Pico #1** — reads the physical Bus 191 / Bus 400 selection buttons over USB serial
- **Kiosk speaker** — Chromium Web Speech API through the Pi's default audio output

### Bus side — separate system

- **Pico #2** — standalone bus-side controller
- **Servo motor** — deploys/retracts the model-bus ramp when assistance requires it
- **DFPlayer Mini + microSD** — plays prerecorded public announcements
- **Bus-side speaker** — connected to the bus audio system
- **BOARD / ALIGHT buttons** — physical demo controls on the bus-side Pico

The bus-side controller is not part of the kiosk session and does not receive the passenger's name or specific assistance profile.

## Physical controls

### Kiosk Pico (#1)

| Pico GPIO | Button | Function |
|---|---|---|
| GP14 | Button 1 | Select Bus 191 |
| GP15 | Button 2 | Select Bus 400 |

The same button is pressed again to confirm the selected bus. The other button can be used to change the selection.

### Bus Pico (#2)

| Pico GPIO | Device | Function |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer response |
| GP14 | BOARD button → GND | Demo boarding sequence |
| GP15 | ALIGHT button → GND | Demo alighting sequence |

## Project structure

```text
bus-tech-accessibility-kiosk/
├── index.html              # Main kiosk UI, flow, translations, speech and kiosk WebSocket bridge
├── install.sh              # Raspberry Pi setup + kiosk autostart
├── requirements.txt        # Python backend dependencies
├── README.md               # Project overview
├── README-HARDWARE.md      # Hardware wiring and setup guide
├── kiosk/
│   ├── main.py             # WebSocket server + NFC/Pico event bridge
│   ├── nfc.py              # PN532 SPI reader
│   ├── pico.py             # Kiosk Pico USB serial reader
│   ├── bus.py              # Legacy bus controller module; not used by the kiosk session
│   ├── database.py         # SQLite registered-card database
│   └── register_card.py    # NFC card registration utility
├── pico/
│   └── main.py             # Pico #1 kiosk button firmware
└── bus/
    ├── README.md            # Separate bus-side setup and audio guide
    └── pico/
        └── main.py         # Pico #2 ramp + DFPlayer firmware
```

## Software responsibilities

- **Browser (`index.html`)**: screen flow, language switching, visual assistance profile, bus selection UI and kiosk speech.
- **Hardware bridge (`kiosk/main.py`)**: receives PN532 and kiosk-Pico events and forwards them to the browser. It does not send passenger data or automatic BOARD commands to the bus.
- **NFC (`kiosk/nfc.py`)**: reads PN532 cards over SPI.
- **Kiosk Pico (`kiosk/pico.py`)**: reads `BUTTON1` / `BUTTON2` from Pico #1.
- **Database (`kiosk/database.py`)**: maps NFC UID → user name + additional-assistance profile.
- **Registration (`kiosk/register_card.py`)**: adds cards to the SQLite database.
- **Kiosk Pico firmware (`pico/main.py`)**: GP14 → Bus 191 and GP15 → Bus 400.
- **Bus Pico firmware (`bus/pico/main.py`)**: independently controls the ramp servo and DFPlayer Mini.

## Audio

There are two separate audio systems:

1. **Kiosk audio:** browser Web Speech API → Chromium → Raspberry Pi audio output.
2. **Bus audio:** prerecorded MP3 → DFPlayer Mini → bus-side speaker.

Kiosk speech is provided in English, Chinese, Malay and Tamil where the corresponding browser TTS voice is available. The UI remains visual even if a TTS voice is unavailable.

Bus-side MP3 tracks are documented in `bus/README.md`:

- Track 1 — general boarding announcement
- Track 2 — ramp ready
- Track 3 — general alighting announcement
- Track 4 — ramp retracting

The bus announcements use general wording and do not identify the passenger or their specific assistance need.

## Raspberry Pi serial port

The Raspberry Pi kiosk connects to Pico #1 for the physical selection buttons. The installed systemd service uses:

```bash
PICO_PORT=/dev/ttyACM0
```

If the kiosk Pico receives a different path, override it when running the installer:

```bash
PICO_PORT=/dev/ttyACM0 ./install.sh
```

The separate bus Pico is not required to be connected to the kiosk Raspberry Pi.

## Install on Raspberry Pi 5

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer installs Chromium and the Python dependencies, enables SPI, adds the runtime user to `dialout`, creates the Python virtual environment, configures the kiosk hardware bridge as a system service and launches `index.html` directly in Chromium kiosk mode.

## Register an NFC card

After the PN532 is connected and detects a card, register it with:

```bash
./.venv/bin/python kiosk/register_card.py
```

The registration utility stores the card UID, user's name and additional-assistance profile in the local SQLite database. Profiles include disability-related needs as well as pregnancy and parent-with-stroller assistance.

## Bus-side setup

See `bus/README.md` for:

- Pico #2 wiring
- servo power requirements
- DFPlayer Mini wiring
- microSD audio files
- serial commands
- bus-side demo testing

The bus-side Pico accepts commands including:

```text
BOARD
ALIGHT
RETRACT
RESET
STATUS
TEST_AUDIO_1
TEST_AUDIO_2
TEST_AUDIO_3
TEST_AUDIO_4
```

The `BOARD` sequence is a bus-side action. It is not automatically triggered by the kiosk session.

## Prototype limitations / final testing

Before demonstrating the complete physical prototype, test the following on the actual hardware:

- PN532 NFC detection and registered-card lookup
- kiosk Pico USB serial connection
- Chromium Web Speech voices for all required languages
- Raspberry Pi speaker output after cold boot
- kiosk physical-button selection and confirmation
- kiosk session ending after arrival information
- bus-side DFPlayer playback and MP3 track timing
- servo ramp angle calibration (`RAMP_UP` / `RAMP_DOWN`)
- safe external power and common ground for the bus-side servo
- separate bus-side BOARD / ALIGHT operation

This is a prototype. The servo/ramp mechanism should be treated as a tabletop demonstration rather than a production passenger-safety system.

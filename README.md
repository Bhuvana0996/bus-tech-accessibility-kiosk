# Bus Tech Accessibility Kiosk

Accessibility transport kiosk prototype for a 7-inch 1024×600 LCD, PN532 NFC reader, two Raspberry Pi Picos, physical bus controls, ramp servo and audio guidance.

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
Choose Bus 191 or Bus 400 using physical buttons
  ↓
🔊 Bus selection instruction
  ↓
Press the same button again to confirm
  ↓
Arrival information
  ↓
🔊 Kiosk arrival announcement
  ↓
Bus-side Pico can deploy the ramp + play public boarding announcement
  ↓
Session ends → Home
```

**Privacy/accessibility rule:** the passenger's specific accessibility needs are displayed visually but are **never spoken aloud**. Audio is used for navigation and general instructions only. Bus-side announcements also use general wording and do not identify the passenger's specific needs.

## Hardware architecture

### Kiosk side

- **Raspberry Pi 5** — main computer, local web server and hardware bridge
- **7-inch 1024×600 LCD** — visual interface
- **PN532 V4** — NFC reader over SPI
- **Pico #1** — reads the physical Bus 191 / Bus 400 selection buttons over USB serial
- **Kiosk speaker** — Chromium Web Speech API through the Pi's default audio output

### Bus side

- **Pico #2** — controls the model-bus ramp and DFPlayer Mini
- **Servo motor** — deploys/retracts the wheelchair ramp
- **DFPlayer Mini + microSD** — plays prerecorded public announcements
- **Bus-side speaker** — connected to the DFPlayer Mini
- **BOARD / ALIGHT buttons** — optional physical demo controls on the bus-side Pico

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
├── index.html              # Main kiosk UI, flow, translations and browser speech
├── kiosk.html              # Hardware-connected browser bridge wrapper
├── install.sh              # Raspberry Pi setup + kiosk autostart
├── requirements.txt        # Python backend dependencies
├── README.md               # Project overview
├── README-HARDWARE.md      # Hardware wiring and setup guide
├── kiosk/
│   ├── main.py             # WebSocket server + NFC/Pico/bus event bridge
│   ├── nfc.py              # PN532 SPI reader
│   ├── pico.py             # Kiosk Pico USB serial reader
│   ├── bus.py              # Bus-side Pico USB serial controller
│   ├── database.py         # SQLite registered-card database
│   └── register_card.py    # NFC card registration utility
├── pico/
│   └── main.py             # Pico #1 kiosk button firmware
└── bus/
    ├── README.md            # Bus-side setup and audio guide
    └── pico/
        └── main.py         # Pico #2 ramp + DFPlayer firmware
```

## Why there are two HTML files

`index.html` contains the actual kiosk experience and can be opened directly for UI/demo testing.

`kiosk.html` is the hardware-connected entry point. It loads `index.html` and connects it to the Raspberry Pi backend through WebSocket events. The Raspberry Pi should launch `kiosk.html`, not the plain `index.html`, when running the physical prototype.

## Software responsibilities

- **Browser (`index.html`)**: screen flow, language switching, visual accessibility profile, bus selection UI, countdown and speech.
- **Hardware bridge (`kiosk/main.py`)**: receives PN532 and kiosk-Pico events, forwards them to the browser and sends bus commands to the bus-side Pico.
- **NFC (`kiosk/nfc.py`)**: reads PN532 cards over SPI.
- **Kiosk Pico (`kiosk/pico.py`)**: reads `BUTTON1` / `BUTTON2` from Pico #1.
- **Bus controller (`kiosk/bus.py`)**: sends commands such as `BOARD`, `ALIGHT` and `RETRACT` to Pico #2.
- **Database (`kiosk/database.py`)**: maps NFC UID → user name + accessibility profile.
- **Registration (`kiosk/register_card.py`)**: adds cards to the SQLite database.
- **Kiosk Pico firmware (`pico/main.py`)**: GP14 → Bus 191 and GP15 → Bus 400.
- **Bus Pico firmware (`bus/pico/main.py`)**: controls the ramp servo and DFPlayer Mini.

## Audio

There are two separate audio systems:

1. **Kiosk audio:** browser Web Speech API → Chromium → Raspberry Pi audio output.
2. **Bus audio:** prerecorded MP3 → DFPlayer Mini → bus-side speaker.

Kiosk speech is provided in English, Chinese, Malay and Tamil where the corresponding browser TTS voice is available. The UI remains visual even if a TTS voice is unavailable.

Bus-side MP3 tracks are documented in `bus/README.md`:

- Track 1 — boarding announcement
- Track 2 — ramp ready
- Track 3 — alighting announcement
- Track 4 — ramp retracting

## Raspberry Pi serial ports

The Raspberry Pi connects to two separate Picos. The installed systemd service uses explicit serial-port environment variables:

```bash
PICO_PORT=/dev/ttyACM0
BUS_PICO_PORT=/dev/ttyACM1
```

If the devices receive different paths on your Raspberry Pi, override them when running the installer:

```bash
PICO_PORT=/dev/ttyACM0 BUS_PICO_PORT=/dev/ttyACM1 ./install.sh
```

For a stable physical deployment, verify the assigned device paths before installation/testing.

## Install on Raspberry Pi 5

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer installs Chromium and the Python dependencies, enables SPI, adds the runtime user to `dialout`, creates the Python virtual environment, configures the hardware bridge as a system service and launches `kiosk.html` in Chromium kiosk mode.

The system service is configured with `PICO_PORT` and `BUS_PICO_PORT` so the two Picos are not confused.

## Register an NFC card

After the PN532 is connected and detects a card, register it with:

```bash
./.venv/bin/python kiosk/register_card.py
```

The registration utility stores the card UID, user's name and accessibility profile in the local SQLite database.

## Bus-side setup

See `bus/README.md` for:

- Pico #2 wiring
- servo power requirements
- DFPlayer Mini wiring
- microSD audio files
- serial commands
- bus-side demo testing

The bus Pico accepts commands including:

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

## Prototype limitations / final testing

Before demonstrating the complete physical prototype, test the following on the actual Raspberry Pi and hardware:

- PN532 NFC detection and registered-card lookup
- both Pico USB serial connections
- Chromium Web Speech voices for all required languages
- Raspberry Pi speaker output after cold boot
- kiosk physical-button selection and confirmation
- bus-side DFPlayer playback and MP3 track timing
- servo ramp angle calibration (`RAMP_UP` / `RAMP_DOWN`)
- safe external power and common ground for the bus-side servo
- full end-to-end flow from NFC tap → bus confirmation → bus-side ramp command

This is a prototype. The servo/ramp mechanism should be treated as a tabletop demonstration rather than a production passenger-safety system.

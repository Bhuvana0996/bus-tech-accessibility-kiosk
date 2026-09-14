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

The current kiosk interface and kiosk speech are **English-only** for the prototype.

## System flow

```text
Welcome screen
  ↓
Tap registered NFC card
  ↓
Card recognised
  ↓
Registered additional-assistance needs shown ON SCREEN
  ↓
Kiosk TTS: general greeting + instruction to choose a bus
  ↓
Choose Bus 191 or Bus 400 using physical buttons
  ↓
Kiosk TTS: bus selection instruction
  ↓
Press the same button again to confirm
  ↓
Arrival information shown + spoken by kiosk TTS
  ↓
Kiosk session ends automatically
```

There is **no separate Start screen or Start button**. The Welcome screen leads directly to NFC identification.

If a required kiosk component is unavailable, the interface enters an explicit **System temporarily unavailable** safe state instead of continuing as though the hardware were working.

**Privacy rule:** the passenger's specific assistance needs are displayed visually but are **never spoken aloud**. Kiosk audio is used for navigation and general instructions only.

## Two separate audio systems

The prototype has two physically separate speakers/audio systems:

```text
KIOSK SIDE
Raspberry Pi 5
   ↓
Audio output / suitable interface
   ↓
Amplifier (if required)
   ↓
66FR 8 Ω 0.5 W kiosk speaker
   ↑
Browser Web Speech API / English TTS

BUS SIDE
Pico #2
   ↓
DFPlayer Mini
   ↓
External bus-side speaker
```

The Raspberry Pi 5 does not have a built-in speaker or 3.5 mm analog audio jack, so the kiosk uses an external speaker connected through a supported Pi audio output/interface. The 66FR kiosk speaker is rated **8 Ω, 0.5 W** and should be connected through a suitable audio interface/amplifier rather than directly to a GPIO pin.

The browser's kiosk speech is currently **English (`en-SG`) only**.

The bus uses its own independent speaker. Pico #2 drives a DFPlayer Mini, which plays TTS-generated MP3 announcement files from the DFPlayer microSD card.

## Fail-safe behavior

### Kiosk side

The Raspberry Pi backend continuously reports the health of:

- **PN532 NFC reader**
- **Pico #1 USB button controller**

The browser checks that state before allowing the related step to continue.

```text
NFC reader unavailable
        ↓
System temporarily unavailable
        ↓
Card processing disabled
        ↓
Automatic reconnect/recovery attempt
```

```text
Pico #1 unavailable
        ↓
System temporarily unavailable
        ↓
Bus selection/confirmation disabled
        ↓
Automatic reconnect/recovery attempt
```

If the Raspberry Pi WebSocket backend disconnects or fails to appear, the browser also enters the safe state and retries the connection automatically.

### Bus side

The bus-side ramp controller uses a stricter rule for automatic movement:

```text
BOARD / ALIGHT
      ↓
30-second delay
      ↓
Play public announcement
      ↓
DFPlayer BUSY confirms audio started
      ↓
DFPlayer BUSY confirms audio finished
      ↓
Only then may the ramp deploy
```

If DFPlayer BUSY is not wired, the controller **does not automatically deploy or retract the ramp** during BOARD / ALIGHT / RETRACT sequences. Invalid commands are ignored and servo errors stop the affected sequence.

This is prototype-level fail-safe logic intended to prevent an unverified audio state from triggering automatic ramp movement. It is not a production passenger-safety system.

## Important separation: kiosk vs bus system

The kiosk and bus-side assistance system are separate physical subsystems.

The kiosk handles passenger identification, visual assistance information, bus selection and arrival information. It does not publicly announce the passenger's specific assistance needs.

The separate bus-side Pico controls the physical ramp and public bus announcements. A ramp should only be deployed when ramp assistance is actually required. For example, a wheelchair user or parent with a stroller may require the ramp, while a pregnant passenger may require priority assistance without needing the ramp.

There are **no physical BOARD / ALIGHT buttons** on Bus Pico #2. The bus controller receives its `BOARD`, `ALIGHT` or `RETRACT` control signal through its serial/control interface for the prototype.

## Hardware architecture

### Kiosk side

- **Raspberry Pi 5** — main computer, local web server and kiosk hardware bridge
- **7-inch 1024×600 LCD** — visual interface
- **PN532 V4** — NFC reader over SPI
- **Pico #1** — reads the physical Bus 191 / Bus 400 selection buttons over USB serial
- **66FR speaker — 8 Ω, 0.5 W** — kiosk English TTS/navigation audio; use a suitable audio interface/amplifier

### Bus side — separate system

- **Pico #2** — ramp/audio controller
- **Servo motor** — deploys/retracts the model-bus ramp when assistance requires it
- **DFPlayer Mini** — plays TTS-generated MP3 announcements
- **DFPlayer microSD** — stores four announcement recordings
- **External bus-side speaker** — connected to DFPlayer
- **DFPlayer BUSY signal on GP15** — required for automatic fail-safe ramp movement

## Physical controls and connections

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
| GP5 / UART1 RX | DFPlayer TX | DFPlayer communication |
| GP15 | DFPlayer BUSY | Required to confirm audio playback before automatic ramp movement |
| GND | Common GND | Common reference |

There are no BOARD / ALIGHT buttons on Pico #2.

## Project structure

```text
bus-tech-accessibility-kiosk/
├── index.html              # Main English-only kiosk UI, speech and WebSocket bridge
├── install.sh              # Raspberry Pi setup + kiosk autostart
├── requirements.txt        # Python backend dependencies
├── README.md               # Project overview
├── README-HARDWARE.md      # Hardware wiring and setup guide
├── kiosk/
│   ├── main.py             # WebSocket server + NFC/Pico event bridge + health monitoring
│   ├── nfc.py              # PN532 SPI reader
│   ├── pico.py             # Kiosk Pico USB serial reader
│   ├── database.py         # SQLite registered-card database
│   └── register_card.py    # NFC card registration utility
├── pico/
│   └── main.py             # Pico #1 kiosk button firmware
└── bus/
    ├── README.md            # Separate bus-side setup and audio guide
    └── pico/
        └── main.py         # Pico #2 ramp + DFPlayer firmware + fail-safe checks
```

## Software responsibilities

- **Browser (`index.html`)**: screen flow, English kiosk UI, visual assistance profile, bus selection UI, English kiosk TTS and hardware fail-safe state.
- **Hardware bridge (`kiosk/main.py`)**: receives PN532 and kiosk-Pico events, forwards them to the browser and reports hardware health.
- **NFC (`kiosk/nfc.py`)**: reads PN532 cards over SPI.
- **Kiosk Pico (`kiosk/pico.py`)**: reads `BUTTON1` / `BUTTON2` from Pico #1.
- **Database (`kiosk/database.py`)**: maps NFC UID → user name + additional-assistance profile.
- **Registration (`kiosk/register_card.py`)**: adds cards to the SQLite database.
- **Kiosk Pico firmware (`pico/main.py`)**: GP14 → Bus 191 and GP15 → Bus 400.
- **Bus Pico firmware (`bus/pico/main.py`)**: controls the ramp servo and DFPlayer audio sequence independently and blocks automatic ramp movement when audio completion cannot be verified.

## Audio

### Kiosk audio

Kiosk audio is generated by the browser's Web Speech API/TTS and sent to the external 66FR kiosk speaker through the Raspberry Pi's configured audio output/interface. The kiosk prototype currently uses **English (`en-SG`) only**.

The kiosk does not speak the passenger's specific assistance needs.

### Bus audio

The bus Pico uses a DFPlayer Mini and a separate bus-side speaker. The public announcements are **generated in advance using TTS**, exported as MP3 files and stored on the DFPlayer microSD card.

The bus announcements are:

- Track 1 — general boarding announcement
- Track 2 — ramp ready
- Track 3 — general alighting announcement
- Track 4 — ramp retracting

Files expected by the firmware:

```text
0001.mp3
0002.mp3
0003.mp3
0004.mp3
```

The announcements use general wording and do not identify the passenger or their specific assistance need.

## Bus sequence timing

### Boarding

```text
BOARD signal received
        ↓
WAIT 30 seconds
        ↓
TTS Track 1 — boarding announcement
        ↓
DFPlayer BUSY confirms finish
        ↓
Ramp deploys
        ↓
TTS Track 2 — ramp ready
```

### Alighting

```text
ALIGHT signal received
        ↓
WAIT 30 seconds
        ↓
TTS Track 3 — alighting announcement
        ↓
DFPlayer BUSY confirms finish
        ↓
Ramp deploys
        ↓
TTS Track 2 — ramp ready
```

### Retracting

```text
RETRACT signal received
        ↓
TTS Track 4 — retracting announcement
        ↓
DFPlayer BUSY confirms finish
        ↓
Ramp retracts
```

The **30-second delay is before the boarding/alighting announcement**, not after it.

## Raspberry Pi audio

The Raspberry Pi 5 uses the **66FR 8 Ω, 0.5 W** speaker for kiosk TTS. Use a suitable supported audio output/interface and amplifier where required by the speaker setup. Do not connect the speaker directly to a Raspberry Pi GPIO pin.

The bus speaker is completely separate and is connected to the DFPlayer on Pico #2.

## Raspberry Pi serial port

The Raspberry Pi kiosk connects to Pico #1 for the physical selection buttons. The installed systemd service uses:

```bash
PICO_PORT=/dev/ttyACM0
```

If the kiosk Pico receives a different path, override it when running the installer:

```bash
PICO_PORT=/dev/ttyACM0 ./install.sh
```

Pico #2 is a separate bus-side subsystem and does not need to share the kiosk's USB connection.

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
- DFPlayer + separate speaker wiring
- TTS MP3 file preparation
- required DFPlayer BUSY wiring for automatic ramp movement
- serial commands
- bus-side demo testing

The bus-side Pico accepts:

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

Before demonstrating the complete physical prototype, test the following on the actual hardware:

- PN532 NFC detection and registered-card lookup
- kiosk Pico USB serial connection
- external 66FR kiosk speaker output after cold boot
- English kiosk TTS output (`en-SG`)
- kiosk physical-button selection and confirmation
- kiosk backend health/fault state by disconnecting the NFC reader and Pico #1
- kiosk session ending after arrival information
- DFPlayer TTS recordings and bus speaker volume
- DFPlayer BUSY playback-finished detection
- 30-second bus-side delay
- correct announcement → ramp deployment order
- automatic ramp movement remains disabled when DFPlayer BUSY is disconnected
- servo ramp angle calibration (`RAMP_UP` / `RAMP_DOWN`)
- safe external power and common ground for the bus-side servo
- separate BOARD / ALIGHT / RETRACT control

This is a prototype. The servo/ramp mechanism should be treated as a tabletop demonstration rather than a production passenger-safety system.

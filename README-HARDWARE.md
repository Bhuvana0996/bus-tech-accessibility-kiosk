# Accessibility Kiosk — Raspberry Pi 5 Hardware Setup

This repository uses a Raspberry Pi 5 as the main computer. The prototype has two separate Raspberry Pi Picos: one for the kiosk-side physical bus buttons and one for the bus-side ramp/audio controller.

## Architecture

```text
                         KIOSK SIDE

PN532 NFC ──SPI──────────────┐
                             │
Pico #1 buttons ──USB────────┤
                             ↓
                        Raspberry Pi 5
                             │
                             ├── WebSocket → kiosk.html → index.html
                             │                       │
                             │                       ├── 7-inch LCD
                             │                       └── Kiosk speaker
                             │
                             └── USB serial → Pico #2
                                               │
                         BUS SIDE              ├── Servo → ramp
                                               └── DFPlayer → speaker
```

The browser owns the user-facing flow. Python bridges the physical hardware to the browser and sends bus-side commands to Pico #2.

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

## Pico #1 — kiosk physical bus buttons

Pico #1 connects to the Raspberry Pi over USB serial.

| Pico GPIO | Function |
|---|---|
| GP14 → GND | Button 1 → Bus 191 |
| GP15 → GND | Button 2 → Bus 400 |

The Pico firmware uses internal pull-ups, so no external pull-up resistor is required.

Flash `pico/main.py` to Pico #1 as `main.py`.

The kiosk uses the same button again to confirm the selected bus. Pressing the other button changes the selection.

## Pico #2 — bus-side ramp and audio controller

Pico #2 is the separate Pico mounted on/with the model bus.

| Pico GPIO | Device | Function |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer response |
| GP14 | BOARD button → GND | Demo boarding sequence |
| GP15 | ALIGHT button → GND | Demo alighting sequence |

Flash `bus/pico/main.py` to Pico #2 as `main.py`.

### Servo power

Do **not** assume the Raspberry Pi Pico can safely power the servo. Use a suitable external 5 V supply when required by the servo's current rating. Connect the servo supply ground, Pico ground and DFPlayer ground together.

Calibrate the ramp endpoints in `bus/pico/main.py`:

```python
RAMP_UP = 10
RAMP_DOWN = 95
```

These values are prototype-specific and should be adjusted to the actual ramp mechanism and servo.

## DFPlayer Mini + bus speaker

The bus-side Pico uses a DFPlayer Mini because prerecorded public announcements are stored as MP3 files on a microSD card.

Use four short recordings:

1. **Track 1 — boarding**
   "Attention passengers. A passenger requiring additional assistance will be boarding. Please give up the priority seat and allow sufficient space for the passenger to board safely. Thank you."
2. **Track 2 — ramp ready**
   "The ramp is ready. Please proceed when safe."
3. **Track 3 — alighting**
   "Attention passengers. A passenger requiring additional assistance will be alighting. Please keep the priority area clear and allow the passenger to alight safely. Thank you."
4. **Track 4 — retracting**
   "The ramp is retracting. Please keep clear."

Do not record or announce the passenger's specific accessibility needs. The public announcement intentionally uses general wording.

The current firmware uses short fixed delays between audio and ramp actions, so the MP3 recordings should be kept consistent with the expected demo timing. For a production system, use a proper playback-status/interlock mechanism rather than relying only on fixed delays.

## Raspberry Pi USB serial ports

The Raspberry Pi communicates with both Picos over USB serial. The default installation uses:

```bash
PICO_PORT=/dev/ttyACM0
BUS_PICO_PORT=/dev/ttyACM1
```

The installer writes these values into the systemd service. If your Raspberry Pi assigns different device paths, override them during installation:

```bash
PICO_PORT=/dev/ttyACM0 BUS_PICO_PORT=/dev/ttyACM1 ./install.sh
```

Check the actual device paths with the Picos connected before testing. For a production deployment, stable udev device names are preferable to relying on `ttyACM0` / `ttyACM1` numbering.

## Kiosk speaker

The kiosk uses the browser's Web Speech API for spoken guidance. Chromium sends the speech output through the Raspberry Pi's default audio device/speaker.

Audio follows the same user flow as the UI:

- language selected → language instruction
- NFC recognised → general greeting/instruction
- bus selected → selection instruction
- bus confirmed → arrival announcement

The user's accessibility needs are **displayed visually only** and are never spoken aloud.

The browser must have the required TTS voices available for the selected language. Verify English, Chinese, Malay and Tamil on the actual Raspberry Pi because available voices depend on the Chromium/OS environment.

## Install

```bash
cd ~/bus-tech-accessibility-kiosk
chmod +x install.sh
./install.sh
```

The installer:

1. installs Chromium and Python dependencies;
2. enables SPI;
3. adds the runtime user to `dialout`;
4. creates the Python virtual environment;
5. installs the PN532 and serial libraries;
6. configures the hardware bridge as a system service;
7. explicitly assigns the kiosk Pico and bus Pico serial ports;
8. launches `kiosk.html` in Chromium kiosk mode.

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
7. Pico #1 Button 1 = Bus 191
   Pico #1 Button 2 = Bus 400
       ↓
8. Same button again = confirm
   Other button = change selection
       ↓
9. Browser displays arrival information + speaks announcement
       ↓
10. Python sends BOARD to Pico #2
       ↓
11. Pico #2 plays boarding announcement and deploys ramp
       ↓
12. Bus-side ALIGHT button can demonstrate alighting
       ↓
13. RETRACT can return the ramp to its upper/home position
```

## Bus-side serial commands

Pico #2 accepts:

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

The physical BOARD and ALIGHT buttons also trigger their respective demo sequences.

## Final hardware checks

Before the complete physical demonstration, verify:

- PN532 detects the intended NFC card reliably;
- Pico #1 and Pico #2 appear on the expected USB serial ports;
- the systemd service has the correct `PICO_PORT` and `BUS_PICO_PORT` values;
- Chromium speech works after a cold boot;
- required TTS voices are available;
- both physical kiosk buttons select/confirm the correct bus;
- DFPlayer tracks play correctly and at the expected timing;
- servo endpoints do not mechanically overtravel the ramp;
- servo has appropriate external power and common ground;
- BOARD reaches Pico #2 and triggers the intended ramp/audio sequence;
- ALIGHT and RETRACT work correctly;
- pressing Home during the kiosk flow leaves the kiosk at a clean new session.

This is a prototype. The ramp/servo mechanism is for tabletop demonstration and should not be treated as a production passenger-safety system.

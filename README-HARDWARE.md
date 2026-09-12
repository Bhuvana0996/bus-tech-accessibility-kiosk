# Accessibility Kiosk — Raspberry Pi 5 Hardware Setup

This repository uses a Raspberry Pi 5 as the main kiosk computer. The prototype has two separate Raspberry Pi Picos: one for the kiosk-side physical bus buttons and one for the independent bus-side ramp/audio controller.

## Architecture

```text
                         KIOSK SIDE

PN532 NFC ──SPI──────────────┐
                             │
Pico #1 buttons ──USB────────┤
                             ↓
                        Raspberry Pi 5
                             │
                             ├── WebSocket → index.html
                             │                       │
                             │                       ├── 7-inch LCD
                             │                       └── Kiosk speaker
                             │
                             └── kiosk session ends after arrival information

                         BUS SIDE — SEPARATE

                  Pico #2
                    │
              ┌─────┴─────┐
              ↓           ↓
          Servo/ramp   DFPlayer → bus speaker
```

The browser owns the user-facing flow. Python bridges the PN532 and kiosk Pico to the browser. The bus-side Pico is independent and does not receive passenger names or specific assistance needs from the kiosk.

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

## Pico #2 — separate bus-side ramp and audio controller

Pico #2 is the separate Pico mounted on/with the model bus. It is independent of the kiosk session.

| Pico GPIO | Device | Function |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer response |
| GP14 | BOARD button → GND | Demo boarding sequence |
| GP15 | ALIGHT button → GND | Demo alighting sequence |

Flash `bus/pico/main.py` to Pico #2 as `main.py`.

### When is the ramp used?

The ramp is **not** automatically deployed for every assistance profile.

Examples:

- Wheelchair user → ramp may be required
- Parent with stroller → ramp may be required
- Mobility aid / crutches → ramp may be required depending on the situation
- Pregnant passenger → assistance may be needed without a ramp
- Blind / low-vision passenger → assistance may be needed without a ramp
- Deaf / hard-of-hearing passenger → visual communication may be needed without a ramp

For the prototype, the bus-side BOARD control is used separately when ramp assistance is actually required.

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

Do not record or announce the passenger's specific assistance needs. The public announcement intentionally uses general wording.

The current firmware uses short fixed delays between audio and ramp actions, so the MP3 recordings should be kept consistent with the expected demo timing. For a production system, use a proper playback-status/interlock mechanism rather than relying only on fixed delays.

## Kiosk speaker

The kiosk uses the browser's Web Speech API for spoken guidance. Chromium sends the speech output through the Raspberry Pi's default audio device/speaker.

Audio follows the kiosk flow:

- language selected → language instruction
- NFC recognised → general greeting/instruction
- bus selected → selection instruction
- bus confirmed → arrival information
- after arrival information → kiosk session ends automatically

The user's specific assistance needs are **displayed visually only** and are never spoken aloud.

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
6. configures the kiosk hardware bridge as a system service;
7. assigns the kiosk Pico serial port;
8. launches `index.html` directly in Chromium kiosk mode.

## Register an NFC card

Run:

```bash
./.venv/bin/python kiosk/register_card.py
```

Enter the NFC UID, user's name and additional-assistance profile. Profiles include wheelchair users, parents with strollers, pregnant passengers, mobility-aid users, sensory-access needs and multiple/other needs.

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
5. Registered → browser shows assistance profile visually
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
10. Kiosk session ends automatically

Separately:

Bus arrives → bus-side Pico is operated independently
       ↓
If ramp assistance is required → BOARD sequence
       ↓
DFPlayer plays general announcement + servo deploys ramp
       ↓
ALIGHT / RETRACT can be operated separately
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
- Pico #1 appears on the expected USB serial port;
- Chromium speech works after a cold boot;
- required TTS voices are available;
- both physical kiosk buttons select/confirm the correct bus;
- the kiosk ends the passenger session after arrival information;
- DFPlayer tracks play correctly and at the expected timing;
- servo endpoints do not mechanically overtravel the ramp;
- servo has appropriate external power and common ground;
- bus-side BOARD / ALIGHT / RETRACT work independently;
- pressing Home during the kiosk flow leaves the kiosk at a clean new session.

This is a prototype. The ramp/servo mechanism is for tabletop demonstration and should not be treated as a production passenger-safety system.

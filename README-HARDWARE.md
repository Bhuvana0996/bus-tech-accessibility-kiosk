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
                             │                       └── External kiosk speaker
                             │                              ↑
                             │                         Browser TTS
                             │
                             └── kiosk session ends after arrival information

                         BUS SIDE — SEPARATE

                  Pico #2
                    │
              ┌─────┴─────┐
              ↓           ↓
          Servo/ramp   DFPlayer Mini
                            │
                       External bus speaker
                            ↑
                    TTS-generated MP3s
```

The browser owns the user-facing kiosk flow. Python bridges the PN532 and kiosk Pico to the browser. The bus-side Pico is a separate subsystem and does not receive passenger names or specific assistance needs through the public audio.

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

## Kiosk external speaker

The Raspberry Pi 5 does not have a built-in speaker. The kiosk therefore uses a separate external speaker connected through a suitable supported audio output/interface.

The browser's Web Speech API provides the kiosk TTS. Chromium sends that audio to the configured Raspberry Pi audio output.

Possible speaker arrangements include:

- powered USB speaker;
- HDMI audio to a display/speaker system;
- Bluetooth speaker;
- suitable USB/I2S audio interface + amplifier + speaker.

Choose the actual option based on the speaker available for the prototype.

## Pico #2 — separate bus-side ramp and audio controller

Pico #2 is mounted on/with the model bus and is independent of the kiosk session.

| Pico GPIO | Device | Function |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer communication |
| GP15 | DFPlayer BUSY | Detect when announcement has finished |
| GND | Common GND | Common reference |

There are **no physical BOARD / ALIGHT buttons** on Pico #2.

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

The bus-side control sequence is only started when ramp assistance is actually required.

### Servo power

Do **not** assume the Raspberry Pi Pico can safely power the servo. Use a suitable external 5 V supply when required by the servo's current rating. Connect the servo supply ground and Pico ground together.

Calibrate the ramp endpoints in `bus/pico/main.py`:

```python
RAMP_UP = 10
RAMP_DOWN = 95
```

These values are prototype-specific and should be adjusted to the actual ramp mechanism and servo.

## DFPlayer Mini + separate bus speaker

The bus-side Pico uses a DFPlayer Mini so that the bus has its own independent audio system.

The four announcements are generated using TTS in advance and exported as MP3 files. The MP3 files are stored on the DFPlayer microSD card.

Recommended wiring:

```text
Pico GP4 (TX)  → DFPlayer RX
Pico GP5 (RX)  ← DFPlayer TX
Pico GP15      ← DFPlayer BUSY
Pico GND       ── DFPlayer GND

DFPlayer speaker output → separate bus-side speaker
```

If the speaker requires more power than the DFPlayer can provide, use an appropriate amplifier between the DFPlayer audio output and the speaker.

### TTS announcements

1. **Track 1 — boarding**
   "Attention passengers. A passenger requiring additional assistance will be boarding. Please give up the priority seat and allow sufficient space for the passenger to board safely. Thank you."
2. **Track 2 — ramp ready**
   "The ramp is ready. Please proceed when safe."
3. **Track 3 — alighting**
   "Attention passengers. A passenger requiring additional assistance will be alighting. Please keep the priority area clear and allow the passenger to alight safely. Thank you."
4. **Track 4 — retracting**
   "The ramp is retracting. Please keep clear."

Do not record or announce the passenger's specific accessibility needs.

Store the files on the DFPlayer microSD as:

```text
01.mp3
02.mp3
03.mp3
04.mp3
```

The exact TTS voice can be chosen when generating the recordings. Keep the wording consistent for the demonstration.

### Playback-finished detection

DFPlayer BUSY is recommended because the ramp should deploy **only after the boarding/alighting announcement has finished**.

If GP15 is not wired, the firmware uses fallback timing values. BUSY is preferred for the physical prototype because the actual TTS recording length can vary.

## Bus-side runtime flow

### Boarding

```text
BOARD signal
     ↓
Wait 30 seconds
     ↓
Play TTS Track 1
     ↓
Wait for announcement to finish
     ↓
Deploy ramp
     ↓
Play TTS Track 2
     ↓
Passenger boards
```

### Alighting

```text
ALIGHT signal
     ↓
Wait 30 seconds
     ↓
Play TTS Track 3
     ↓
Wait for announcement to finish
     ↓
Deploy ramp
     ↓
Play TTS Track 2
     ↓
Passenger alights
```

### Retracting

```text
RETRACT signal
     ↓
Play TTS Track 4
     ↓
Wait for announcement to finish
     ↓
Retract ramp
```

The **30-second delay is before the boarding/alighting announcement**.

## Kiosk speaker and bus speaker are separate

```text
Raspberry Pi 5 → external kiosk speaker
                         ↓
                    kiosk TTS

Pico #2 → DFPlayer → external bus speaker
                         ↓
                  bus TTS MP3s
```

These audio systems do not share a speaker.

## Kiosk runtime flow

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
9. Browser displays arrival information + speaks it
       ↓
10. Kiosk session ends automatically

Separately:

Bus-side control signal
       ↓
Pico #2
       ↓
If ramp assistance is required → BOARD / ALIGHT sequence
       ↓
30-second delay
       ↓
General TTS announcement
       ↓
Announcement finishes
       ↓
Ramp deploys
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

There are no physical BOARD / ALIGHT buttons.

## Final hardware checks

Before the complete physical demonstration, verify:

- PN532 detects the intended NFC card reliably;
- Pico #1 appears on the expected USB serial port;
- external kiosk speaker works after a cold boot;
- required kiosk TTS voices are available;
- both physical kiosk buttons select/confirm the correct bus;
- the kiosk ends the passenger session after arrival information;
- DFPlayer plays all four TTS-generated MP3s correctly;
- bus speaker volume is clear in the demonstration environment;
- DFPlayer BUSY correctly indicates playback completion;
- 30-second bus-side delay occurs before the boarding/alighting announcement;
- ramp deploys only after the announcement finishes;
- ramp-ready announcement plays after deployment;
- servo endpoints do not mechanically overtravel the ramp;
- servo has appropriate external power and common ground;
- BOARD / ALIGHT / RETRACT control works independently;
- Home during the kiosk flow leaves the kiosk at a clean new session.

This is a prototype. The ramp/servo mechanism is for tabletop demonstration and should not be treated as a production passenger-safety system.

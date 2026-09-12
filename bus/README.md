# Bus-side ramp and announcement controller

This is the separate second Pico used on the model bus. It controls the ramp servo and the bus-side audio system independently of the Accessibility Kiosk.

## Hardware

- Raspberry Pi Pico (#2)
- Servo motor for the ramp
- DFPlayer Mini
- microSD card in the DFPlayer containing TTS-generated MP3 announcements
- Bus-side speaker connected to the DFPlayer Mini
- Optional DFPlayer BUSY connection for accurate playback-finished detection

There are **no physical BOARD / ALIGHT buttons** on the bus Pico.

## Assistance logic

The ramp is **not** deployed for every assistance profile.

Examples:

- Wheelchair user → ramp may be required
- Parent with stroller → ramp may be required
- Mobility aid / crutches → ramp may be required depending on the situation
- Pregnant passenger → additional assistance may be needed, but a ramp is not automatically required
- Blind / low-vision passenger → assistance may be needed, but a ramp is not automatically required
- Deaf / hard-of-hearing passenger → visual communication may be required, but a ramp is not automatically required

The bus controller does not receive the passenger's name or specific assistance profile through the public audio system.

## Audio approach

The bus Pico does not perform live cloud TTS itself. Instead, the four public announcements are created using TTS in advance and saved as MP3 files on the DFPlayer microSD card.

This gives the prototype:

- natural speech without requiring an internet connection on the bus;
- a separate physical bus speaker;
- consistent announcement wording;
- no passenger-specific information in the public announcement.

The four recordings are:

1. **Track 1 — boarding**
   "Attention passengers. A passenger requiring additional assistance will be boarding. Please give up the priority seat and allow sufficient space for the passenger to board safely. Thank you."
2. **Track 2 — ramp ready**
   "The ramp is ready. Please proceed when safe."
3. **Track 3 — alighting**
   "Attention passengers. A passenger requiring additional assistance will be alighting. Please keep the priority area clear and allow the passenger to alight safely. Thank you."
4. **Track 4 — retracting**
   "The ramp is retracting. Please keep clear."

Do not record or announce the passenger's specific accessibility needs.

## Wiring

| Bus-side Pico | Device | Purpose |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer communication |
| GP15 | DFPlayer BUSY | Detect when TTS audio has finished |
| GND | Common GND | Common reference |

The DFPlayer speaker output connects to the separate bus-side speaker. If the speaker requires more power than the DFPlayer can provide, use a suitable amplifier between the DFPlayer audio output and the speaker.

### Servo power

Power the servo from a suitable external 5 V supply if required by its current rating. Do not draw high servo current directly through the Pico. Keep the servo supply ground and Pico ground common.

### DFPlayer BUSY pin

The recommended wiring is:

```text
DFPlayer BUSY → Pico GP15
```

The firmware uses BUSY to detect when an announcement has finished. If GP15 is not wired, the firmware falls back to the durations in `TRACK_FALLBACK_MS` in `bus/pico/main.py`.

## Ramp and announcement sequence

### Boarding

```text
BOARD command received
        ↓
WAIT 30 seconds
        ↓
Play TTS Track 1 — boarding announcement
        ↓
Wait until announcement finishes
        ↓
Deploy ramp
        ↓
Play TTS Track 2 — ramp ready
        ↓
Passenger boards
```

### Alighting

```text
ALIGHT command received
        ↓
WAIT 30 seconds
        ↓
Play TTS Track 3 — alighting announcement
        ↓
Wait until announcement finishes
        ↓
Deploy ramp
        ↓
Play TTS Track 2 — ramp ready
        ↓
Passenger alights
```

### Retracting

```text
RETRACT command received
        ↓
Play TTS Track 4 — ramp retracting
        ↓
Wait until announcement finishes
        ↓
Retract ramp
```

The important timing rule is that the **30-second delay happens first**, before the boarding/alighting announcement. The ramp only deploys after that announcement has completely finished.

## Pico firmware

Copy `bus/pico/main.py` to the bus-side Pico as `main.py` and reset it.

The Pico accepts these serial commands:

- `BOARD` — wait 30 s → boarding announcement → deploy ramp → ramp-ready announcement
- `ALIGHT` — wait 30 s → alighting announcement → deploy ramp → ramp-ready announcement
- `RETRACT` — retract sequence with retracting announcement
- `RESET` — return ramp to the upper/home position
- `STATUS` — report ramp angle and DFPlayer BUSY availability
- `TEST_AUDIO_1` to `TEST_AUDIO_4` — test individual TTS-generated recordings

There are no physical BOARD / ALIGHT buttons.

## Kiosk separation

The Accessibility Kiosk and this bus-side controller remain separate systems.

The kiosk uses its own Raspberry Pi 5 audio output/speaker for kiosk navigation TTS. The bus has its **own separate speaker and audio system** controlled by Pico #2 + DFPlayer.

The kiosk's public-facing UI does not speak the passenger's specific assistance needs. The bus announcements also use only general wording.

## TTS file preparation

Generate the four announcement recordings with the chosen TTS voice before the demonstration. Export them as MP3 files and copy them to the DFPlayer microSD card using the track numbering expected by the firmware:

```text
/01.mp3   → boarding
/02.mp3   → ramp ready
/03.mp3   → alighting
/04.mp3   → retracting
```

Keep the recordings short and clear. Test the actual speaker volume in the demonstration environment.

## Testing

Before connecting the ramp mechanism, test the audio commands:

```text
TEST_AUDIO_1
TEST_AUDIO_2
TEST_AUDIO_3
TEST_AUDIO_4
```

Then test:

```text
RESET
STATUS
BOARD
ALIGHT
RETRACT
```

For the first physical ramp test, keep the servo disconnected or mechanically unloaded so the `RAMP_UP` and `RAMP_DOWN` values can be calibrated safely.

The servo endpoints in `bus/pico/main.py` are prototype values:

```python
RAMP_UP = 10
RAMP_DOWN = 95
```

Adjust them to the actual model ramp.

## Prototype limitation

This is a tabletop demonstration system, not a production passenger-safety controller. The servo mechanism must be mechanically constrained and supervised during testing.

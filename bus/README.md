# Bus-side ramp and announcement controller

This is the separate second Pico used on the model bus. It controls the ramp servo and the bus-side audio system independently of the Accessibility Kiosk.

## Hardware

- Raspberry Pi Pico (#2)
- Servo motor for the ramp
- DFPlayer Mini
- microSD card in the DFPlayer containing TTS-generated MP3 announcements
- Bus-side speaker connected to the DFPlayer Mini
- **DFPlayer BUSY on Pico GP15 — required for automatic fail-safe ramp movement**

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

1. **0001.mp3 — boarding**
   "Attention passengers. A passenger requiring additional assistance will be boarding. Please give up the priority seat and allow sufficient space for the passenger to board safely. Thank you."
2. **0002.mp3 — ramp ready**
   "The ramp is ready. Please proceed when safe."
3. **0003.mp3 — alighting**
   "Attention passengers. A passenger requiring additional assistance will be alighting. Please keep the priority area clear and allow the passenger to alight safely. Thank you."
4. **0004.mp3 — retracting**
   "The ramp is retracting. Please keep clear."

Do not record or announce the passenger's specific accessibility needs.

## Fail-safe rule

Automatic ramp movement is allowed only when the DFPlayer BUSY signal confirms the required announcement started and finished successfully.

```text
BOARD / ALIGHT / RETRACT
        ↓
Play required announcement
        ↓
BUSY confirms playback started
        ↓
BUSY confirms playback finished
        ↓
Only then may the servo move
```

If GP15 / DFPlayer BUSY is not wired, the firmware enters **DISABLED_FAILSAFE** for automatic ramp sequences. It will not guess the announcement duration and will not move the ramp automatically.

This is intentional: losing audio confirmation must not silently trigger ramp movement.

## Wiring

| Bus-side Pico | Device | Purpose |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer communication |
| GP15 | DFPlayer BUSY | Confirm announcement playback before ramp movement |
| GND | Common GND | Common reference |

The DFPlayer speaker output connects to the separate bus-side speaker. If the speaker requires more power than the DFPlayer can provide, use a suitable amplifier between the DFPlayer audio output and the speaker.

### Servo power

Power the servo from a suitable external 5 V supply if required by its current rating. Do not draw high servo current directly through the Pico. Keep the servo supply ground and Pico ground common.

### DFPlayer BUSY pin

Required wiring for automatic fail-safe ramp operation:

```text
DFPlayer BUSY → Pico GP15
```

DFPlayer BUSY should be LOW while the MP3 is playing and return HIGH after playback finishes. The firmware requires both transitions before automatic ramp movement.

## Ramp and announcement sequence

### Boarding

```text
BOARD command received
        ↓
WAIT 30 seconds
        ↓
Play 0001.mp3 — boarding announcement
        ↓
BUSY confirms playback finished
        ↓
Deploy ramp
        ↓
Play 0002.mp3 — ramp ready
```

### Alighting

```text
ALIGHT command received
        ↓
WAIT 30 seconds
        ↓
Play 0003.mp3 — alighting announcement
        ↓
BUSY confirms playback finished
        ↓
Deploy ramp
        ↓
Play 0002.mp3 — ramp ready
```

### Retracting

```text
RETRACT command received
        ↓
Play 0004.mp3 — ramp retracting
        ↓
BUSY confirms playback finished
        ↓
Retract ramp
```

The important timing rule is that the **30-second delay happens first**, before the boarding/alighting announcement. The ramp only deploys after the announcement has completely finished and playback has been confirmed.

## Pico firmware

Copy `bus/pico/main.py` to the bus-side Pico as `main.py` and reset it.

The Pico accepts these serial commands:

- `BOARD` — wait 30 s → verified boarding announcement → deploy ramp → verified ramp-ready announcement
- `ALIGHT` — wait 30 s → verified alighting announcement → deploy ramp → verified ramp-ready announcement
- `RETRACT` — verified retracting announcement → retract ramp
- `RESET` — return ramp to the upper/home position
- `STATUS` — report ramp angle, DFPlayer BUSY availability and automatic-ramp state
- `TEST_AUDIO_1` to `TEST_AUDIO_4` — test individual TTS-generated recordings

There are no physical BOARD / ALIGHT buttons.

If an audio command fails, BUSY never confirms playback, the wrong command is received, or the servo reports an error, the affected automatic sequence stops without continuing to the next ramp movement.

## Kiosk separation

The Accessibility Kiosk and this bus-side controller remain separate systems.

The kiosk uses its own Raspberry Pi 5 audio output/speaker for kiosk navigation TTS. The bus has its **own separate speaker and audio system** controlled by Pico #2 + DFPlayer.

The kiosk's public-facing UI does not speak the passenger's specific assistance needs. The bus announcements also use only general wording.

## TTS file preparation

Generate the four announcement recordings with the chosen TTS voice before the demonstration. Export them as MP3 files and copy them to the DFPlayer microSD card using the track numbering expected by the firmware:

```text
/0001.mp3   → boarding
/0002.mp3   → ramp ready
/0003.mp3   → alighting
/0004.mp3   → retracting
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

First verify that `STATUS` reports:

```text
DF_BUSY=AVAILABLE
AUTO_RAMP=ENABLED
```

With GP15 disconnected, `STATUS` should report `AUTO_RAMP=DISABLED_FAILSAFE`, and BOARD / ALIGHT / RETRACT must not move the ramp automatically.

For the first physical ramp test, keep the servo disconnected or mechanically unloaded so the `RAMP_UP` and `RAMP_DOWN` values can be calibrated safely.

The servo endpoints in `bus/pico/main.py` are prototype values:

```python
RAMP_UP = 10
RAMP_DOWN = 95
```

Adjust them to the actual model ramp.

## Prototype limitation

This is a tabletop demonstration system, not a production passenger-safety controller. The servo mechanism must be mechanically constrained and supervised during testing. Fail-safe software does not replace physical safety hardware, limit switches, current protection or emergency-stop controls.

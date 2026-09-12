# Bus-side ramp and announcement controller

This is the separate second Pico used on the model bus. It controls the ramp servo and a DFPlayer Mini audio module independently of the Accessibility Kiosk.

## Hardware

- Raspberry Pi Pico (#2)
- Servo motor for the ramp
- DFPlayer Mini
- Bus-side speaker connected to the audio system
- microSD card for the announcement recordings
- Two physical demo pushbuttons

## Assistance logic

The ramp is **not** deployed for every assistance profile.

Examples:

- Wheelchair user → ramp may be required
- Parent with stroller → ramp may be required
- Mobility aid / crutches → ramp may be required depending on the situation
- Pregnant passenger → additional assistance may be needed, but a ramp is not automatically required
- Blind / low-vision passenger → assistance may be needed, but a ramp is not automatically required
- Deaf / hard-of-hearing passenger → visual communication may be required, but a ramp is not automatically required

For this prototype, the bus-side BOARD control is operated separately when ramp assistance is actually required. The bus controller does not receive the passenger's NFC profile or specific needs from the kiosk.

## Wiring

| Bus-side Pico | Device | Purpose |
|---|---|---|
| GP16 | Servo signal | Ramp movement |
| GP4 / UART1 TX | DFPlayer RX | Audio commands |
| GP5 / UART1 RX | DFPlayer TX | DFPlayer response |
| GP14 | Board button to GND | Demo boarding sequence |
| GP15 | Alight button to GND | Demo alighting sequence |
| GND | Common GND | Common reference |

Power the servo from a suitable external 5 V supply if the servo draws more current than the Pico can safely provide. Keep the Pico, DFPlayer and servo grounds common.

The DFPlayer Mini handles prerecorded audio playback. A passive speaker can be connected to the DFPlayer speaker output when the speaker is within the module's output capability; larger bus-style speakers may require an appropriate external amplifier.

## SD card audio files

Use four short MP3 recordings. The playback number is based on the track numbering recognised by the DFPlayer:

1. Boarding announcement:
   "Attention passengers. A passenger requiring additional assistance will be boarding. Please give up the priority seat and allow sufficient space for the passenger to board safely. Thank you."
2. Ramp ready:
   "The ramp is ready. Please proceed when safe."
3. Alighting announcement:
   "Attention passengers. A passenger requiring additional assistance will be alighting. Please keep the priority area clear and allow the passenger to alight safely. Thank you."
4. Retracting:
   "The ramp is retracting. Please keep clear."

Do not record or announce the passenger's specific accessibility needs. The public announcement intentionally uses general wording.

## Pico firmware

Copy `bus/pico/main.py` to the bus-side Pico as `main.py` and reset it.

The Pico accepts these USB serial commands:

- `BOARD` — announcement + deploy ramp + ready announcement
- `ALIGHT` — alighting announcement + deploy ramp + ready announcement
- `RETRACT` — retract announcement + retract ramp
- `RESET` — return ramp to the upper/home position
- `STATUS` — report current ramp angle
- `TEST_AUDIO_1` to `TEST_AUDIO_4` — test individual recordings

The physical buttons also trigger BOARD and ALIGHT for demonstrations.

## Kiosk separation

The Accessibility Kiosk and this bus-side controller are separate systems.

The kiosk ends the passenger session after showing the selected bus and arrival information. It does not send `BOARD`, deploy the ramp or play the bus announcement.

The bus-side controller is operated independently when the bus arrives and additional boarding/alighting assistance is required. This keeps the passenger's private assistance profile out of the public bus audio system.

## Timing and safety notes

The current firmware uses fixed delays between audio playback and ramp movement. Keep the demonstration MP3 recordings consistent with the expected timing. For a production system, use a proper playback-status/interlock mechanism rather than relying only on fixed delays.

The servo endpoints (`RAMP_UP` and `RAMP_DOWN`) must be calibrated for the actual model ramp. The servo should have an appropriate external power supply where required; do not draw high servo current directly through the Pico.

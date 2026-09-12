# Bus-side ramp and announcement controller

This is the second Pico used on the model bus. It controls the ramp servo and a DFPlayer Mini audio module.

## Hardware

- Raspberry Pi Pico (#2)
- Servo motor for the ramp
- DFPlayer Mini
- Small speaker connected to DFPlayer Mini
- microSD card for the announcement recordings
- Two optional demo pushbuttons

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

The DFPlayer Mini is used because a normal passive speaker cannot be driven directly by the Pico for prerecorded spoken announcements. DFPlayer provides the audio output to the speaker over its speaker output. The module requires a microSD card for playback.

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

## Kiosk integration

The Raspberry Pi kiosk backend sends `BOARD` to the second Pico after the passenger confirms a bus and the arrival screen opens. The second Pico can then deploy the ramp and play the bus-side boarding announcement.

For the Raspberry Pi to distinguish the two Picos, the installed systemd service uses:

```text
PICO_PORT=/dev/ttyACM0
BUS_PICO_PORT=/dev/ttyACM1
```

The installer allows these paths to be overridden if the Raspberry Pi assigns different device paths:

```bash
PICO_PORT=/dev/ttyACM0 BUS_PICO_PORT=/dev/ttyACM1 ./install.sh
```

Check the actual device paths with both Picos connected before testing. For a production deployment, stable udev device names are preferable to relying on `ttyACM0` / `ttyACM1` numbering.

Alighting is currently triggered from the bus-side Pico's ALIGHT button so the prototype can demonstrate an alighting event independently of the kiosk. A real deployment should replace this with a stop/vehicle event from the bus system.

## Timing and safety notes

The current firmware uses fixed delays between audio playback and ramp movement. Keep the demonstration MP3 recordings consistent with the expected timing. For a production system, use a proper playback-status/interlock mechanism rather than relying only on fixed delays.

The servo endpoints (`RAMP_UP` and `RAMP_DOWN`) must be calibrated for the actual model ramp. The servo should have an appropriate external power supply where required; do not draw high servo current directly through the Pico.

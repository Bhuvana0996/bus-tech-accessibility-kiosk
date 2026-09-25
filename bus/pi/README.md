# Bus-side Raspberry Pi 5 controller

This folder is for the **bus-side Raspberry Pi 5**, not the kiosk.

## Hardware

- Raspberry Pi 5
- Servo for the ramp
- Amplifier
- Speaker

The controller does not use the Pico #2 / DFPlayer hardware from `bus/pico/`.

## Audio

Install `mpg123` and place these files in `bus/audio/`:

- `0001.mp3` — boarding announcement
- `0002.mp3` — ramp ready announcement
- `0003.mp3` — alighting announcement
- `0004.mp3` — ramp retracting announcement

The program waits for mpg123 to finish before moving the servo. This is software-level playback completion; unlike the old DFPlayer design, it does not have a physical BUSY feedback wire.

## Servo

Edit `SERVO_GPIO` in `main.py` to match the GPIO used by the servo signal wire.

The default is GPIO 18 only as a configuration placeholder.

## Commands

- `BOARD`
- `ALIGHT`
- `RETRACT`
- `RESET`
- `STATUS`
- `TEST_AUDIO_1` through `TEST_AUDIO_4`


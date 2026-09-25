#!/usr/bin/env python3
"""
Bus-side controller for Raspberry Pi 5.

Hardware:
- Raspberry Pi 5
- Servo connected to a GPIO pin
- Amplifier + speaker connected to the Pi audio output

Commands:
  BOARD
  ALIGHT
  RETRACT
  RESET
  STATUS
  TEST_AUDIO_1 ... TEST_AUDIO_4

Set SERVO_GPIO below to the GPIO used by the servo signal wire.
Audio files are expected in bus/audio/0001.mp3 ... 0004.mp3.
"""

import os
import subprocess
import sys
import time

SERVO_GPIO = 18  # Change this to the GPIO used by your servo signal wire.
RAMP_UP = 10
RAMP_DOWN = 95
ASSISTANCE_DELAY_SECONDS = 30
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "audio")

try:
    from gpiozero import AngularServo
except ImportError:
    print("gpiozero is not installed. Install it with: sudo apt install python3-gpiozero")
    sys.exit(1)

servo = AngularServo(
    SERVO_GPIO,
    min_angle=-90,
    max_angle=90,
    min_pulse_width=0.0005,
    max_pulse_width=0.0025,
)

def angle_for(position):
    position = max(0, min(100, position))
    return -90 + (position / 100.0) * 180

def move_ramp(position):
    servo.angle = angle_for(position)
    time.sleep(1)
    print(f"RAMP_POSITION={position}")

def play_audio(number):
    filename = os.path.join(AUDIO_DIR, f"{number:04d}.mp3")
    if not os.path.exists(filename):
        print(f"AUDIO_ERROR=FILE_NOT_FOUND:{filename}")
        return False

    print(f"AUDIO_START={filename}", flush=True)
    try:
        result = subprocess.run(
            ["mpg123", "-q", filename],
            check=False,
        )
    except FileNotFoundError:
        print("AUDIO_ERROR=mpg123_not_installed")
        return False

    if result.returncode != 0:
        print(f"AUDIO_ERROR=EXIT_{result.returncode}")
        return False

    print(f"AUDIO_FINISH={filename}", flush=True)
    return True

def board():
    print("BOARD_WAIT=30_SECONDS", flush=True)
    time.sleep(ASSISTANCE_DELAY_SECONDS)

    if not play_audio(1):
        print("BOARDING_ABORTED=AUDIO_FAILED")
        return

    move_ramp(RAMP_DOWN)

    if play_audio(2):
        print("BOARDING_READY")
    else:
        print("BOARDING_READY=AUDIO_FAILED")

def alight():
    print("ALIGHT_WAIT=30_SECONDS", flush=True)
    time.sleep(ASSISTANCE_DELAY_SECONDS)

    if not play_audio(3):
        print("ALIGHTING_ABORTED=AUDIO_FAILED")
        return

    move_ramp(RAMP_DOWN)

    if play_audio(2):
        print("ALIGHTING_READY")
    else:
        print("ALIGHTING_READY=AUDIO_FAILED")

def retract():
    if not play_audio(4):
        print("RETRACT_AUDIO_FAILED")
        return

    move_ramp(RAMP_UP)
    print("RAMP_RETRACTED")

def reset():
    move_ramp(RAMP_UP)
    print("RESET_COMPLETE")

def status():
    print("STATUS=READY")

def handle(command):
    command = command.strip().upper()

    if command == "BOARD":
        board()
    elif command == "ALIGHT":
        alight()
    elif command == "RETRACT":
        retract()
    elif command == "RESET":
        reset()
    elif command == "STATUS":
        status()
    elif command.startswith("TEST_AUDIO_"):
        try:
            number = int(command.rsplit("_", 1)[1])
            if number not in (1, 2, 3, 4):
                raise ValueError
            play_audio(number)
        except ValueError:
            print("ERROR=USE_TEST_AUDIO_1_TO_4")
    elif command == "QUIT":
        raise SystemExit
    elif command:
        print("ERROR=UNKNOWN_COMMAND")

def main():
    print("BUS_PI_CONTROLLER=READY")
    print(f"SERVO_GPIO={SERVO_GPIO}")
    print(f"AUDIO_DIR={os.path.abspath(AUDIO_DIR)}")
    print("Commands: BOARD ALIGHT RETRACT RESET STATUS TEST_AUDIO_1 TEST_AUDIO_2 TEST_AUDIO_3 TEST_AUDIO_4 QUIT")

    reset()

    for line in sys.stdin:
        handle(line)

if __name__ == "__main__":
    main()

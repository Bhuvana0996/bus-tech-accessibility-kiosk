#!/usr/bin/env python3
"""
Bus-side controller for Raspberry Pi 5.

Hardware:
- Raspberry Pi 5
- Servo signal on BCM GPIO 18 (physical pin 12)
- Amplifier + speaker connected to the Pi audio output

Commands:
  BOARD
  ALIGHT
  RETRACT
  RESET
  STATUS
  TEST_RAMP_DOWN
  TEST_RAMP_UP
  TEST_AUDIO_1 ... TEST_AUDIO_4
"""

import os
import subprocess
import sys
import time

SERVO_GPIO = 18
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
    initial_angle=None,
)


def angle_for(position):
    position = max(0, min(100, position))
    return -90 + (position / 100.0) * 180


def move_ramp(position):
    """Move the servo to a ramp position and report success."""
    try:
        target = angle_for(position)
        print(f"RAMP_MOVE={position}% ({target:.1f} degrees)", flush=True)

        # Move in small steps so the physical ramp moves smoothly.
        current = servo.angle
        if current is None:
            current = target

        step = 3 if target >= current else -3
        angle = current

        while (step > 0 and angle < target) or (step < 0 and angle > target):
            angle += step
            if step > 0:
                angle = min(angle, target)
            else:
                angle = max(angle, target)
            servo.angle = angle
            time.sleep(0.08)

        servo.angle = target
        time.sleep(0.5)
        print(f"RAMP_POSITION={position}", flush=True)
        return True

    except Exception as exc:
        print(f"RAMP_ERROR={type(exc).__name__}:{exc}", flush=True)
        return False


def play_audio(number):
    filename = os.path.join(AUDIO_DIR, f"{number:04d}.mp3")
    if not os.path.exists(filename):
        print(f"AUDIO_ERROR=FILE_NOT_FOUND:{filename}", flush=True)
        return False

    print(f"AUDIO_START={filename}", flush=True)
    try:
        result = subprocess.run(["mpg123", "-q", filename], check=False)
    except FileNotFoundError:
        print("AUDIO_ERROR=mpg123_not_installed", flush=True)
        return False

    if result.returncode != 0:
        print(f"AUDIO_ERROR=EXIT_{result.returncode}", flush=True)
        return False

    print(f"AUDIO_FINISH={filename}", flush=True)
    return True


def board():
    print("BOARD_WAIT=30_SECONDS", flush=True)
    time.sleep(ASSISTANCE_DELAY_SECONDS)

    if not play_audio(1):
        print("BOARDING_ABORTED=AUDIO_FAILED", flush=True)
        return

    if not move_ramp(RAMP_DOWN):
        print("BOARDING_ABORTED=RAMP_FAILED", flush=True)
        return

    print("BOARDING_READY" if play_audio(2) else "BOARDING_READY=AUDIO_FAILED", flush=True)


def alight():
    print("ALIGHT_WAIT=30_SECONDS", flush=True)
    time.sleep(ASSISTANCE_DELAY_SECONDS)

    if not play_audio(3):
        print("ALIGHTING_ABORTED=AUDIO_FAILED", flush=True)
        return

    if not move_ramp(RAMP_DOWN):
        print("ALIGHTING_ABORTED=RAMP_FAILED", flush=True)
        return

    print("ALIGHTING_READY" if play_audio(2) else "ALIGHTING_READY=AUDIO_FAILED", flush=True)


def retract():
    if not play_audio(4):
        print("RETRACT_AUDIO_FAILED", flush=True)
        return

    if move_ramp(RAMP_UP):
        print("RAMP_RETRACTED", flush=True)
    else:
        print("RETRACT_ABORTED=RAMP_FAILED", flush=True)


def reset():
    if move_ramp(RAMP_UP):
        print("RESET_COMPLETE", flush=True)
    else:
        print("RESET_FAILED", flush=True)


def status():
    print("STATUS=READY", flush=True)


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
    elif command == "TEST_RAMP_DOWN":
        print("TEST_RAMP_DOWN_OK" if move_ramp(RAMP_DOWN) else "TEST_RAMP_DOWN_FAILED", flush=True)
    elif command == "TEST_RAMP_UP":
        print("TEST_RAMP_UP_OK" if move_ramp(RAMP_UP) else "TEST_RAMP_UP_FAILED", flush=True)
    elif command.startswith("TEST_AUDIO_"):
        try:
            number = int(command.rsplit("_", 1)[1])
            if number not in (1, 2, 3, 4):
                raise ValueError
            play_audio(number)
        except ValueError:
            print("ERROR=USE_TEST_AUDIO_1_TO_4", flush=True)
    elif command == "QUIT":
        raise SystemExit
    elif command:
        print("ERROR=UNKNOWN_COMMAND", flush=True)


def main():
    print("BUS_PI_CONTROLLER=READY", flush=True)
    print(f"SERVO_GPIO={SERVO_GPIO} (BCM / physical pin 12)", flush=True)
    print(f"AUDIO_DIR={os.path.abspath(AUDIO_DIR)}", flush=True)
    print(
        "Commands: BOARD ALIGHT RETRACT RESET STATUS "
        "TEST_RAMP_DOWN TEST_RAMP_UP TEST_AUDIO_1 TEST_AUDIO_2 TEST_AUDIO_3 TEST_AUDIO_4 QUIT",
        flush=True,
    )

    # Start in the retracted position.
    reset()

    for line in sys.stdin:
        handle(line)


if __name__ == "__main__":
    main()

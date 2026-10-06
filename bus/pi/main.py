#!/usr/bin/env python3
"""
Automatic bus-side controller for Raspberry Pi 5.

When started, this controller:
1. Announces that accessibility assistance is starting.
2. Deploys the ramp.
3. Keeps the ramp deployed for at least 30 seconds.
4. Announces that the ramp is retracting.
5. Retracts the ramp.

Hardware:
- Raspberry Pi 5
- Servo signal on BCM GPIO 18 (physical pin 12)
- Amplifier + speaker connected to the Pi audio output
"""

import os
import shutil
import subprocess
import sys
import time

SERVO_GPIO = 18
RAMP_UP = 10
RAMP_DOWN = 95
RAMP_HOLD_SECONDS = 30
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "audio")

try:
    from gpiozero import AngularServo
except ImportError:
    print("gpiozero is not installed. Run: sudo apt install python3-gpiozero", flush=True)
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
    """Move the servo smoothly to the requested ramp position."""
    target = angle_for(position)
    print(f"RAMP_MOVE={position}% ({target:.1f} degrees)", flush=True)

    try:
        current = servo.angle
        if current is None:
            current = angle_for(RAMP_UP)

        step = 3 if target >= current else -3
        angle = current

        while (step > 0 and angle < target) or (step < 0 and angle > target):
            angle += step
            angle = min(angle, target) if step > 0 else max(angle, target)
            servo.angle = angle
            time.sleep(0.08)

        servo.angle = target
        time.sleep(0.5)
        print(f"RAMP_POSITION={position}", flush=True)
        return True
    except Exception as exc:
        print(f"RAMP_ERROR={type(exc).__name__}:{exc}", flush=True)
        return False


def speak(text):
    """Play a spoken announcement using espeak-ng/espeak if available."""
    print(f"ANNOUNCEMENT={text}", flush=True)

    command = shutil.which("espeak-ng") or shutil.which("espeak")
    if command:
        result = subprocess.run(
            [command, "-s", "145", "-a", "150", text],
            check=False,
        )
        return result.returncode == 0

    print("AUDIO_WARNING=espeak-ng_or_espeak_not_installed", flush=True)
    return False


def play_audio(number):
    """Play an optional numbered MP3 if the project has one."""
    filename = os.path.join(AUDIO_DIR, f"{number:04d}.mp3")
    if not os.path.exists(filename):
        return False

    mpg123 = shutil.which("mpg123")
    if not mpg123:
        return False

    return subprocess.run([mpg123, "-q", filename], check=False).returncode == 0


def automatic_demo():
    """Run the complete bus accessibility demo automatically on startup."""
    print("BUS_ACCESSIBILITY_DEMO=START", flush=True)

    # Start safely in the retracted position.
    if not move_ramp(RAMP_UP):
        print("DEMO_FAILED=INITIAL_RAMP_POSITION", flush=True)
        return

    speak("Accessibility assistance requested. The bus ramp will deploy shortly.")

    time.sleep(2)

    if not move_ramp(RAMP_DOWN):
        print("DEMO_FAILED=RAMP_DEPLOY", flush=True)
        return

    speak("The accessibility ramp is now deployed. Please proceed when safe.")

    # Ramp remains deployed for at least 30 seconds.
    print(f"RAMP_HOLD={RAMP_HOLD_SECONDS}_SECONDS", flush=True)
    time.sleep(RAMP_HOLD_SECONDS)

    speak("The accessibility assistance period is complete. The ramp will now retract.")

    time.sleep(2)

    if move_ramp(RAMP_UP):
        speak("Ramp retracted. Thank you.")
        print("BUS_ACCESSIBILITY_DEMO=COMPLETE", flush=True)
    else:
        print("DEMO_FAILED=RAMP_RETRACT", flush=True)


def main():
    print("BUS_PI_CONTROLLER=READY", flush=True)
    print("SERVO_GPIO=18 (BCM / physical pin 12)", flush=True)
    print(f"RAMP_HOLD_SECONDS={RAMP_HOLD_SECONDS}", flush=True)

    automatic_demo()


if __name__ == "__main__":
    main()

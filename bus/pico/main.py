from machine import Pin, PWM, UART
import sys
import time

# BUS-SIDE PICO #2
# The bus Pico controls the ramp servo and DFPlayer Mini audio only.
# There are NO physical BOARD / ALIGHT buttons.
#
# FAIL-SAFE RULE:
# Automatic ramp movement is allowed only when DFPlayer BUSY is wired and
# confirms that the required announcement actually started and finished.
# If BUSY is unavailable or audio timing cannot be confirmed, the ramp is
# NOT moved automatically.
#
# GP16 -> servo signal
# GP4  -> DFPlayer RX (UART1 TX)
# GP5  <- DFPlayer TX (UART1 RX)
# GP15 <- DFPlayer BUSY (LOW while playing)

SERVO_PIN = 16
DF_TX = 4
DF_RX = 5
DF_BUSY_PIN = 15

RAMP_UP = 10
RAMP_DOWN = 95
SERVO_STEP_DELAY_MS = 15
DF_VOLUME = 22
ASSISTANCE_DELAY_MS = 30_000

ANNOUNCEMENTS = {
    1: (
        "Attention passengers. A passenger requiring additional assistance "
        "will be boarding. Please give up the priority seat and allow "
        "sufficient space for the passenger to board safely. Thank you."
    ),
    2: "The ramp is ready. Please proceed when safe.",
    3: (
        "Attention passengers. A passenger requiring additional assistance "
        "will be alighting. Please keep the priority area clear and allow "
        "the passenger to alight safely. Thank you."
    ),
    4: "The ramp is retracting. Please keep clear.",
}

AUDIO_FILES = {
    1: "0001.mp3",
    2: "0002.mp3",
    3: "0003.mp3",
    4: "0004.mp3",
}

TRACK_FALLBACK_MS = {
    1: 8_000,
    2: 3_000,
    3: 8_000,
    4: 3_000,
}

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)
df = UART(1, baudrate=9600, tx=Pin(DF_TX), rx=Pin(DF_RX))

try:
    df_busy = Pin(DF_BUSY_PIN, Pin.IN, Pin.PULL_UP)
    HAS_DF_BUSY = True
except Exception:
    df_busy = None
    HAS_DF_BUSY = False

current_angle = RAMP_UP


def servo_angle(angle):
    angle = max(0, min(180, angle))
    duty_us = 500 + int((2000 * angle) / 180)
    servo.duty_u16(int(duty_us * 65535 / 20000))


def move_ramp(target):
    global current_angle
    target = max(0, min(180, target))
    if current_angle == target:
        return True

    try:
        step = 1 if target > current_angle else -1
        while current_angle != target:
            current_angle += step
            servo_angle(current_angle)
            time.sleep_ms(SERVO_STEP_DELAY_MS)
        return True
    except Exception as exc:
        print("SERVO_ERROR=" + str(exc))
        return False


def df_command(command, parameter=0):
    packet = bytearray([
        0x7E, 0xFF, 0x06, command, 0x00,
        (parameter >> 8) & 0xFF, parameter & 0xFF,
        0x00, 0x00, 0xEF
    ])
    checksum = -(0xFF + 0x06 + command + 0x00 +
                 ((parameter >> 8) & 0xFF) + (parameter & 0xFF))
    checksum &= 0xFFFF
    packet[7] = (checksum >> 8) & 0xFF
    packet[8] = checksum & 0xFF
    df.write(packet)


def play(track):
    """Play a mapped MP3. Returns False for an invalid track."""
    if track not in AUDIO_FILES:
        print("UNKNOWN_AUDIO_TRACK=" + str(track))
        return False

    print("PLAY_FILE=" + AUDIO_FILES[track])
    try:
        df_command(0x03, track)
        time.sleep_ms(150)
        return True
    except Exception as exc:
        print("DFPLAYER_ERROR=" + str(exc))
        return False


def wait_for_audio(track, require_busy=False):
    """Return True only when playback is confirmed to have completed."""
    if not HAS_DF_BUSY:
        if require_busy:
            print("AUDIO_FAILSAFE_STOP=DF_BUSY_NOT_WIRED")
            return False
        time.sleep_ms(TRACK_FALLBACK_MS.get(track, 3_000))
        return True

    start = time.ticks_ms()

    # DFPlayer BUSY is normally HIGH while idle and LOW while playing.
    # Require both a real start and a real finish before an automatic ramp move.
    while df_busy.value() != 0:
        time.sleep_ms(20)
        if time.ticks_diff(time.ticks_ms(), start) > 5_000:
            print("AUDIO_START_TIMEOUT=" + str(track))
            return False

    while df_busy.value() == 0:
        time.sleep_ms(50)
        if time.ticks_diff(time.ticks_ms(), start) > 60_000:
            print("AUDIO_TIMEOUT=" + str(track))
            return False

    return True


def safe_audio_sequence(track):
    if not play(track):
        print("AUDIO_FAILSAFE_STOP=PLAY_COMMAND_FAILED")
        return False
    if not wait_for_audio(track, require_busy=True):
        print("AUDIO_FAILSAFE_STOP=PLAYBACK_NOT_CONFIRMED")
        return False
    return True


def wait_30_seconds():
    print("ASSISTANCE_DELAY_START=30")
    time.sleep_ms(ASSISTANCE_DELAY_MS)
    print("ASSISTANCE_DELAY_DONE")


def boarding_sequence():
    print("BOARDING_START")
    if not HAS_DF_BUSY:
        print("BOARDING_ABORTED=DF_BUSY_NOT_WIRED")
        return

    wait_30_seconds()

    print("PLAY_BOARDING")
    if not safe_audio_sequence(1):
        return
    print("BOARDING_ANNOUNCEMENT_DONE")

    print("RAMP_DEPLOYING")
    if not move_ramp(RAMP_DOWN):
        print("BOARDING_ABORTED=SERVO_ERROR")
        return
    print("RAMP_DEPLOYED")

    print("PLAY_RAMP_READY")
    if not safe_audio_sequence(2):
        return
    print("RAMP_READY")


def alighting_sequence():
    print("ALIGHTING_START")
    if not HAS_DF_BUSY:
        print("ALIGHTING_ABORTED=DF_BUSY_NOT_WIRED")
        return

    wait_30_seconds()

    print("PLAY_ALIGHTING")
    if not safe_audio_sequence(3):
        return
    print("ALIGHTING_ANNOUNCEMENT_DONE")

    print("RAMP_DEPLOYING")
    if not move_ramp(RAMP_DOWN):
        print("ALIGHTING_ABORTED=SERVO_ERROR")
        return
    print("RAMP_DEPLOYED")

    print("PLAY_RAMP_READY")
    if not safe_audio_sequence(2):
        return
    print("RAMP_READY")


def retract_sequence():
    print("RAMP_RETRACT_REQUEST")
    if not HAS_DF_BUSY:
        print("RETRACT_ABORTED=DF_BUSY_NOT_WIRED")
        return

    if not safe_audio_sequence(4):
        return

    print("RAMP_RETRACTING")
    if not move_ramp(RAMP_UP):
        print("RETRACT_ABORTED=SERVO_ERROR")
        return
    print("RAMP_RETRACTED")


def handle_command(command):
    command = command.strip().upper()

    if command == "BOARD":
        boarding_sequence()
    elif command == "ALIGHT":
        alighting_sequence()
    elif command == "RETRACT":
        retract_sequence()
    elif command == "RESET":
        if move_ramp(RAMP_UP):
            print("RESET_OK")
        else:
            print("RESET_FAILED=SERVO_ERROR")
    elif command == "STATUS":
        print("RAMP_ANGLE=" + str(current_angle))
        print("DF_BUSY=" + ("AVAILABLE" if HAS_DF_BUSY else "NOT_WIRED"))
        print("AUTO_RAMP=" + ("ENABLED" if HAS_DF_BUSY else "DISABLED_FAILSAFE"))
    elif command.startswith("TEST_AUDIO_"):
        try:
            track = int(command.split("_")[-1])
            if track in AUDIO_FILES:
                if play(track):
                    wait_for_audio(track, require_busy=False)
            else:
                print("UNKNOWN_AUDIO_TRACK=" + str(track))
        except ValueError:
            print("UNKNOWN_COMMAND=" + command)
    elif command:
        print("UNKNOWN_COMMAND=" + command)


if not move_ramp(RAMP_UP):
    print("SERVO_STARTUP_ERROR")

time.sleep_ms(500)
df_command(0x06, DF_VOLUME)
df_command(0x16, 0)
print("BUS_PICO_READY")
print("AUDIO_SOURCE=PREGENERATED_TTS_MP3")
print("AUDIO_FILES=0001.mp3,0002.mp3,0003.mp3,0004.mp3")
print("DF_BUSY=" + ("AVAILABLE" if HAS_DF_BUSY else "NOT_WIRED"))
print("AUTO_RAMP=" + ("ENABLED" if HAS_DF_BUSY else "DISABLED_FAILSAFE"))

try:
    import uselect
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
except Exception:
    poll = None

while True:
    if poll:
        try:
            if poll.poll(0):
                line = sys.stdin.readline()
                if line:
                    handle_command(line)
        except Exception as exc:
            print("SERIAL_INPUT_ERROR=" + str(exc))

    time.sleep_ms(30)

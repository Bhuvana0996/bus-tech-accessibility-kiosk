from machine import Pin, PWM, UART
import sys
import time

# BUS-SIDE PICO #2
# The bus Pico controls the ramp servo and DFPlayer Mini audio only.
# There are NO physical BOARD / ALIGHT buttons.
# Public announcements are TTS-generated MP3 files stored on the DFPlayer microSD.
#
# GP16 -> servo signal
# GP4  -> DFPlayer RX (UART1 TX)
# GP5  <- DFPlayer TX (UART1 RX)
# GP15 <- DFPlayer BUSY (optional but recommended; LOW while playing)
#
# The bus-side speaker connects to the DFPlayer Mini, not directly to the Pico.

SERVO_PIN = 16
DF_TX = 4
DF_RX = 5
DF_BUSY_PIN = 15

RAMP_UP = 10
RAMP_DOWN = 95
SERVO_STEP_DELAY_MS = 15
DF_VOLUME = 22
ASSISTANCE_DELAY_MS = 30_000

# Fallback durations are used only if the DFPlayer BUSY pin is not available.
# Replace these with the actual TTS recording lengths if BUSY is not wired.
TRACK_FALLBACK_MS = {
    1: 8_000,   # boarding announcement
    2: 3_000,   # ramp ready
    3: 8_000,   # alighting announcement
    4: 3_000,   # ramp retracting
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
        return

    step = 1 if target > current_angle else -1
    while current_angle != target:
        current_angle += step
        servo_angle(current_angle)
        time.sleep_ms(SERVO_STEP_DELAY_MS)


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
    """Start a TTS-generated MP3 track on the DFPlayer."""
    df_command(0x03, track)
    time.sleep_ms(150)


def wait_for_audio(track):
    """Wait until the selected announcement has finished."""
    if HAS_DF_BUSY:
        # DFPlayer BUSY is normally LOW while audio is playing.
        start = time.ticks_ms()
        # Give the module a moment to start playback.
        time.sleep_ms(100)
        while df_busy.value() == 0:
            time.sleep_ms(50)
            # Safety timeout prevents the ramp sequence from hanging forever.
            if time.ticks_diff(time.ticks_ms(), start) > 60_000:
                print("AUDIO_TIMEOUT=" + str(track))
                return
        return

    time.sleep_ms(TRACK_FALLBACK_MS.get(track, 3_000))


def wait_30_seconds():
    print("ASSISTANCE_DELAY_START=30")
    time.sleep_ms(ASSISTANCE_DELAY_MS)
    print("ASSISTANCE_DELAY_DONE")


def boarding_sequence():
    print("BOARDING_START")
    wait_30_seconds()

    print("PLAY_BOARDING")
    play(1)
    wait_for_audio(1)
    print("BOARDING_ANNOUNCEMENT_DONE")

    print("RAMP_DEPLOYING")
    move_ramp(RAMP_DOWN)
    print("RAMP_DEPLOYED")

    print("PLAY_RAMP_READY")
    play(2)
    wait_for_audio(2)
    print("RAMP_READY")


def alighting_sequence():
    print("ALIGHTING_START")
    wait_30_seconds()

    print("PLAY_ALIGHTING")
    play(3)
    wait_for_audio(3)
    print("ALIGHTING_ANNOUNCEMENT_DONE")

    print("RAMP_DEPLOYING")
    move_ramp(RAMP_DOWN)
    print("RAMP_DEPLOYED")

    print("PLAY_RAMP_READY")
    play(2)
    wait_for_audio(2)
    print("RAMP_READY")


def retract_sequence():
    print("RAMP_RETRACTING")
    play(4)
    wait_for_audio(4)

    move_ramp(RAMP_UP)
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
        move_ramp(RAMP_UP)
        print("RESET_OK")
    elif command == "STATUS":
        print("RAMP_ANGLE=" + str(current_angle))
        print("DF_BUSY=" + ("AVAILABLE" if HAS_DF_BUSY else "NOT_WIRED"))
    elif command == "TEST_AUDIO_1":
        play(1)
    elif command == "TEST_AUDIO_2":
        play(2)
    elif command == "TEST_AUDIO_3":
        play(3)
    elif command == "TEST_AUDIO_4":
        play(4)
    elif command:
        print("UNKNOWN_COMMAND=" + command)


servo_angle(current_angle)
time.sleep_ms(500)
df_command(0x06, DF_VOLUME)
df_command(0x16, 0)
print("BUS_PICO_READY")
print("AUDIO_SOURCE=TTS_GENERATED_MP3")
print("DF_BUSY=" + ("AVAILABLE" if HAS_DF_BUSY else "NOT_WIRED"))

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
        except Exception:
            pass

    time.sleep_ms(30)

from machine import Pin, PWM, UART
import sys
import time

# BUS-SIDE PICO
# Servo signal: GP16
# DFPlayer Mini UART: GP4 TX -> DFPlayer RX, GP5 RX <- DFPlayer TX
# Demo buttons: GP14 = BOARD, GP15 = ALIGHT (button to GND)
SERVO_PIN = 16
DF_TX = 4
DF_RX = 5
BOARD_BUTTON = 14
ALIGHT_BUTTON = 15

RAMP_UP = 10
RAMP_DOWN = 95
SERVO_STEP_DELAY_MS = 15
DF_VOLUME = 22

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)
df = UART(1, baudrate=9600, tx=Pin(DF_TX), rx=Pin(DF_RX))
board_button = Pin(BOARD_BUTTON, Pin.IN, Pin.PULL_UP)
alight_button = Pin(ALIGHT_BUTTON, Pin.IN, Pin.PULL_UP)

current_angle = RAMP_UP


def servo_angle(angle):
    angle = max(0, min(180, angle))
    duty_us = 500 + int((2000 * angle) / 180)
    servo.duty_u16(int(duty_us * 65535 / 20000))


def move_ramp(target):
    global current_angle
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
    # Track number is the file number on the DFPlayer SD card.
    df_command(0x03, track)
    time.sleep_ms(150)


def boarding_sequence():
    print("BOARDING_START")
    play(1)
    time.sleep_ms(2500)
    print("RAMP_DEPLOYING")
    move_ramp(RAMP_DOWN)
    play(2)
    time.sleep_ms(1800)
    print("RAMP_READY")


def alighting_sequence():
    print("ALIGHTING_START")
    play(3)
    time.sleep_ms(2500)
    print("RAMP_DEPLOYING")
    move_ramp(RAMP_DOWN)
    play(2)
    time.sleep_ms(1800)
    print("RAMP_READY")


def retract_sequence():
    print("RAMP_RETRACTING")
    play(4)
    time.sleep_ms(1500)
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
    elif command == "TEST_AUDIO_1":
        play(1)
    elif command == "TEST_AUDIO_2":
        play(2)
    elif command == "TEST_AUDIO_3":
        play(3)
    elif command == "TEST_AUDIO_4":
        play(4)


servo_angle(current_angle)
time.sleep_ms(500)
df_command(0x06, DF_VOLUME)
df_command(0x16, 0)
print("BUS_PICO_READY")

last_board = 1
last_alight = 1
last_emit = time.ticks_ms() - 500

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

    now = time.ticks_ms()
    b = board_button.value()
    a = alight_button.value()

    if last_board == 1 and b == 0 and time.ticks_diff(now, last_emit) > 500:
        boarding_sequence()
        last_emit = time.ticks_ms()

    if last_alight == 1 and a == 0 and time.ticks_diff(now, last_emit) > 500:
        alighting_sequence()
        last_emit = time.ticks_ms()

    last_board = b
    last_alight = a
    time.sleep_ms(30)

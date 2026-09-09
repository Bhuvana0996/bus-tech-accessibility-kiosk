from machine import Pin
import time

# Button 1 = Bus 191, Button 2 = Bus 400.
# Each pushbutton connects its GPIO to GND.
button1 = Pin(14, Pin.IN, Pin.PULL_UP)
button2 = Pin(15, Pin.IN, Pin.PULL_UP)

last1 = 1
last2 = 1
last_emit = 0

print("PICO_READY")

while True:
    b1 = button1.value()
    b2 = button2.value()
    now = time.ticks_ms()

    if last1 == 1 and b1 == 0 and time.ticks_diff(now, last_emit) > 250:
        print("BUTTON1")
        last_emit = now

    if last2 == 1 and b2 == 0 and time.ticks_diff(now, last_emit) > 250:
        print("BUTTON2")
        last_emit = now

    last1 = b1
    last2 = b2
    time.sleep_ms(20)

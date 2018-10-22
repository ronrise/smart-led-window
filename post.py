import pigpio
import time

pin = 21

pi = pigpio.pi()

brightness = 0

while brightness < 255:
    pi.set_PWM_dutycycle(pin, brightness)
    brightness += 1
    time.sleep(0.05)

while brightness > 0:
    pi.set_PWM_dutycycle(pin, brightness)
    brightness += 1
    time.sleep(0.05)

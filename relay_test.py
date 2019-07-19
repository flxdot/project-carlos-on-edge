import RPi.GPIO as GPIO
import time

pins = [20, 21, 22, 23, 24, 25, 26, 27]

GPIO.setmode(GPIO.BCM)

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

# activate each pin for one second
for cnt, pin in enumerate(pins):
    print('Relay {}'.format(cnt + 1))
    GPIO.output(pin, GPIO.LOW)
    time.sleep(1)
    GPIO.output(pin, GPIO.HIGH)

GPIO.cleanup()

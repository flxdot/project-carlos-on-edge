#!/usr/bin/python

import time

import RPi.GPIO as GPIO

from legacy.sensors.auxiliary import SmartSensor

usleep = lambda x: time.sleep(x / 1000000.0)


class SeeedUltraSonicRanger(SmartSensor):
    """Do distance measurements with the Seeed Ultrasonic Ranger.


    Based on the documentation:
    http://wiki.seeedstudio.com/Grove-Ultrasonic_Ranger/

    This Grove - Ultrasonic ranger is a non-contact distance measurement module which works at 40KHz. When we provide
    a pulse trigger signal with more than 10uS through signal pin, the Grove_Ultrasonic_Ranger will issue 8 cycles of
    40kHz cycle level and detect the echo. The pulse width of the echo signal is proportional to the measured distance.
    Here is the formula: Distance = echo signal high time * Sound speed (340M/S)/2. Grove_Ultrasonic_Ranger's trig and
    echo signal share 1 SIG pin.
    """

    # The range of this device is
    # Measuring range: 0.02-3.5 m
    # Therefore the max timeout range should be returned after 0.1029 seconds
    _TIMEOUT = 0.15

    def __init__(self, pin):
        """Constructor

        :param pin: (mandatory, int) pin number
        """

        self._pin = pin

    def _get_distance(self):
        """Internal method to measure the distance with the ultra sonic ranger."""

        # set the mode to GPIO pin layout
        GPIO.setmode(GPIO.BCM)

        # set the channel as output
        GPIO.setup(self._pin, GPIO.OUT)

        # write a special activation sequence
        # Note: I have no idea why this has to be performed
        GPIO.output(self._pin, GPIO.LOW)
        usleep(2)
        GPIO.output(self._pin, GPIO.HIGH)
        usleep(11)
        GPIO.output(self._pin, GPIO.LOW)

        # turn the chanel to in and wait for a response
        GPIO.setup(self._pin, GPIO.IN)

        # wait for any previous pulse to end
        t0 = time.time()
        while GPIO.input(self._pin):
            if time.time() - t0 > SeeedUltraSonicRanger._TIMEOUT:
                return None

        # wait for the pulse to start
        t0 = time.time()
        while not GPIO.input(self._pin):
            # wait .15 second at most
            if time.time() - t0 > SeeedUltraSonicRanger._TIMEOUT:
                return None

        # wait for the pulse to stop
        t1 = time.time()
        while GPIO.input(self._pin):
            # wait .15 second at most
            if time.time() - t0 > SeeedUltraSonicRanger._TIMEOUT:
                return None

        # measure the time it took for the pulse to stop
        t2 = time.time()

        # calculate the length of the high signal in seconds
        duration = t2 - t1

        # calculate the distance in m
        # time * speed of sound divided by 2 because the echo has to come back
        distance = duration * 340 / 2

        # return the distance
        return distance

    def get_distance(self, retries=5):
        """Measures the distance to the next object in m.

        :return: distance in m
        """

        for cnt in range(retries):
            dist = self._get_distance()
            if dist:
                return dist
        return None

    def measure(self):
        """Performs a measurement and returns all available values in a dictionary.
        The keys() are the names of the measurement and the values the corresponding values.

        :return: dict
        """

        return {"distance": self.get_distance()}

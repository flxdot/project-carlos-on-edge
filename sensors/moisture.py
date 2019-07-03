#!/usr/bin/python

#Project Carlos
#

import time, signal, sys
import sensors.SDL_Adafruit_ADS1x15


class CapacitiveSoilMoistureSensor(object):
    """This class is an interface to the Capacitive Soil Moisture Sensor v1.2"""


    def __init__(self, ic, gain=4096, sps=250):
        """

        :param ic: i2c address
        :param gain: voltage for the sensor
        :param sps: samples per second
        """

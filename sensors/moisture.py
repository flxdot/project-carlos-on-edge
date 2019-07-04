#!/usr/bin/python


class CapacitiveSoilMoistureSensor(object):
    """This class is an interface to the Capacitive Soil Moisture Sensor v1.2"""

    # the PGA of the capacitive moisture sensor
    __PGA = 4096  # +/- 4.096V

    # the minimum voltage the sensor will return
    __MIN_VOLTAGE = 1.2

    # the max voltage the sensor will return
    __MAX_VOLTAGE = 2.5

    def __init__(self, ad_converter, channel, sps=250):
        """Constructor

        :param ad_converter: (mandatory, sensors.ad_converter.ADS1x15) object to interface the A/D converter
        :param channel: (mandatory, uint) the channel to which the sensor is connected to
        :param sps: samples per second
        """

        # store propertie4s
        self._adconv = ad_converter
        self._chan = channel
        self._sps = sps

    def convertVoltageToMoisture(self, v):
        """Converts the voltage values to moisture level.

        :param v: (mandatory, float) voltage in V
        :return:
        """

        return 1 - ((v - self.__MIN_VOLTAGE) / (self.__MAX_VOLTAGE - self.__MIN_VOLTAGE))


    def read(self):
        """Reads the sensor voltage."""

        # convert from mV to V
        return self._adconv.readADCSingleEnded(channel=self._chan, pga=self.__PGA, sps=self._sps) / 1000

    def readMoistureLevel(self):
        """Returns the moisture level from 0-1.

        0: Sensor at dry air
        1: Dipped in water
        """

        return self.convertVoltageToMoisture(self.read())

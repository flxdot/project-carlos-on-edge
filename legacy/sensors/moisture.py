#!/usr/bin/python

from legacy.sensors.ad_converter import ADConverter
from legacy.sensors.auxiliary import SmartSensor


class CapacitiveSoilMoistureSensor(SmartSensor):
    """This class is an interface to the Capacitive Soil Moisture Sensor v1.2"""

    # the PGA of the capacitive moisture sensor
    __PGA = 4096  # +/- 4.096V

    # the minimum voltage the sensor will return
    __MIN_VOLTAGE = 1.2

    # the max voltage the sensor will return
    __MAX_VOLTAGE = 2.5

    # the minimum voltage which will be interpreted as valid reading
    __MIN_VALID_VOLTAGE = 1

    # the max voltage which will be interpreted as valid reading
    __MAX_VALID_VOLTAGE = 3

    def __init__(self, address, channel, sps=250):
        """Constructor

        :param address: (mandatory, hex) the i2c address of the ADS1x15 a/d converter
        :param channel: (mandatory, uint) the channel to which the sensor is connected to
        :param sps: samples per second
        """

        # store properties
        self._adconv = ADConverter(address)
        self._chan = channel
        self._sps = sps

        # perform a first read because some time there seems to be some sort of glitch where the internal memory
        self._read()

    def _convertVoltageToMoisture(self, v):
        """Converts the voltage values to moisture level.

        :param v: (mandatory, float) voltage in V
        :return:
        """

        return 1 - (
            (v - self.__MIN_VOLTAGE) / (self.__MAX_VOLTAGE - self.__MIN_VOLTAGE)
        )

    def _read(self):
        """Reads the sensor voltage."""

        # convert from mV to V
        return (
            self._adconv.readADCSingleEnded(
                channel=self._chan, pga=self.__PGA, sps=self._sps
            )
            / 1000
        )

    def readMoistureLevel(self):
        """Returns the moisture level from 0-1.

        0: Sensor at dry air
        1: Dipped in water
        """

        # read the voltage
        volts = self._read()
        # check if the values are within boundaries one would expect
        if volts < self.__MIN_VALID_VOLTAGE or volts > self.__MAX_VALID_VOLTAGE:
            return None
        # return the converted voltage value
        return self._convertVoltageToMoisture(volts)

    def measure(self):
        """Performs a measurement and returns all available values in a dictionary.
        The keys() are the names of the measurement and the values the corresponding values.

        :return: dict
        """

        # read the voltage
        volts = self._read()
        # check if the values are within boundaries one would expect
        if volts < self.__MIN_VALID_VOLTAGE or volts > self.__MAX_VALID_VOLTAGE:
            return {"volts": None, "percentage": None}

        # convert the volts to moisture level
        moisture = self._convertVoltageToMoisture(volts)

        return {"volts": float(volts), "percentage": float(moisture)}

    @classmethod
    def from_config(cls, config: dict):
        """Alternative constructor to obtain a moisture sensor based on the given config

        :param config: (mandatory, dict) the loaded config as dictionary
        :return: CapacitiveSoilMoistureSensor
        """

        return cls(address=config["i2c-address"], channel=config["channel"])

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Config did not contain mandatory fields
        :raises ValueError: Config did not contain valid information
        """

        # i2c-address ######################

        # key existing?
        if "i2c-address" not in config.keys():
            raise KeyError("Config is missing mandatory field " "i2c-address" ".")

        # check value
        ADConverter.validate_config(config["i2c-address"])

        # channel ##########################

        # key existing?
        if "channel" not in config.keys():
            raise KeyError("Config is missing mandatory field " "channel" ".")

        # check value
        ADConverter._types[config["i2c-address"]].validate_channel(config["channel"])

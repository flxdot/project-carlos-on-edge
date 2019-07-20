#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep
from enum import Enum

from sensors.auxiliary import SmartSensor

def set_max_priority(): pass
def set_default_priority(): pass

def validate_config(config: dict):
    """Checks if all required parameter are available in the passed config dictionary.

    :param config: (mandatory, dict) the config dictionary of the sensor
    :return: None
    :raises ValueError: When the type is not found or a invalid GPIO pin is configured
    :raises KeyError: When a mandatory key in the config dictionary is not available
    """

    if 'type' not in config.keys():
        raise KeyError('Config dictionary is missing mandatory field ''type''.')

    # check if the DHT type is correct
    try:
        DHTtype.from_val(config['type'])

        # check if the gpio-pin property is available
        if 'gpio-pin' not in config.keys():
            raise KeyError('Config dictionary is missing mandatory field ''gpio-pin''.')

        if config['gpio-pin'] not in list(range(1, 27)):
            the_pin = config['gpio-pin']
            raise ValueError(f'{the_pin} is not a valid GPIO pin. Please select any from 1 to 27.')

    except TypeError:
        raise ValueError('Temperature sensor type invalid.')
    except ValueError:
        raise ValueError('Temperature sensor type invalid.')


def get_sensor(config: dict):
    """Returns a instance of a Light sensor based on the given type

    :param type: (mandatory, dict) the config dictionary defining the temperature sensor
    :return: None
    :raises ValueError: When the passed type was not found.
    """

    try:
        return DHT(dht_type=DHTtype.from_val(config['type']),
                   pin=config['gpio-pin'])
    except TypeError:
        return None
    except ValueError:
        return None
    except KeyError:
        return None


class DHTtype(Enum):

    DHT11 = 0
    DHT22 = 1

    @classmethod
    def from_val(cls, val):
        """Return an instance of the DHTtype based on the input

        :param val: (mandatory, DHTtype, str, int, float) the value which shall be interpreted as DHTtype.
        :return: DHTtype
        :raises TypeError: When val is of any other type than the described above.
        """

        if isinstance(val, DHTtype):
            return val
        elif isinstance(val, str):
            return DHTtype.from_str(val)
        elif isinstance(val, (int, float)):
            return DHTtype.from_num(val)
        else:
            TypeError(f'Can not determine the DHT type from input of type {type(val).__name__}.')

    @classmethod
    def from_str(cls, val: str):
        """Return an instance of the DHTtype based on the given string.

        :param val: (mandatory, str) the value which shall be interpreted as DHTtype.
        :return: DHTtype
        :raises TypeError: When val is of any other type than the described above.
        :raises ValueError: When the val can not be interpreted
        """

        if not isinstance(val, str):
            raise TypeError(f'This method is used to determine the DHT type based on a str input. You passed a value of '
                            f'type ''{type(val).__name__}''.')

        # allow case insensitive
        val = val.lower()

        if val == '11' or val == 'dht11':
            return DHTtype.DHT11
        elif val == '22' or val == 'dht22':
            return DHTtype.DHT22
        else:
            raise ValueError(f'Unknown DHT Type ''{val}''.')

    @classmethod
    def from_num(cls, val: [float, int]):
        """Return an instance of the DHTtype based on the given number.

        :param val: (mandatory, int or float) the value which shall be interpreted as DHTtype.
        :return: DHTtype
        :raises TypeError: When val is of any other type than the described above.
        :raises ValueError: When the val can not be interpreted
        """

        if not isinstance(val, (int, float)):
            raise TypeError(
                f'This method is used to determine the DHT type based on a int or float input. You passed a value of '
                f'type ''{type(val).__name__}''.')

        # allow case insensitive
        val = val.lower()

        if val == 11:
            return DHTtype.DHT11
        elif val == 22:
            return DHTtype.DHT22
        else:
            raise ValueError(f'Unknown DHT Type ''{val}''.')


class DHT(SmartSensor):
    """Code for Temperature & Humidity Sensor of Seeed Studio.

    Code is originally from, but modified to my needs:
    http://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/
    """

    PULSES_CNT = 41

    MAX_CNT = 320

    def __init__(self, dht_type: [DHTtype, str, int], pin: int):
        """

        :param dht_type: either DHTtype.DHT11 or DHTtype.22
        :param pin: gpio pin where the sensor is connected to
        """

        # store the pin and type
        self.pin = pin
        self.dht_type = dht_type

        # setup the GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)

    @property
    def dht_type(self):
        return self._dht_type

    @dht_type.setter
    def dht_type(self, type):
        self._dht_type = DHTtype.from_val(type)
        self._last_temp = 0.0
        self._last_humi = 0.0

    def _read(self):
        """Internal read method.

        :returns (humidity in %, temperature in °C)"""

        # Send Falling signal to trigger sensor output data
        # Wait for 20ms to collect 42 bytes data
        GPIO.setup(self.pin, GPIO.OUT)
        set_max_priority()

        GPIO.output(self.pin, GPIO.HIGH)
        sleep(.2)

        GPIO.output(self.pin, GPIO.LOW)
        sleep(.018)

        GPIO.setup(self.pin, GPIO.IN)

        # a short delay needed
        for i in range(10):
            pass

        # pullup by host 20-40 us
        count = 0
        while GPIO.input(self.pin):
            count += 1
            if count > self.MAX_CNT:
                # print("pullup by host 20-40us failed")
                set_default_priority()
                return None, "pullup by host 20-40us failed"

        pulse_cnt = [0] * (2 * self.PULSES_CNT)
        fix_crc = False
        for i in range(0, self.PULSES_CNT * 2, 2):
            while not GPIO.input(self.pin):
                pulse_cnt[i] += 1
                if pulse_cnt[i] > self.MAX_CNT:
                    # print("pulldown by DHT timeout %d" % i))
                    set_default_priority()
                    return None, "pulldown by DHT timeout {}".format(i)

            while GPIO.input(self.pin):
                pulse_cnt[i + 1] += 1
                if pulse_cnt[i + 1] > self.MAX_CNT:
                    # print("pullup by DHT timeout {}".format((i + 1)))
                    if i == (self.PULSES_CNT - 1) * 2:
                        # fix_crc = True
                        # break
                        pass
                    set_default_priority()
                    return None, "pullup by DHT timeout {}".format(i)

        # back to normal priority
        set_default_priority()

        total_cnt = 0
        for i in range(2, 2 * self.PULSES_CNT, 2):
            total_cnt += pulse_cnt[i]

        # Low level ( 50 us) average counter
        average_cnt = total_cnt / (self.PULSES_CNT - 1)
        # print("low level average loop = {}".format(average_cnt))

        data = ''
        for i in range(3, 2 * self.PULSES_CNT, 2):
            if pulse_cnt[i] > average_cnt:
                data += '1'
            else:
                data += '0'

        data0 = int(data[0: 8], 2)
        data1 = int(data[8:16], 2)
        data2 = int(data[16:24], 2)
        data3 = int(data[24:32], 2)
        data4 = int(data[32:40], 2)

        if fix_crc and data4 != ((data0 + data1 + data2 + data3) & 0xFF):
            data4 = data4 ^ 0x01
            data = data[0: self.PULSES_CNT - 2] + ('1' if data4 & 0x01 else '0')

        if data4 == ((data0 + data1 + data2 + data3) & 0xFF):
            if self._dht_type == DHTtype.DHT11:
                humi = int(data0)
                temp = int(data2)
            elif self._dht_type == DHTtype.DHT22:
                humi = float(int(data[0:16], 2) * 0.1)
                temp = float(int(data[17:32], 2) * 0.2 * (0.5 - int(data[16], 2)))
        else:
            # print("checksum error!")
            return None, "checksum error!"

        return humi, temp

    def read(self, retries=15):
        for i in range(retries):
            humi, temp = self._read()
            if not humi is None:
                break
        if humi is None:
            return self._last_humi, self._last_temp
        self._last_humi, self._last_temp = humi, temp
        return humi, temp


    def measure(self):
        """Performs a measurement and returns all available values in a dictionary.
        The keys() are the names of the measurement and the values the corresponding values.

        :return: dict
        """

        humi, temp = self.read()
        if humi == 0 and temp == 0:
            return {'humidity': None, 'temperature': None}
        return {'humidity': float(humi), 'temperature': float(temp)}

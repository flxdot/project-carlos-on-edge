#!/usr/bin/python
import RPi.GPIO as GPIO
import time

from Auxiliary import Timer
from ifcInflux import InfluxAttachedSensor, get_client
from sensors.auxiliary import SmartSensor
from sensors.distance import SeeedUltraSonicRanger


class PumpControl():
    """"""

    def __init__(self, config: dict):
        """

        :param config: (mandatory, dictionary)
        """

        self.pump_jobs = list()

        # dictionary of available pumps
        self.pumps = dict()
        for pump in config['pumps']:
            name = list(pump.keys())[0]
            self.pumps[name] = Pump(name=name, config=pump[name], main_config=config)

    def add_job(self, pump: str, valve: int, duration: [float, int]):
        """

        :param pump: (mandatory, str) name of the pump
        :param valve: (mandatory, int) gpio pin of the valve
        :param duration: (mandatory, float or int) duration where the pump shall be active in seconds
        :return: true when the job could be created successfully
        """

        if pump not in self.pumps.keys():
            return False

        try:
            self.pump_jobs.append(PumpJob(pump=pump, valve=valve, duration=duration))
        except Exception:
            return False
        return True

    def start(self):
        """Starts the data acquisition of the environment."""

        for sensor in self.pumps.values():
            sensor.start()

    def stop(self):
        """Stops the data acquisition of the environment."""

        for sensor in self.pumps.values():
            sensor.stop()

    def join(self):
        """Wait for all sensors to stop the data acquisition."""

        for sensor in self.pumps.values():
            sensor.join()

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: When the mandatory pumps keys is not available in the config
        """

        if 'pumps' not in config:
            raise KeyError('The config did not contain the mandatory section ''pumps''.')

        for pump in config['pumps']:
            Pump.validate_config(pump)


class Pump(Timer):

    def __init__(self, name: str, config: dict, main_config: dict):
        """

        :param name: (mandatory, str) The name of the pump
        :param config: (mandatory, dictionary) the config of the irrigation loop
        :param main_config: (mandatory, dictionary) the general config (required to build a db client)
        """

        super().__init__(name=f'pump-{name}', period=60)

        # get the tank level
        self.tank_level = InfluxAttachedSensor(name=f'water-level', period=60, measurement=f'pump-{name}',
                                               sensor=WaterTank(config['water-tank']),
                                               dbclient=get_client(main_config))

        self.pin = config['gpio-pin']

    def timer_fcn(self):
        """

        :return:
        """

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Key is missing from config
        :raises ValueError: Configuration is wrong.
        """

        if 'gpio-pin' not in config:
            raise KeyError('Mandatory section ''gpio-pin'' is missing in the config.')

        if config['gpio-pin'] < 4 or config['gpio-pin'] > 27:
            raise ValueError(f'Can not use gpio-pins {config["gpio-pin"]} as digital input. Check the GPIO layout of '
                             f'your raspberry. And note that pin 1 & 2 is used for I2C bus.')

        if 'water-tank' not in config:
            raise KeyError('Mandatory section ''water-tank'' is missing in the config.')

        WaterTank.validate_config(config['water-tank'])


class PumpJob():

    def __init__(self, pump: Pump, valve: int, duration: [float, int]):
        """

        :param pump: (mandatory, Pump) the actual class of the pump
        :param valve: (mandatory, int) gpio pin of the valve
        :param duration: (mandatory, float or int) duration where the pump shall be active in seconds
        :return: true when the job could be created
        """

        self.pump = pump
        self.valve = valve
        self.duration = duration

        # setup the GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pump.pin, GPIO.OUT)
        GPIO.setup(self.valve, GPIO.OUT)

    def execute(self):
        """Executes the pump job."""

        # get the current water level
        self.pump.tank_level.timer_fcn()

        # open the value first to allow the water to flow as soon as the pump runs
        GPIO.output(self.valve, GPIO.LOW)

        # start the pump
        GPIO.output(self.pump.pin, GPIO.LOW)

        # wait the wanted time
        time.sleep(self.duration)

        # close the valve first to shut down the flow as fast as possible
        GPIO.output(self.valve, GPIO.HIGH)

        # stop the pump
        GPIO.output(self.pump.pin, GPIO.HIGH)

        # get the current water level after the pump has stopped
        self.pump.tank_level.timer_fcn()


class WaterTank(SmartSensor):
    """

    """

    def __init__(self, config: dict):
        """

        :param config: (mandatory, dict) the dictionary defining the pump tank
        """

        self.level_warning = config['low-level-warning']
        self.level_alarm = config['low-level-alarm']
        self.level_sensor = SeeedUltraSonicRanger(config['gpio-pin'])

    def get_level(self):
        """Get the tank level, low level warning and low level alarm.

        :return: tuple (level, warning, alarm)
        """

        # make a reading of the sensor
        level = self.level_sensor.get_distance()
        # make sure the measurement is valid
        if level:
            return level, level < self.level_warning, level < self.level_alarm
        return None, None, None

    def measure(self):
        """Performs a measurement and returns all available values in a dictionary.
        The keys() are the names of the measurement and the values the corresponding values.

        :return: dict
        """

        level, warning, alarm = self.get_level()

        return {
            'level': level,
            'low-level-warning': warning,
            'low-level-alarm': alarm,
        }

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Key is missing from the config
        :raises ValueError: The configured values are invalid
        """

        # check if everything is available
        sections = ['gpio-pin', 'low-level-warning', 'low-level-alarm']
        for section in sections:
            if section not in config:
                raise KeyError(f'Mandatory section {section} is missing in the config.')

        # check the values of the gpio-pin
        if config['gpio-pin'] < 4 or config['gpio-pin'] > 27:
            raise ValueError(f'Can not use gpio-pins {config["gpio-pin"]} as digital input. Check the GPIO layout of '
                             f'your raspberry. And note that pin 1 & 2 is used for I2C bus.')

        # check the plausibility of the of the low-level thresholds
        if config['low-level-alarm'] < 0:
            raise ValueError('The water tank low level alarm can not be set to a negative value.')

        if config['low-level-warning'] < config['low-level-alarm']:
            raise ValueError('The water tank low level warning can not be smaller than the low level alarm.')

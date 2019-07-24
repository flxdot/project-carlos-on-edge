#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import datetime
from threading import Lock

from Auxiliary import Timer
from ifcInflux import InfluxAttachedSensor, get_client
from sensors.auxiliary import SmartSensor
from sensors.distance import SeeedUltraSonicRanger


class PumpControl():
    """
    The PumpControl hosts all configured pumps and takes care that the pump job will be executed
    """

    class __PumpControl(Timer):

        def __init__(self, config: dict):
            """

            :param config: (mandatory, dictionary)
            """

            # set the period to one to make sure to execute the pump jobs as fast as possible
            super().__init__(name='PumpControl', period=1)

            # the lock to sync the threads
            self._job_lock = Lock()

            # the list of pumps jobs which need to be carried out
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

            # create new pump job
            try:
                pj = PumpJob(pump=self.pumps[pump], valve=valve, duration=duration)
            except Exception:
                return False

            # add the job to the list of jobs
            with self._job_lock:
                self.pump_jobs.append(pj)
                return True

            return False

        def start(self):
            """Starts the cyclic work of each pump."""

            # start the pumps
            for pump in self.pumps.values():
                pump.start()

            # call the start of the thread
            super().start()

        def stop(self):
            """Stops the cyclic work of each pump."""

            for pump in self.pumps.values():
                pump.stop()

        def join(self):
            """Wait for pumps to be finished with their cyclic work."""

            for pump in self.pumps.values():
                pump.join()

            super().join()

        def timer_fcn(self):
            """Will regularly check for new pump jobs. And execute them.

            :return: None
            """

            # get copy of job list
            with self._job_lock:
                # empty the class wide job que
                cur_jobs = self.pump_jobs[:]
                self.pump_jobs = list()

            # execute the local job que
            for job in cur_jobs:
                job.execute()
                # wait at least 1 second before executing the next job
                time.sleep(1)

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

    instance = None

    def __new__(cls, config = None):  # __new__ always a classmethod
        if not PumpControl.instance:
            if config is None:
                from CarlosOnEdge import CarlosOnEdge
                config = CarlosOnEdge.config
            PumpControl.instance = PumpControl.__PumpControl(config)
        return PumpControl.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)


class Pump:

    def __init__(self, name: str, config: dict, main_config: dict):
        """

        :param name: (mandatory, str) The name of the pump
        :param config: (mandatory, dictionary) the config of the irrigation loop
        :param main_config: (mandatory, dictionary) the general config (required to build a db client)
        """

        super().__init__()

        #
        self.measurement = f'pump-{name}'
        self._dbclient = get_client(main_config)
        self._active = False

        # get the tank level
        self.tank_level = InfluxAttachedSensor(name=f'water-level', period=60, measurement=self.measurement,
                                               sensor=WaterTank(config['water-tank']),
                                               dbclient=self._dbclient)

        self.pin = config['gpio-pin']

        # setup the GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)

    def activate(self):
        """Activates the pump: Start the flow of water"""

        # get the current water level
        self.tank_level.record_measurement()

        # set the active flag (this will also write the status to the DB)
        self.active = True

        # activate the pump
        GPIO.output(self.pin, GPIO.LOW)


    def deactivate(self):
        """Deactivates the pump: Stops the flow of water."""

        # deactivate the pump
        GPIO.output(self.pin, GPIO.HIGH)

        # set the active flag (this will also write the status to the DB)
        self.active = False

        # get the current water level
        self.tank_level.record_measurement()

    def _write_status(self):
        """Writes the current status to the db."""

        # write active flag to the db
        self._dbclient.write_points(self._get_status_for_db())

    def _get_status_for_db(self):
        """Return the json object which is written to the database."""

        return [
            {
                "measurement": self.measurement,
                "tags": {},
                "time": str(datetime.datetime.now(datetime.timezone.utc)),
                "fields": {
                    "active": self.active,
                }
            }
        ]

    def start(self):
        """Starts the data tank level measurements."""

        self.tank_level.start()

    def stop(self):
        """Stops the tank level measurements."""

        self.tank_level.stop()

    def join(self):
        """Wait for all threads to be finished."""

        self.tank_level.join()

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        status_data = self._get_status_for_db()  # get old status
        self._active = val
        status_data += self._get_status_for_db()  # get new status
        self._dbclient.write_points(status_data)

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Key is missing from config
        :raises ValueError: Configuration is wrong.
        """

        name = list(config.keys())[0]
        config = config[name]

        if 'gpio-pin' not in config:
            raise KeyError(f"Mandatory section 'gpio-pin' is missing in the config for pump {name}.")

        if config['gpio-pin'] < 4 or config['gpio-pin'] > 27:
            raise ValueError(f'Can not use gpio-pins {config["gpio-pin"]} as digital input for pump {name}. '
                             f'Check the GPIO layout of your raspberry. And note that pin 1 & 2 is used for I2C bus.')

        if 'water-tank' not in config:
            raise KeyError(f"Mandatory section 'water-tank'' is missing in the config for pump {name}.")

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
        GPIO.setup(self.valve, GPIO.OUT)

    def execute(self):
        """Executes the pump job."""

        # open the value first to allow the water to flow as soon as the pump runs
        GPIO.output(self.valve, GPIO.LOW)

        # start the pump
        self.pump.activate()

        # wait the wanted time
        time.sleep(self.duration)

        # close the valve first to shut down the flow as fast as possible
        GPIO.output(self.valve, GPIO.HIGH)

        # stop the pump
        self.pump.deactivate()


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

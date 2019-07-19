#!/usr/bin/python

import os
import abc
import time
import logging
import logging.handlers
from threading import Thread, Event, Lock

class Timer(Thread):
    """The Timer is used to perform periodic tasks."""

    def __init__(self, name: str, period: [float, int]):
        """

        :param name: (mandatory, string) name of the timer
        :param period: (mandatory, float or int) timer period in seconds
        """

        # init Thread super class
        super().__init__(name=name)

        # some internal attributes
        self._timer_period = period
        self._timer_lock = Lock()
        self._timer_stop = Event()
        self._timer_next_execution = time.time()
        self._timer_logger = get_logger(f'Timer_{name}', level=logging.WARNING)

    def run(self):
        """The Thread method."""

        # store information about the next call
        self._timer_next_execution = time.time()

        # run until the timer is marked to be destroyed
        while not self._timer_stop.is_set():
            try:
                self.timer_fcn()
            except Exception:
                self._timer_logger.exception('Unknown exception while executing ''timer_fcn()''.')

            # sleep until the next execution is due
            with self._timer_lock:
                self._timer_next_execution = self._timer_next_execution + self._timer_period
            sleep_time = self._timer_next_execution - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                self._timer_logger.warning(f'Exceeded timer period by {abs(sleep_time)*1000:.2f}ms.')

    def set_period(self, period: [float, int]):
        """Change the current timer period to the wanted value.

        :param period: (mandatory, float or int) timer period in seconds
        :return:
        """

        with self._timer_lock:
            self._timer_period = period

    @abc.abstractmethod
    def timer_fcn(self):
        """The timer_fcn will be called periodically with the defined period.

        :return:
        """
        pass


class DbAttachedSensor(Timer):
    """The DBAttachedSensor is the super class for all sensors which some how sendint their data to any type of
     database."""

    def __init__(self, name: str, period: [float, int], sensor):
        """Constructor ot the DbAttachedSensor class. Please specify a unique name and a wanted sample period.

        :param name: (mandatory, str) name of the sensor
        :param period: (mandatory, float or int) the wanted data acquisition period of the sensor data in seconds.
        :param sensor: (mandatory, sensors.auxiliary.SmartSensor) The actual class of the sensor.
        """

        if sensor is None:
            raise ValueError('The input Sensor can not be of NoneType.')

        super().__init__(name=name, period=period)

        # store the handle to the sensor
        self.sensor = sensor

        # todo: increase log level
        self.logger = get_logger(name, level=logging.DEBUG)

        # the database data of the sensor
        self._db_data = None

    def timer_fcn(self):
        """The actual work of the sensor of gathering data and sending it to the database."""

        # get the data
        try:
            self.measure()
        except Exception:
            self.logger.exception(f'{self.name}: Unknown error while gathering measurement data.')
            return None

        # write the data to the database
        try:
            self.write_db()
        except Exception:
            self.logger.exception(f'{self.name}: Unknown error while writing measurement data to database.')
            return None

    @abc.abstractmethod
    def measure(self):
        """Performs a measurement and stores the obtained data in the _db_data field.

        :return:
        """
        pass

    @abc.abstractmethod
    def write_db(self):
        """Write the data stored in the _db_data field into the data base.

        :return:
        """
        pass

def get_logger(name, level=logging.DEBUG, path=os.path.join(os.getcwd(), 'log')):
    """

    :param name: (mandatory, string) name of the logger
    :param level: (optional, default: logging.DEBUG) the logging level
    :param path: (optional, default: './log/') path to the log files
    :return: logging.Logger
    """

    the_logger = logging.Logger(name=name, level=level)

    # check path
    if not os.path.isdir(path):
        os.makedirs(path)

    # create formatter
    format_str = '%(asctime)s.%(msecs)03d - %(levelname)-8s - %(message)s'
    date_format = '%Y-%d-%m %H:%M:%S'
    formatter = logging.Formatter(format_str, date_format)

    # add stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    the_logger.addHandler(stream_handler)

    # time rotating file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(path, f'{name}.log'),
                                       when="midnight",
                                       interval=1,
                                       backupCount=7)
    the_logger.addHandler(file_handler)

    return the_logger

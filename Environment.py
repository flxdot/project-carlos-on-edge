#!/usr/bin/python

import time
from sensors.light import validate_config as validate_light_config
from sensors.light import get_sensor as get_light_sensor
from sensors.temperature import validate_config as validate_temp_config
from sensors.temperature import get_sensor as get_temp_sensor
from ifcInflux import InfluxAttachedSensor, get_client

class Environment(object):
    """The Environment will record the environment conditions of the plants like Sunlight intensity, UV index,
    Temperature, Humidity, Weather Forecast.
    """

    def __init__(self, config: dict):
        """

        :param config: (mandatory, dictionary)
        """

        from CarlosOnEdge import SENSOR_PERIOD

        # list of all environment sensors
        self.sensors = list()

        # init all environment sensors
        if 'environment' in config.keys():
            env_cfg = config['environment']

            # uv-light sensor
            if 'uv-light' in env_cfg.keys():
                the_sensor = InfluxAttachedSensor(name='uv-light', period=SENSOR_PERIOD, measurement='environment',
                                                  sensor=get_light_sensor(env_cfg['uv-light']),
                                                  dbclient=get_client(config))
                self.sensors.append(the_sensor)

            # temp & humidity sensor
            if 'temp-humi' in env_cfg.keys():
                the_sensor = InfluxAttachedSensor(name='temp-humi', period=SENSOR_PERIOD, measurement='environment',
                                                  sensor=get_temp_sensor(env_cfg['temp-humi']),
                                                  dbclient=get_client(config))
                self.sensors.append(the_sensor)

            # todo: weather forecast

    def start(self):
        """Starts the data acquisition of the environment."""

        for sensor in self.sensors:
            time.sleep(1)
            sensor.start()

    def stop(self):
        """Stops the data acquisition of the environment."""

        for sensor in self.sensors:
            sensor.stop()

    def join(self):
        """Wait for all sensors to stop the data acquisition."""

        for sensor in self.sensors:
            sensor.join()

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Config is not valid
        """

        # check if the environment key is available in the config
        if 'environment' not in config.keys():
            return None

        # check the config
        env_cfg = config['environment']

        # uv-light sensor
        if 'uv-light' in env_cfg.keys():
            validate_light_config(env_cfg['uv-light'])

        # temp & humidity sensor
        if 'temp-humi' in env_cfg.keys():
            validate_temp_config(env_cfg['temp-humi'])

        # todo: weather forecast

#!/usr/bin/python

import time
from ifcInflux import InfluxAttachedSensor, get_client
from sensors.moisture import CapacitiveSoilMoistureSensor

class Irrigation():
    """"""

    def __init__(self, config: dict):
        """

        :param config: (mandatory, dictionary)
        """

        # list of all irregation loops
        self.loops = dict()

        irrs_cfg = config['irrigation-loops']

        for irr_cfg in irrs_cfg:
            name = list(irr_cfg.keys())[0]
            loop_cfg = irr_cfg[name]
            self.loops[name] = IrrigationLoop(name=name, config=loop_cfg, main_config=config)

    def start(self):
        """Starts the data acquisition of the environment."""

        for sensor in self.loops.values():
            sensor.start()

    def stop(self):
        """Stops the data acquisition of the environment."""

        for loop in self.loops.values():
            loop.stop()

    def join(self):
        """Wait for all sensors to stop the data acquisition."""

        for loop in self.loops.values():
            loop.join()

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Mandatory field is missing
        :raises ValueError: Config value if wrong
        """

        if 'irrigation-loops' not in config.keys():
            raise KeyError('Mandatory section \'irrigation-loops\' is missing in the config.')

        irrs_cfg = config['irrigation-loops']

        for irr_cfg in irrs_cfg:
            IrrigationLoop.validate_config(irr_cfg)


class IrrigationLoop():

    def __init__(self, name: str, config: dict, main_config: dict):
        """

        :param name: (mandatory, str) The name if the irrigation loop
        :param config: (mandatory, dictionary) the config of the irrigation loop
        :param main_config: (mandatory, dictionary) the general config (required to build a db client)
        """
        from CarlosOnEdge import SENSOR_PERIOD

        self.name = name

        # define the measurement name
        measurement = f'irrigation-loop-{name}'

        # the moisture sensor
        self.moisture_sensor = InfluxAttachedSensor(name=f'{name}-moisture-sensor', period=SENSOR_PERIOD, measurement=measurement,
                                                    sensor=CapacitiveSoilMoistureSensor.from_config(
                                                        config['moisture-sensor']),
                                                    dbclient=get_client(main_config))

        # the pump

        # the valve

        # the watering rules

    def start(self):
        """Starts the data acquisition of the irrigation loop."""

        self.moisture_sensor.start()

    def stop(self):
        """Stops the data acquisition of the irrigation loop."""

        self.moisture_sensor.stop()

    def join(self):
        """Wait for all sensors to stop the data acquisition."""

        self.moisture_sensor.join()

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Mandatory field is missing
        :raises ValueError: Config value if wrong
        """

        # name
        name = list(config.keys())[0]
        loop_cfg = config[name]

        # moisture-sensor
        if 'moisture-sensor' not in loop_cfg.keys():
            raise KeyError(f'Mandatory section \'moisture-sensor\' is missing for irrigation-loop {name}.')

        CapacitiveSoilMoistureSensor.validate_config(loop_cfg['moisture-sensor'])

        # pump

        # valve-gpio

        # watering-rules

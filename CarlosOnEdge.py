#!/usr/bin/python

import time
import os
import yaml
import ifcInflux
from Environment import Environment
from Irrigation import Irrigation
from Pump import PumpControl
from sensors.i2c import i2cLock

SENSOR_PERIOD = 5

class CarlosOnEdge():
    """CarlosOnEdge will take of all those jobs which are not done in the cloud:
        - gathering information about the plants (moisture level)
        - gathering information about the plant environments (Sunlight, weather, etc.)
        - watering your plants
    """

    class __CarlosOnEdge():
        """Private member of the CarlosOnEdge to make sure the CarlosOnEdge is Singleton."""

        def __init__(self, config_file: str = 'config.yaml'):
            """

            :param config_file: (optional, str) path to the config file. Default is: config.yaml
            """

            # acquire the lock once
            self._i2c_lock = i2cLock()

            # config ###############################

            # does the file exist?
            if not os.path.exists(config_file):
                raise FileNotFoundError('The config file ''config.yaml'' could not be located. '
                                        'Make sure to create one with the syntax described in the documentation.')

            # store the inputs
            self._cfg_file = config_file

            with open('config.yaml', 'r') as document:
                self.config = yaml.safe_load(document)

            # valid date the config
            CarlosOnEdge.validate_config(self.config)

            # create classes ########################

            self.environment = Environment(self.config)

            # create the pump controller before the irrigation loops!
            self.pump_controller = PumpControl(self.config)

            self.irrigation_loops = Irrigation(self.config)

        def start(self):
            """Vamos! Let carlos start its work.

            - start environment data acquisition
            - start irrigation loops
            - start the pump controller
            """

            self.environment.start()
            self.irrigation_loops.start()
            self.pump_controller.start()

        def stop(self):
            """Tops the data acquisition, moisture control and pump controls"""

            self.environment.stop()
            self.irrigation_loops.stop()
            self.pump_controller.stop()

        def wait(self):
            """Wait until carlos has done it's job.

            Note: This will never be the case since carlos will wait for all """


            self.environment.join()
            self.irrigation_loops.join()
            self.pump_controller.join()

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        :param config: (mandatory, dict) the loaded config as dictionary
        """

        # influxdb
        ifcInflux.validate_config(config)

        # environment
        Environment.validate_config(config)

        # irrigation-loops
        Irrigation.validate_config(config)

        # pumps
        PumpControl.validate_config(config)

    instance = None

    def __new__(cls):  # __new__ always a classmethod
        if not CarlosOnEdge.instance:
            CarlosOnEdge.instance = CarlosOnEdge.__CarlosOnEdge()
        return CarlosOnEdge.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)



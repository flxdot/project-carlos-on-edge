#!/usr/bin/python


class PumpControl():
    """"""

    def __init__(self, config: dict):
        """

        :param config: (mandatory, dictionary)
        """

        # dictionary of available pumps
        self.pumps = dict()

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
        """


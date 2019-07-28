import abc

SENSOR_PERIOD = 5

class SmartSensor():
    """The SmartSensor is the superclass of every available sensor. It unifies the interface by providint a measure()
    method which will return a dictionary with the recent measurements in a dictionary. The keys() are the names of the
    measurement and the values the corresponding values.
    """

    @abc.abstractmethod
    def measure(self):
        """Performs a measurement and returns all available values in a dictionary.
        The keys() are the names of the measurement and the values the corresponding values.

        :return: dict
        """
        pass

import os
import yaml
import InfluxClient

class CarlosOnEdge():
    class __CarlosOnEdge():
        """

        """

        def __init__(self, config_file: str = 'config.yaml'):
            """

            :param config_file: (optional, str) path to the config file. Default is: config.yaml
            """

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

            self.db_con = InfluxClient.get_client(self.config)

            #

        @staticmethod
        def validate_config(config: dict):
            """Checks whether the config is valid. If the config does not contain valid information, a exception will be
            raised.

            :param config: (mandatory, dict) the loaded config as dictionary
            """

            # check influx config
            InfluxClient.validate_config(config)

    instance = None

    def __new__(cls):  # __new__ always a classmethod
        if not CarlosOnEdge.instance:
            CarlosOnEdge.instance = CarlosOnEdge.__CarlosOnEdge()
        return CarlosOnEdge.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)



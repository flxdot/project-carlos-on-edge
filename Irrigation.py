#!/usr/bin/python

import time

from Auxiliary import Timer, convert_to_seconds
from ifcInflux import InfluxAttachedSensor, get_client
from sensors.moisture import CapacitiveSoilMoistureSensor


class Irrigation():
    """"""

    def __init__(self, config: dict, pump_controller):
        """

        :param config: (mandatory, dictionary)
        :param pump_controller: (mandatory, PumpController) The pump controller
        """

        # list of all irregation loops
        self.loops = dict()
        self.pump_controller = pump_controller

        irrs_cfg = config['irrigation-loops']

        for irr_cfg in irrs_cfg:
            name = list(irr_cfg.keys())[0]
            loop_cfg = irr_cfg[name]
            self.loops[name] = IrrigationLoop(name=name, config=loop_cfg, main_config=config,
                                              pump_controller=pump_controller)

    def start(self):
        """Starts the data acquisition of the environment."""

        for loop in self.loops.values():
            loop.start()

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


class IrrigationLoop(Timer):

    def __init__(self, name: str, config: dict, main_config: dict, pump_controller):
        """

        :param name: (mandatory, str) The name of the irrigation loop
        :param config: (mandatory, dictionary) the config of the irrigation loop
        :param main_config: (mandatory, dictionary) the general config (required to build a db client)
        :param pump_controller: (mandatory, PumpController) The pump controller
        """
        from CarlosOnEdge import SENSOR_PERIOD

        super().__init__(name=name, period=60)

        self.pump_controller = pump_controller

        # define the measurement name
        self.measurement = f'irrigation-loop-{name}'

        # the db client read data
        self.db_df_client = get_client(main_config)

        # the moisture sensor
        self.moisture_sensor = InfluxAttachedSensor(name=f'{name}-moisture-sensor', period=SENSOR_PERIOD,
                                                    measurement=self.measurement,
                                                    sensor=CapacitiveSoilMoistureSensor.from_config(
                                                        config['moisture-sensor']),
                                                    dbclient=get_client(main_config))

        # the pump
        self.pump_name = config['pump']
        self.pump = self.pump_controller.pumps[self.pump_name]
        # the last time the pump was active
        self.last_pump_actv = 0

        # the valve
        try:
            self.valve_pin = config['valve-gpio']
        except KeyError:
            self.valve_pin = None

        # the watering rules
        self.watering_rule = WateringRule(irrigation_loop=self, config=config['watering-rule'])

    def start(self):
        """Starts the data acquisition of the irrigation loop."""

        self.moisture_sensor.start()

        super().start()

    def stop(self):
        """Stops the data acquisition of the irrigation loop."""

        self.moisture_sensor.stop()

    def join(self):
        """Wait for all sensors to stop the data acquisition."""

        self.moisture_sensor.join()

    def timer_fcn(self):
        """Check the watering rule."""

        # make sure to obey the time out after an pump job has been successfully submitted
        if time.time() - self.last_pump_actv < self.watering_rule.interval:
            return

        # get the query string
        field = f'{self.moisture_sensor.name}-percentage'
        query = self.watering_rule.build_query(measurement=self.measurement, field=field)
        res = self.db_df_client.query(query)
        data = res[self.measurement]

        # get data as list
        data_list = list()
        for sample in list(data):
            data_list.append(sample[field])

        # check if all data points are smaller as the wanted threshold
        if self.watering_rule.check_moisture(data_list):
            # create a new pump job and submit it afterwards
            if self.pump_controller.add_job(pump=self.pump_name, valve=self.valve_pin,
                                            duration=self.watering_rule.time):
                # set the time stamp of the last successful pump job submission
                self.last_pump_actv = time.time()

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

        # check if all required keys are available
        av_keys = loop_cfg.keys()
        req_keys = ['moisture-sensor', 'pump', 'watering-rule']
        missing_keys = list()
        for key in req_keys:
            if key not in av_keys:
                missing_keys.append(key)

        if missing_keys:
            missing_keys = [f"'{key}'" for key in missing_keys]
            raise KeyError(f"Mandatory section {', '.join(missing_keys)} is missing for irrigation-loop {name}.")

        # moisture-sensor
        CapacitiveSoilMoistureSensor.validate_config(loop_cfg['moisture-sensor'])

        # watering-rules
        WateringRule.validate_config(loop_cfg['watering-rule'])


class WateringRule():

    def __init__(self, irrigation_loop: IrrigationLoop, config: dict):
        """

        :param name: (mandatory, str) the name of the watering rule
        """

        self.irrigation_loop = irrigation_loop

        # the low level of the moisture sensor
        self.trigger_low_level = config['trigger']['low-level']
        # the time in seconds where the moisture level has to less than the trigger_low_level in seconds
        self.trigger_time = convert_to_seconds(config['trigger']['time'])
        # the time where the pump shall be activated in case the moisture level is too low in seconds
        self.time = convert_to_seconds(config['time'])
        # the minimal time between two consecutive pump activations in seconds
        self.interval = convert_to_seconds(config['interval'])

    def build_query(self, measurement: str, field: str) -> str:
        """The Query string which can be used to check the watering rule.

        :param measurement: (mandatory, str) the name of the measurement
        :param field: (mandatory, str) the name of the field.
        :returns str: The query string to check the watering rule
        """

        return f'SELECT "{field}" from "{measurement}" WHERE time > now() - {int(self.trigger_time)}s'

    def check_moisture(self, moisture_data: list):
        """Checks whether all of the given

        :param moisture_data: (mandatory, list) the moisture levels
        :return bool: True when the moisture level has been violated.
        """

        # moisture level is stored in % 0-1 and the low level is stored in % 0-100
        return all([val * 100 < self.trigger_low_level for val in moisture_data])

    @staticmethod
    def validate_config(config: dict):
        """Checks whether the config is valid. If the config does not contain valid information, a exception will be
        raised.

        example config:

            watering-rule:
              trigger:
                low-level: 38
                time: 30m
              time: 3s
              interval: 15m

        :param config: (mandatory, dict) the loaded config as dictionary
        :raises KeyError: Mandatory field is missing
        :raises ValueError: Config value if wrong
        """

        # check if all required keys are available
        av_keys = config.keys()
        req_keys = ['trigger', 'time', 'interval']
        missing_keys = list()
        for key in req_keys:
            if key not in av_keys:
                missing_keys.append(key)

        if missing_keys:
            missing_keys = [f"'{key}'" for key in missing_keys]
            raise KeyError(f"Mandatory section {', '.join(missing_keys)} is missing for watering-rule.")

        # check the trigger
        if 'low-level' not in config['trigger']:
            raise KeyError(f"Mandatory section 'low-level' is missing for watering-rules trigger.")
        if 'time' not in config['trigger']:
            raise KeyError(f"Mandatory section 'time' is missing for watering-rules trigger.")

        # check values
        if config['trigger']['low-level'] < 0 or config['trigger']['low-level'] > 100:
            raise ValueError('Trigger low-level has to be in between 0 and 100.')
        try:
            convert_to_seconds(config['trigger']['time'])
        except (KeyError, ValueError):
            raise ValueError(f"Configured trigger time '{config['trigger']['time']}' of the watering-rule could not be "
                             f"interpreted.")
        try:
            convert_to_seconds(config['time'])
        except (KeyError, ValueError):
            raise ValueError(f"Configured time '{config['time']}' of the watering-rule could not be "
                             f"interpreted.")
        try:
            convert_to_seconds(config['interval'])
        except (KeyError, ValueError):
            raise ValueError(f"Configured interval '{config['interval']}' of the watering-rule could not be "
                             f"interpreted.")

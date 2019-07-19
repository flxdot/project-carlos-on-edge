#!/usr/bin/python

from datetime import datetime, timezone

from influxdb import InfluxDBClient
from Auxiliary import DbAttachedSensor


def validate_config(config: dict):
    """Checks if all required parameter are available in the passed config dictionary.

    :param config_file: (mandatory, dict) dictionary holding the config
    :return: None
    :raises: KeyError
    """

    # check if the influxdb key is available in the config
    if 'influxdb' not in config.keys():
        raise KeyError('The loaded config did not contain the mandatory field ''influxdb''.')

    # check the config
    cfg_db = config['influxdb']

    # check for missing keys
    missing_fields = list()
    mandatory_fields = ['host', 'user', 'password', 'database']
    for field in mandatory_fields:
        if field not in cfg_db.keys():
            missing_fields.append(field)

    # are there any missing fields?
    if missing_fields:
        missing_fields = ', '.join([f'\'{x}\'' for x in missing_fields])
        raise KeyError(f'Could not find {missing_fields} of the influx db. Please validate the config file.')


def get_client(config: dict):
    """Creates a client based on the passed config dictionary.

    :param config: (mandatory, dict) the loaded configuration.
    :return: InfluxDBClient
    """

    cfg_db = config['influxdb']

    # check for optional port
    if 'port' in cfg_db.keys():
        port = cfg_db['port']
    else:
        port = 8086

    # create influx db client
    dbclient = InfluxDBClient(host=cfg_db['host'], port=port, username=cfg_db['user'], password=cfg_db['password'])

    # make sure the data base exists (if database exists a new will not be created)
    dbclient.query(f"CREATE DATABASE {cfg_db['database']}")

    # select the wanted database
    dbclient.switch_database(cfg_db['database'])

    return dbclient


class InfluxAttachedSensor(DbAttachedSensor):
    """InfluxAttachedSensor is the super class for every sensor which shall write its data to the InfluxDB."""

    def __init__(self, name: str, period: [float, int], measurement: str, sensor, dbclient: InfluxDBClient):
        """

        :param name: (mandatory, str) name of the sensor
        :param period: (mandatory, float or int) the wanted data acquisition period of the sensor data in seconds.
        :param measurement: (mandatory, string) name of the measurement
        :param sensor: (mandatory, sensors.auxiliary.SmartSensor) The actual class of the sensor.
        :param dbclient: (mandatory, InfluxDBClient) the client to the Influx data base. Make sure the database is
        already pre selected!
        """

        super().__init__(name=name, period=period, sensor=sensor)

        # store the db client
        self._dbclient = dbclient
        self._measurement = measurement

        # create dummy of the data
        self._db_data = list()

    def add_data(self, field: (str, list), value, tags=dict(),
                 timestamp=datetime.now(timezone.utc)):
        """Adds data to the internal data buffer.

        Adding a single field:
          my_sensor.add_data('temperature01', 23.4)

        Adding a single field with multiple measurements:
          my_sensor.add_data('temperature01', [23.4, 24.1],
                             timestamp=[datetime.datetime(2019, 7, 23, 19, 32, 34, 0),
                                        datetime.datetime(2019, 7, 23, 19, 32, 35, 0)])

        Adding multiple fields:
          my_sensor.add_data(['temperature01', 'temperature02'], [23.4, 24.1])

        Adding multiple fields with multiple measurements:
          my_sensor.add_data(['temperature01', 'temperature02'],
                             [[23.4, 24.1, 24.5], [56.4, 56.6, 57.0]],
                             timestamp=[datetime.datetime(2019, 7, 23, 19, 32, 34, 0),
                                        datetime.datetime(2019, 7, 23, 19, 32, 35, 0),
                                        datetime.datetime(2019, 7, 23, 19, 32, 36, 0)])

        :param field: (mandatory) the name of the field or fields
        :param value: (mandatory) the measurement values
        :param tags: (optional, dict) dictionary of tags associated with the measurement
        :param timestamp: (optional) utc time stamp or list of utc timestamps
        :raises ValuesError: When list sizes do not agree
        :return:
        """

        # make sure the timestamp is iterable
        if not isinstance(timestamp, list):
            timestamp = [timestamp]
        if not isinstance(value, list):
            value = [value]

        # store each sample
        sample_cnt = len(timestamp)
        for idx, tstamp in enumerate(timestamp):
            # create new sample
            cur_sample = dict()
            # set the measurement
            cur_sample['measurement'] = self._measurement
            # set the tags
            cur_sample['tags'] = tags
            # set the timestamp
            cur_sample['time'] = str(tstamp)
            print(tstamp)

            # single field?
            fields = dict()
            if isinstance(field, list):
                for field_idx, cur_field in enumerate(field):
                    cur_val = value[field_idx]
                    if sample_cnt == 1:
                        fields[cur_field] = value[field_idx]
                    elif len(cur_val) < idx:
                        raise ValueError('Found different number of values and timestamps!')
                    elif isinstance(cur_val, list):
                        fields[cur_field] = value[field_idx][idx]
                    else:
                        raise ValueError('Found miss match between timestamp count the value count.')
            else:
                fields[field] = value[idx]
            cur_sample['fields'] = fields

            # add the current sample to the data
            self._db_data.append(cur_sample)

    def measure(self):
        """Performs a measurement and stores the obtained data in the _db_data field.

        :return:
        """

        # get the actual measurement values as dictionary
        data = self.sensor.measure()

        self.print_sensor_data(data)

        # add the name of the sensor the measurements
        fields = [f'{self.name}-{meas_name}' for meas_name in list(data.keys())]

        # get the values as list
        values = list(data.values())

        # store the data in the buffer
        self.add_data(field=fields, value=values, timestamp=datetime.now(timezone.utc))

    def print_sensor_data(self, sensor_data: dict):
        """Prints the sensor data into the command line.

        :param sensor_data: (mandatory, dict) the sensor data returned from the self.sensor.measure() method
        :return:
        """

        # prepare output
        max_field_len = max([len(x) for x in sensor_data.keys()])
        output = f'### {self.name} {"".ljust(max_field_len+9-len(self.name), "#")}'
        for key, val in sensor_data.items():
            output += f"\n{str(key).ljust(max_field_len, ' ')} : {val:.2f}"
        output += '\n'.ljust(max_field_len+15, '#') + '\n'
        print(output)

    def write_db(self):
        """Write the data stored in the _db_data field into the data base.

        :return:
        """

        # write the data and clear it when ever the writing was successful
        if self._dbclient.write_points(self._db_data):
            self._clear_data()

    def _clear_data(self):
        """Internal method to clean up the internal data buffer. Is done when ever the data was written to the db
        successfully."""

        self._db_data = list()

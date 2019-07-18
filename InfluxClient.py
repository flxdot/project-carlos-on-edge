from influxdb import InfluxDBClient

def validate_config(config: dict):
    """Checks if all required parameter are available in the passed config dictionary.

    :param config_file: (mandatory, dict) dictionary holding the config
    :return: None
    :raises: KeyError,
    """

    # Create the Client to the InfluxDB
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

    return InfluxDBClient(host=cfg_db['host'], port=port, username=cfg_db['user'], password=cfg_db['password'])

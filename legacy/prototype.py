#!/usr/bin/python

import datetime
import os
import signal
import sys
import time

import yaml
from influxdb import InfluxDBClient
from sensors.ad_converter import ADS1x15

# uv sensor
from sensors.light import SDL_Pi_SI1145

# moisture sensor
from sensors.moisture import CapacitiveSoilMoistureSensor
from sensors.temperature import DHT


# Keyboard interrupt handler
def signal_handler(signal, frame):
    print("You pressed Ctrl+C!")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# read the config
if not os.path.exists("config.yaml"):
    raise FileNotFoundError(
        "The config file "
        "config.yaml"
        " could not be located. "
        "Make sure to create one with the syntax described in the config"
    )

with open("config.yaml", "r") as document:
    config = yaml.safe_load(document)

# Create the Client to the InfluxDB
if "influxdb" not in config.keys():
    raise KeyError(
        "The loaded config did not contain the mandatory field " "influxdb" "."
    )

# check the config
cfg_db = config["influxdb"]
if "host" not in cfg_db.keys():
    raise KeyError(
        "Could not find the host of the influx db. Please validate the config file."
    )
elif "user" not in cfg_db.keys():
    raise KeyError(
        "Could not find the user of the influx db. Please validate the config file."
    )
elif "password" not in cfg_db.keys():
    raise KeyError(
        "Could not find the password of the influx db. Please validate the config file."
    )
elif "database" not in cfg_db.keys():
    raise KeyError(
        "Could not find the database of the influx db. Please validate the config file."
    )

# check for optional port
if "port" in cfg_db.keys():
    port = cfg_db["port"]
else:
    port = 8086

# create client
dbclient = InfluxDBClient(
    host=cfg_db["host"], port=port, username=cfg_db["user"], password=cfg_db["password"]
)

# select the wanted database
dbclient.switch_database(cfg_db["database"])
# Initialise the ADC using the default mode (use default I2C address)
ads = ADS1x15()
soil_sensors = dict()
soil_sensors["moisture_sensor"] = CapacitiveSoilMoistureSensor(ads, channel=1, sps=16)
soil_sensors["moisture_gartenkraeuter_large"] = CapacitiveSoilMoistureSensor(
    ads, channel=2, sps=16
)

# create UV sensor
uv_sensor = SDL_Pi_SI1145()

# create temp&humi sensor
temp_sensor = DHT("11", 4)


while True:

    print("\n\n{}".format(str(datetime.datetime.now())))
    print("--------------------")

    # temperature sensor #################################################
    humi, temp = temp_sensor.read()

    print("Temperature: {:.2f}°C".format(temp))
    print("Humidity   : {:.4f}%".format(humi))
    print("--------------------")

    # insert data into influxdb
    json_body = [
        {
            "measurement": "environment",
            "tags": {},
            "time": str(datetime.datetime.now(datetime.timezone.utc)),
            "fields": {
                "temperature": temp,
                "humidity": humi,
            },
        }
    ]
    dbclient.write_points(json_body)

    # moisture sensor ####################################################
    for name, soil_sensor in soil_sensors.items():
        volts = soil_sensor._read()
        moisture = soil_sensor._convertVoltageToMoisture(volts)

        print("Moisture: {:.2f}%".format(moisture))
        print("Voltage : {:.4f}V".format(volts))
        print("--------------------")

        # insert data into influxdb
        json_body = [
            {
                "measurement": name,
                "tags": {},
                "time": str(datetime.datetime.now(datetime.timezone.utc)),
                "fields": {
                    "voltage": volts,
                    "moisture": moisture,
                },
            }
        ]
        dbclient.write_points(json_body)

    # UV Sensor #########################################################
    vis_raw = uv_sensor.readVisible()
    vis_lux = uv_sensor.convertVisibleToLux(vis_raw)
    ir_raw = uv_sensor.readIR()
    ir_lux = uv_sensor.convertIrToLux(ir_raw)
    uv_idx = uv_sensor.readUVindex()
    print("Vis     : " + str(vis_raw))
    print("Vis Lux : " + str(vis_lux))
    print("IR      : " + str(ir_raw))
    print("IR Lux  : " + str(ir_lux))
    print("UV Index: " + str(uv_idx))
    print("--------------------")

    json_body = [
        {
            "measurement": "uv_light",
            "tags": {},
            "time": str(datetime.datetime.now(datetime.timezone.utc)),
            "fields": {
                "vis_raw": vis_raw,
                "vis_lux": vis_lux,
                "ir_raw": ir_raw,
                "ir_lux": ir_lux,
                "ur_idx": uv_idx,
            },
        }
    ]
    dbclient.write_points(json_body)

    time.sleep(5)

import time, signal, sys
import datetime

# moisture sensor
import sensors.SDL_Adafruit_ADS1x15 as SDL_Adafruit_ADS1x15
# uv sensor
import sensors.SDL_Pi_SI1145 as SDL_Pi_SI1145
import sensors.SI1145Lux as SI1145Lux
from influxdb import InfluxDBClient

dbclient = InfluxDBClient(host='mydomain.com', port=8086, username='myuser', password='mypass')
dbclient.switch_database('carlos_prototype_db')

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

ADS1115 = 0x01  # 16-bit ADC

# Select the gain
# gain = 6144  # +/- 6.144V
gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
# gain = 1024  # +/- 1.024V
# gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
# sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

# Initialise the ADC using the default mode (use default I2C address)
adc = SDL_Adafruit_ADS1x15.ADS1x15(ic=ADS1115)
sensor = SDL_Pi_SI1145.SDL_Pi_SI1145()


while (True):
    
    # Read channels  in single-ended mode using the settings above
    
    # 
    print("--------------------")
    voltsCh0 = adc.readADCSingleEnded(0, gain, sps) / 1000
    rawCh0 = adc.readRaw(0, gain, sps)
    print("Channel 0 ={:.6f}V raw=0x{:4X} dec={}".format(voltsCh0, rawCh0, rawCh0))
    voltsCh1 = adc.readADCSingleEnded(1, gain, sps) / 1000
    rawCh1 = adc.readRaw(1, gain, sps)
    print("Channel 1 ={:.6f}V raw=0x{:4X} dec={}".format(voltsCh1, rawCh1, rawCh1))
    voltsCh2 = adc.readADCSingleEnded(2, gain, sps) / 1000
    rawCh2 = adc.readRaw(2, gain, sps)
    print("Channel 2 ={:.6f}V raw=0x{:4X} dec={}".format(voltsCh2, rawCh2, rawCh2))
    voltsCh3 = adc.readADCSingleEnded(3, gain, sps) / 1000
    rawCh3 = adc.readRaw(3, gain, sps)
    print("Channel 3 ={:.6f}V raw=0x{:4X} dec={}".format(voltsCh3, rawCh3, rawCh3))
    print("--------------------")

    json_body = [
        {
            "measurement": "moisture_sensor",
            "tags": {},
            "time": str(datetime.datetime.now(datetime.timezone.utc)),
            "fields": {
                "voltage": voltsCh1,
                "value": rawCh1,
            }
        }
    ]
    dbclient.write_points(json_body)

    # UV Sensor

    vis = sensor.readVisible()
    IR = sensor.readIR()
    UV = sensor.readUV()
    IR_Lux = SI1145Lux.SI1145_IR_to_Lux(IR)
    vis_Lux = SI1145Lux.SI1145_VIS_to_Lux(vis)
    uvIndex = UV / 100.0
    print('--------------------')
    print('Vis: ' + str(vis))
    print('IR:  ' + str(IR))
    print('UV:  ' + str(UV))
    print('--------------------')
    print('Vis Lux:  ' + str(vis_Lux))
    print('IR Lux:   ' + str(IR_Lux))
    print('UV Index: ' + str(uvIndex))
    print('--------------------')

    json_body = [
        {
            "measurement": "uv_light",
            "tags": {},
            "time": str(datetime.datetime.now(datetime.timezone.utc)),
            "fields": {
                "vis_lux": vis_Lux,
                "ir_lux": IR_Lux,
                "uv_idx": uvIndex,
                "vis_raw": vis,
                "ir_raw": IR,
                "uv_raw": UV,
            }
        }
    ]
    dbclient.write_points(json_body)

    time.sleep(10)

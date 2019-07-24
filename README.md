# project-carlos-on-edge
The code running on raspberry pi on edge to read and fetch sensor data

# Requirements

1. Activate the i2c interface on your raspberry-pi
2. install python3.7
3. install required packages:
   ```bash
   python3.7 -m pip install -r requirements.txt
   ```

# Configuration

```yaml

influxdb:
  host: 127.0.01
  user: my_influx_user
  password: t0pS3cr3t
  database: carlos_prototype

environment:
  uv-light: SI1145
  temp-humi:
    type: DHT11
    gpio-pin: 5

irrigation-loops:
  - box-mix-small:
      moisture-sensor:
        i2c-address: 0x48
        channel: 1
      pump: main-pump
      valve-gpio: 21
      watering-rule:
        trigger:
          low-level: 38
          time: 30m
        time: 2s
        interval: 15m
  - box-mix-large:
      moisture-sensor:
        i2c-address: 0x48
        channel: 2
      pump: main-pump
      valve-gpio: 22
      watering-rule:
        trigger:
          low-level: 38
          time: 30m
        time: 3s
        interval: 15m

pumps:
  - main-pump:
      gpio-pin: 20
      water-tank:
        gpio-pin: 7
        low-level-warning: 25
        low-level-alarm: 15



```

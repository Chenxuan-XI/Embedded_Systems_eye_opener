import time
from smbus2 import SMBus, i2c_msg
import paho.mqtt.client as mqtt
import json
import threading
import gpiod

# MQTT def
client = mqtt.Client()
Broker = "10.215.255.119"
PORT = 1883
# client.username_pw_set("tfboys","Abc12345")
TOPIC = "cx/iotbox01/sensors"
TOPIC_heater = "cx/iotbox01/heater"

def on_message(client, userdata, msg):
    print(f"Received: {msg.payload.decode()}")

def mqtt_loop():
    client.connect(Broker, PORT, 60)
    client.subscribe(TOPIC_heater)
    client.on_message = on_message
    client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

bus = SMBus(1)

# Si7021 definitions
SI7021_ADDR = 0x40
SI7021_READ_TEMPERATURE = 0xF3
SI7021_READ_HUMIDITY = 0xF5

def read_si7021_temperature():
    write = i2c_msg.write(SI7021_ADDR, [SI7021_READ_TEMPERATURE])
    bus.i2c_rdwr(write)

    time.sleep(0.1)

    read = i2c_msg.read(SI7021_ADDR, 2)
    bus.i2c_rdwr(read)

    data = list(read)
    raw = (data[0] << 8) | data[1]

    temperature = (175.72 * raw) / 65536.0 - 46.85
    return temperature


def read_si7021_humidity():
    write = i2c_msg.write(SI7021_ADDR, [SI7021_READ_HUMIDITY])
    bus.i2c_rdwr(write)

    time.sleep(0.1)

    read = i2c_msg.read(SI7021_ADDR, 2)
    bus.i2c_rdwr(read)

    data = list(read)
    raw = (data[0] << 8) | data[1]

    humidity = (125.0 * raw) / 65536.0 - 6.0
    return humidity

def read_distance_cm():
    trig.set_value(1)
    time.sleep(0.00001)
    trig.set_value(0)

    timeout = time.time() + 0.04

    while echo.get_value() == 0:
        if time.time() > timeout:
            return None
        start = time.time()

    while echo.get_value() == 1:
        if time.time() > timeout:
            return None
        end = time.time()

    pulse = end - start
    return (pulse * 34300) / 2


CHIP = "gpiochip0"
TRIG = 23  # BCM numbering
ECHO = 24

chip = gpiod.Chip(CHIP)

trig = chip.get_line(TRIG)
echo = chip.get_line(ECHO)

trig.request(consumer="hcsr04_trig", type=gpiod.LINE_REQ_DIR_OUT)
echo.request(consumer="hcsr04_echo", type=gpiod.LINE_REQ_DIR_IN)


# Main loop
while True:
    try:
        distance_cm = read_distance_cm()
        if distance_cm is None:
            distance_cm = 1000
        distance_cm = round(distance_cm,3)
        temperature = read_si7021_temperature()
        humidity = read_si7021_humidity()

        payload = {
            "timestamp": int(time.time()),
            "window": distance_cm,
            "temperature": temperature,
            "humidity": humidity, 
        }

        # MSG_INFO = client.publish("IC.embedded/GroupJay",adc_value)
        # mqtt.error_string(MSG_INFO.rc)
        client.publish(TOPIC, json.dumps(payload))
        print("Published:", payload)
        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        break

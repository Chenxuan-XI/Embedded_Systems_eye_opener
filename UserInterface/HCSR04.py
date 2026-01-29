import paho.mqtt.client as mqtt
import threading
import gpiod
import time

BROKER_IP = "10.202.92.35"
MQTT_PORT = 1883

TOPIC_TEMPERATURE = "home/temp"
TOPIC_HUMIDITY = "home/humidity"
TOPIC_WINDOW = "home/window"
TOPIC_HEATER_SET = "home/heater/set"

client = mqtt.Client()

def mqtt_loop():
    client.connect(BROKER_IP, MQTT_PORT, 60)
    client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

def read_distance_cm():
    # Trigger pulse
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

while True:
    d = read_distance_cm()
    if d:
        print(f"{d:.2f} cm")
        client.publish(TOPIC_WINDOW, d)
    else:
        print("Out of range")
    time.sleep(2)







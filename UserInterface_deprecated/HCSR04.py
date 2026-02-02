import paho.mqtt.client as mqtt
import pigpio
import threading
import gpiod
import time

BROKER_IP = "10.215.255.119"
MQTT_PORT = 1883

TOPIC_TEMPERATURE = "home/temp"
TOPIC_HUMIDITY = "home/humidity"
TOPIC_WINDOW = "home/window"
TOPIC_HEATER_SET = "home/heater/set"

heater_on = True
moving_average = [0,0,0,0,0]


client = mqtt.Client()
def on_message(client, userdata, msg):
    print(f"Received: {msg.payload.decode()}")
    for i in range(len(moving_average)-1):
        moving_average[5-i-1] = moving_average[5-i-2]
        print(moving_average[5-i-1])
    moving_average[0] = float(msg.payload.decode())
    avg_window = sum(moving_average)/len(moving_average)
    print("Moving Average", avg_window)


def mqtt_loop():
    client.connect(BROKER_IP, MQTT_PORT, 60)
    client.subscribe(TOPIC_WINDOW)
    client.on_message = on_message
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










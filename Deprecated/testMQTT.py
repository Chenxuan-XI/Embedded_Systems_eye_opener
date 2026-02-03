import paho.mqtt.client as mqtt
import time

BROKER_IP = "10.202.92.35"   # e.g. 192.168.1.100
TOPIC = "home/pi/test"

client = mqtt.Client()
client.connect(BROKER_IP, 1883, 60)

while True:
    client.publish(TOPIC, "Hello from Raspberry Pi")
    print("Message sent")
    time.sleep(2)

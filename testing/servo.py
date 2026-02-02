import pigpio, time
import paho.mqtt.client as mqtt
import json

pi = pigpio.pi()          # connects to local pigpiod
GPIO = 18                 # servo signal wire here

pi.set_mode(GPIO, pigpio.OUTPUT)
SERVO_ON_POS = 500
SERVO_OFF_POS = 2500

# # SG90 typical range: 500–2500 us (some prefer 600–2400)
# for pw in (500, 1500, 2500, 1500):
#     pi.set_servo_pulsewidth(GPIO, pw)
#     time.sleep(1)

# pi.set_servo_pulsewidth(GPIO, 0)   # stop pulses
# pi.stop()


BROKER_IP = "10.215.255.119"
TOPIC = "cx/iotbox01/heater"

def on_message(client, userdata, msg):
    cmd = json.parse(msg.payload.decode())
    print(f"Received: {cmd}")
    if cmd.command == "ON":
        pi.set_servo_pulsewidth(GPIO, SERVO_ON_POS)
    elif cmd.command == "OFF":
        pi.set_servo_pulsewidth(GPIO, SERVO_ON_POS)
    

client = mqtt.Client()
client.connect(BROKER_IP, 1883, 60)

client.subscribe(TOPIC)
client.on_message = on_message

client.loop_forever()
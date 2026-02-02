from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import threading
import time
import json

app = Flask(__name__)

# ======================
# MQTT 配置
# ======================
MQTT_BROKER = "10.215.255.119"
MQTT_PORT = 1883
TOPIC_sensor = "cx/iotbox01/sensors"
TOPIC_heater = "cx/iotbox01/heater"

#GPIO Settings

CHIP = "gpiochip0"
TRIG = 23  # BCM numbering
ECHO = 24

# ======================
# MQTT Client
# ======================
mqtt_client = mqtt.Client()

import json

import json

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_sensor:
        print("Received Sensor Data:", payload)

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            print("Invalid JSON")
            return

        window = data.get("window")

        if window is None:
            print("No window value in payload")
            return

        if window > 300:
            client.publish(TOPIC_heater, "OFF")
            print("Heater OFF")
        else:
            client.publish(TOPIC_heater, "ON")
            print("Heater ON")

    

def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe(TOPIC_sensor)
    mqtt_client.on_message = on_message
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

# ======================
# Flask Routes
# ======================

# ⭐ 根路径：直接返回 HTML UI
@app.route("/")
def index():
    return render_template("index.html")

# （可选）给 HTML 用的 API
# @app.route("/api/heater", methods=["POST"])
# def set_heater():
#     data = request.json
#     state = data.get("state", "").upper()

#     if state not in ["ON", "OFF"]:
#         return jsonify({"error": "state must be ON or OFF"}), 400

#     mqtt_client.publish(TOPIC_heater, state)
#     return jsonify({"ok": True, "state": state})

# ======================
# 启动
# ======================


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # 允许局域网 / 服务器访问
        port=8000,
        debug=True,
        use_reloader=False
    )

from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import threading
import time

app = Flask(__name__)

# ======================
# MQTT 配置
# ======================
MQTT_BROKER = "10.202.92.35"
MQTT_PORT = 1883

TOPIC_TEMPERATURE = "home/temp"
TOPIC_HUMIDITY = "home/humidity"
TOPIC_WINDOW = "home/window"
TOPIC_HEATER_SET = "home/heater/set"

# ======================
# MQTT Client
# ======================
mqtt_client = mqtt.Client()

def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
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
@app.route("/api/heater", methods=["POST"])
def set_heater():
    data = request.json
    state = data.get("state", "").upper()

    if state not in ["ON", "OFF"]:
        return jsonify({"error": "state must be ON or OFF"}), 400

    mqtt_client.publish(TOPIC_HEATER_SET, state)
    return jsonify({"ok": True, "state": state})

# ======================
# 启动
# ======================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # 允许局域网 / 服务器访问
        port=5000,
        debug=True
    )

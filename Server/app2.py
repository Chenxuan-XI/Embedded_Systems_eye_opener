from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import threading
import time

app = Flask(__name__)

# ======================
# MQTT 配置
# ======================
MQTT_BROKER = "10.215.255.119"
MQTT_PORT = 1883

TOPIC_TEMPERATURE = "home/temp"
TOPIC_HUMIDITY = "home/humidity"
TOPIC_WINDOW = "home/window"          # 这里你用来发 distance 或 OPEN/CLOSED 都可以
TOPIC_HEATER_SET = "home/heater/set"

# ======================
# 全局最新数据缓存
# ======================
latest = {
    "temp": None,
    "hum": None,
    "distance": None,     # 如果 home/window 发的是距离(cm)，就填这里
    "window": None,       # OPEN/CLOSED 或 inferred
    "updated_at": None
}
latest_lock = threading.Lock()

# 如果你的 home/window 发的是距离（cm），用这个阈值推断 OPEN/CLOSED
WINDOW_OPEN_THRESHOLD_CM = 20.0

# ======================
# MQTT Client
# ======================
mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode(errors="ignore").strip()

    now = time.time()

    with latest_lock:
        latest["updated_at"] = now

        if topic == TOPIC_TEMPERATURE:
            # 尝试解析成数字
            try:
                latest["temp"] = float(payload)
            except ValueError:
                latest["temp"] = payload

        elif topic == TOPIC_HUMIDITY:
            try:
                latest["hum"] = float(payload)
            except ValueError:
                latest["hum"] = payload

        elif topic == TOPIC_WINDOW:
            # 可能是：distance 数字 OR "OPEN"/"CLOSED"
            up = payload.upper()

            # 1) 如果是 OPEN/CLOSED 直接用
            if up in ["OPEN", "CLOSED"]:
                latest["window"] = up
                latest["distance"] = None

            else:
                # 2) 否则尝试当作 distance
                try:
                    d = float(payload)
                    latest["distance"] = d
                    latest["window"] = "OPEN" if d > WINDOW_OPEN_THRESHOLD_CM else "CLOSED"
                except ValueError:
                    # 3) 既不是数字也不是 OPEN/CLOSED，就原样放到 window
                    latest["window"] = payload

    print(f"Received topic={topic} payload={payload}")

def mqtt_loop():
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # ✅ 订阅所有你要显示的 topic
    mqtt_client.subscribe([
        (TOPIC_TEMPERATURE, 0),
        (TOPIC_HUMIDITY, 0),
        (TOPIC_WINDOW, 0),
    ])

    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

# ======================
# Flask Routes
# ======================

@app.route("/")
def index():
    return render_template("index.html")

# 给前端轮询用：拉最新状态
@app.route("/api/state", methods=["GET"])
def get_state():
    with latest_lock:
        return jsonify(latest)

# 你原来的 heater 控制 API 保留
@app.route("/api/heater", methods=["POST"])
def set_heater():
    data = request.json or {}
    state = str(data.get("state", "")).upper()

    if state not in ["ON", "OFF"]:
        return jsonify({"error": "state must be ON or OFF"}), 400

    mqtt_client.publish(TOPIC_HEATER_SET, state)
    return jsonify({"ok": True, "state": state})

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
        use_reloader=False
    )

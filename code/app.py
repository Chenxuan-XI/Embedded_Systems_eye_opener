import json
import time
import threading

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template_string

# ======================
# MQTT CONFIG
# ======================
MQTT_BROKER = "10.202.92.141"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"

# ======================
# GLOBAL STATE
# ======================
latest_data = {
    "temperature": None,
    "humidity": None,
    "distance": None,
    "window_open": None,
    "comfort_score": None,
    "recommendation": "Waiting for data...",
    "reasons": []
}

# ======================
# SENSOR FUSION LOGIC
# ======================
def fuse_and_decide(temp, hum, dist):
    reasons = []

    # --- window detection ---
    window_open = dist is not None and dist > 100

    # --- comfort score ---
    score = 100
    score -= abs(temp - 21) * 5
    if hum > 60:
        score -= (hum - 60) * 1.5
    if window_open:
        score -= 10

    score = max(0, int(score))

    # --- decision logic ---
    if temp < 19:
        reasons.append("Temperature is below comfort range")
        if window_open:
            recommendation = "Close window before turning ON heating"
            reasons.append("Window is currently open")
        else:
            recommendation = "Turn ON heating"
    elif temp > 22:
        recommendation = "Turn OFF heating"
        reasons.append("Temperature is above comfort range")
    else:
        recommendation = "Heating OFF"
        reasons.append("Temperature is within comfort range")

    if hum > 65:
        reasons.append("High humidity detected")

    return window_open, score, recommendation, reasons


# ======================
# MQTT CALLBACKS
# ======================
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    global latest_data
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temperature")
        hum = payload.get("humidity")
        dist = payload.get("distance")

        window_open, score, rec, reasons = fuse_and_decide(temp, hum, dist)

        latest_data.update({
            "temperature": temp,
            "humidity": hum,
            "distance": dist,
            "window_open": window_open,
            "comfort_score": score,
            "recommendation": rec,
            "reasons": reasons
        })

    except Exception as e:
        print("Error processing MQTT message:", e)


def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()


# ======================
# FLASK WEB UI
# ======================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Heating Assistant</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; }
        .card { background: white; padding: 20px; width: 400px;
                margin: 50px auto; border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; }
        .big { font-size: 24px; font-weight: bold; }
        .rec { margin-top: 20px; padding: 10px; background: #eef; }
    </style>
</head>
<body>
<div class="card">
    <h1>Smart Heating Assistant</h1>
    <p>Temperature: <b>{{ d.temperature }} °C</b></p>
    <p>Humidity: <b>{{ d.humidity }} %</b></p>
    <p>Window: <b>{{ "OPEN" if d.window_open else "CLOSED" }}</b></p>

    <p class="big">Comfort Score: {{ d.comfort_score }} / 100</p>

    <div class="rec">
        <b>Recommendation:</b><br>
        {{ d.recommendation }}
        <ul>
        {% for r in d.reasons %}
            <li>{{ r }}</li>
        {% endfor %}
        </ul>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, d=latest_data)


@app.route("/api/data")
def api_data():
    return jsonify(latest_data)


# ======================
# MAIN
# ======================
if __name__ == "__main__":
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=False)

from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import threading
import time
import json
import os
import sys
import sqlite3
import numpy as np

CODE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code"))
if CODE_DIR not in sys.path:
    sys.path.append(CODE_DIR)


app = Flask(__name__)

# ======================
# MQTT Config
# ======================
MQTT_BROKER = "10.215.255.119"
MQTT_PORT = 1883
TOPIC_SENSOR = "cx/iotbox01/sensors"
TOPIC_HEATER = "cx/iotbox01/heater"

# ======================
# Control thresholds / tuning
# ======================
WINDOW_OPEN_THRESHOLD = 500.0
MOVING_AVG_LEN = 5

# "bad for my health" thresholds (adjust to your needs)
TEMP_BAD_LOW = 16.0
TEMP_BAD_HIGH = 28.0
HUM_BAD_LOW = 30.0
HUM_BAD_HIGH = 70.0

DEFAULT_THRESHOLDS = {
    "T_cold": 18.0,
    "H_dry": 30.0,
    "W_open": 600.0
}

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sensor.db"))

# ----------------------
# Local decision-engine helpers (mirror code/decision_engine.py)
# ----------------------
def load_recent(minutes=30, db_file=None):
    db_file = db_file or DB_FILE
    since = int(time.time()) - minutes * 60
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "SELECT temperature, humidity, window FROM sensor_log WHERE time >= ?",
        (since,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def compute_thresholds(rows):
    if len(rows) < 20:
        return dict(DEFAULT_THRESHOLDS)

    temps = np.array([r[0] for r in rows], dtype=float)
    hums  = np.array([r[1] for r in rows], dtype=float)
    wins  = np.array([r[2] for r in rows], dtype=float)

    return {
        "T_cold": round(temps.mean() - 1.0, 2),
        "H_dry": round(float(np.percentile(hums, 20)), 2),
        "W_open": 600
    }


def heater_decision_local(temp, hum, win, thresholds=None):
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        th.update(thresholds)

    if win is None:
        return "OFF", "No window data"

    if win >= th["W_open"]:
        return "OFF", "Window open – heating disabled"

    if temp is None or hum is None:
        return "OFF", "Missing temperature/humidity data"

    if temp < th["T_cold"] and hum >= th["H_dry"]:
        return "ON", "Temperature below adaptive threshold"

    if temp < th["T_cold"] and hum < th["H_dry"]:
        return "OFF", "Air too dry – heating not recommended"

    return "OFF", "Temperature comfortable"

# Health alert cooldown so you don't get spammed
HEALTH_ALERT_COOLDOWN_SEC = 15 * 60

# ======================
# Server state (thread-safe)
# ======================
state_lock = threading.Lock()

settings = {
    # tri-state: "Automatic" | "Alert" | "Off"
    "off_when_window_open": "Automatic",
    "on_when_window_shut": "Automatic",
    # two-state: "ON" | "OFF"
    "open_window_health_alert": "OFF",
}

moving_average = [0.0] * MOVING_AVG_LEN

last_published_heater = None  # "ON"/"OFF"
last_health_alert_ts = 0.0

# ======================
# MQTT Client
# ======================
mqtt_client = mqtt.Client()


def _normalize_cmd(cmd) -> str | None:
    if cmd is None:
        return None
    c = str(cmd).strip().upper()
    return c if c in ("ON", "OFF") else None


def heater_decision(temp, hum, win, thresholds=None):
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        th.update(thresholds)

    if win is None:
        return "OFF", "No window data"

    if win >= th["W_open"]:
        return "OFF", "Window open – heating disabled"

    if temp is None or hum is None:
        return "OFF", "Missing temperature/humidity data"

    if temp < th["T_cold"] and hum >= th["H_dry"]:
        return "ON", "Temperature below adaptive threshold"

    if temp < th["T_cold"] and hum < th["H_dry"]:
        return "OFF", "Air too dry – heating not recommended"

    return "OFF", "Temperature comfortable"

def publish_heater(cmd: str, reason: str = ""):
    """
    Publish heater command to MQTT (JSON payload).
    cmd: "ON" or "OFF"
    """
    global last_published_heater

    cmd = _normalize_cmd(cmd)
    if cmd is None:
        return

    # Avoid spamming the same value repeatedly
    with state_lock:
        if last_published_heater == cmd:
            return
        last_published_heater = cmd

    payload = json.dumps({"command": cmd, "source": "server", "reason": reason})
    mqtt_client.publish(TOPIC_HEATER, payload)
    print(f"[MQTT] publish {TOPIC_HEATER} {payload}")


def send_phone_notification(title: str, message: str):
    """
    Hook for phone notifications.
    Implement using a service you prefer: Pushover / Pushbullet / Telegram / ntfy / etc.

    This function is intentionally a stub so your app runs even without credentials.
    """
    print(f"[ALERT] {title}: {message}")


def maybe_send_health_alert(temp: float | None, hum: float | None, window_is_open: bool):
    global last_health_alert_ts

    with state_lock:
        enabled = (settings["open_window_health_alert"] == "ON")

    if not enabled:
        return

    now = time.time()
    if now - last_health_alert_ts < HEALTH_ALERT_COOLDOWN_SEC:
        return

    # Only alert if conditions are "bad" AND window is NOT open (so "open window" makes sense)
    temp_bad = (temp is not None) and (temp < TEMP_BAD_LOW or temp > TEMP_BAD_HIGH)
    hum_bad = (hum is not None) and (hum < HUM_BAD_LOW or hum > HUM_BAD_HIGH)

    if (temp_bad or hum_bad) and (not window_is_open):
        last_health_alert_ts = now

        parts = []
        if temp is not None:
            parts.append(f"Temp={temp:.1f}°C")
        if hum is not None:
            parts.append(f"Humidity={hum:.1f}%")

        msg = " / ".join(parts) if parts else "Unhealthy conditions detected"
        send_phone_notification(
            "Health alert: open window",
            f"{msg}. Consider opening a window to improve comfort/air."
        )


def _parse_json_or_text(payload: str) -> dict | None:
    payload = (payload or "").strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def on_message(client, userdata, msg):
    topic = msg.topic
    raw = msg.payload.decode(errors="ignore").strip()

    # --- Heater topic: accept raw "ON"/"OFF" or JSON {"command":"ON", ...}
    if topic == TOPIC_HEATER:
        cmd = _normalize_cmd(raw)
        source = None

        if cmd is None:
            obj = _parse_json_or_text(raw)
            if isinstance(obj, dict):
                cmd = _normalize_cmd(obj.get("command"))
                source = obj.get("source")

        if cmd is None:
            print("[MQTT] heater payload not understood:", raw)
            return


        # Track latest state to reduce server spam later
        global last_published_heater
        with state_lock:
            last_published_heater = cmd

        print(f"[MQTT] heater state observed: {cmd} (source={source})")
        return

    # --- Sensor topic: JSON expected
    if topic != TOPIC_SENSOR:
        return

    print("Received Sensor Data:", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Invalid JSON")
        return

    window = data.get("window")
    temperature = data.get("temperature")
    humidity = data.get("humidity")

    def to_float(x):
        try:
            return float(x) if x is not None else None
        except (TypeError, ValueError):
            return None

    window_val = to_float(window)
    temp_val = to_float(temperature)
    hum_val = to_float(humidity)

    if window_val is None:
        print("No valid window value in payload")
        return

    # update moving average
    global moving_average
    moving_average = [window_val] + moving_average[:-1]
    avg_window = sum(moving_average) / len(moving_average)

    window_is_open = avg_window > WINDOW_OPEN_THRESHOLD
    print("Moving Average window:", avg_window, "window_is_open:", window_is_open)

    # health alert hook
    maybe_send_health_alert(temp_val, hum_val, window_is_open)

    # Read settings (no manual override timer anymore)
    with state_lock:
        off_when_open = settings["off_when_window_open"]
        on_when_shut = settings["on_when_window_shut"]

    # Adaptive thresholds from last 30 minutes (DB-backed)
    try:
        rows = load_recent(minutes=30)
        th = compute_thresholds(rows)
    except Exception as e:
        print("Threshold compute failed:", e)
        th = dict(DEFAULT_THRESHOLDS)
    th["W_open"] = WINDOW_OPEN_THRESHOLD

    # Auto logic based on settings
    if window_is_open:
        if off_when_open == "Automatic":
            cmd, reason = heater_decision_local(
                temp_val,
                hum_val,
                avg_window,
                thresholds=th,
            )
            publish_heater(cmd, reason=reason)
        elif off_when_open == "Alert":
            send_phone_notification(
                "Window open",
                "Window appears open. Heater NOT auto-turned off (Alert mode)."
            )
        # Off => do nothing
    else:
        if on_when_shut == "Automatic":
            cmd, reason = heater_decision_local(
                temp_val,
                hum_val,
                avg_window,
                thresholds=th,
            )
            publish_heater(cmd, reason=reason)
        elif on_when_shut == "Alert":
            send_phone_notification(
                "Window shut",
                "Window appears shut. Heater NOT auto-turned on (Alert mode)."
            )
        # Off => do nothing
    print(off_when_open,on_when_shut)


def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe([(TOPIC_SENSOR, 0), (TOPIC_HEATER, 0)])
    mqtt_client.on_message = on_message
    mqtt_client.loop_forever()


threading.Thread(target=mqtt_loop, daemon=True).start()

# ======================
# Flask Routes
# ======================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/heater", methods=["POST"])
def api_heater():
    """
    Receives heater command from UI (HTTP), publishes MQTT from server.
    JSON: { "command": "ON" | "OFF" }

    NEW: flips settings instead of using a timed manual override.
      - ON  => off_when_window_open becomes Off
      - OFF => on_when_window_shut becomes Off
    """
    data = request.get_json(silent=True) or {}
    cmd = _normalize_cmd(data.get("command"))

    if cmd is None:
        return jsonify({"error": "command must be ON or OFF"}), 400

    publish_heater(cmd, reason="manual http")

    with state_lock:
        current_settings = dict(settings)

    return jsonify({"ok": True, "state": cmd, "settings": current_settings})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """
    GET returns current settings
    POST accepts partial updates:
      - off_when_window_open: "Automatic" | "Alert" | "Off"
      - on_when_window_shut:  "Automatic" | "Alert" | "Off"
      - open_window_health_alert: "ON" | "OFF"
    """
    if request.method == "GET":
        with state_lock:
            return jsonify(settings)

    data = request.get_json(silent=True) or {}

    def valid_tri(v): return v in ("Automatic", "Alert", "Off")
    def valid_onoff(v): return v in ("ON", "OFF")

    patch = {}

    if "off_when_window_open" in data:
        v = str(data["off_when_window_open"])
        if not valid_tri(v):
            return jsonify({"error": "off_when_window_open must be Automatic, Alert, or Off"}), 400
        patch["off_when_window_open"] = v

    if "on_when_window_shut" in data:
        v = str(data["on_when_window_shut"])
        if not valid_tri(v):
            return jsonify({"error": "on_when_window_shut must be Automatic, Alert, or Off"}), 400
        patch["on_when_window_shut"] = v

    if "open_window_health_alert" in data:
        v = str(data["open_window_health_alert"]).upper()
        if not valid_onoff(v):
            return jsonify({"error": "open_window_health_alert must be ON or OFF"}), 400
        patch["open_window_health_alert"] = v

    with state_lock:
        settings.update(patch)
        updated = dict(settings)

    return jsonify({"ok": True, "settings": updated})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
        use_reloader=False
    )

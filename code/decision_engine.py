import json
import time
import sqlite3
import numpy as np
import paho.mqtt.client as mqtt

BROKER = "10.215.255.119"
PORT = 1883

TOPIC_IN  = "cx/iotbox01/sensors"
TOPIC_OUT = "cx/iotbox01/recommendation"
DB_FILE   = "sensor.db"

DEFAULT_THRESHOLDS = {
    "T_cold": 18.0,
    "H_dry": 30.0,
    "W_open": 600.0
}

# Read from DB
def load_recent(minutes=30):
    since = int(time.time()) - minutes * 60
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT temperature, humidity, window FROM sensor_log WHERE time >= ?",
        (since,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# Threshold Calculation
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

# Decision Logic (compat shim)
def decide(temp, hum, win, th):
    return heater_decision(temp, hum, win, th)

# MQTT callback
def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(TOPIC_IN)
    print("Subscribed to", TOPIC_IN)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        temp = float(data["temperature"])
        hum  = float(data["humidity"])
        win  = float(data["window"])

        rows = load_recent(minutes=30)
        th = compute_thresholds(rows)

        heater, reason = decide(temp, hum, win, th)

        out = {
            "timestamp": int(time.time()),
            "heater": heater,
            "reason": reason,
            "thresholds": th
        }

        client.publish(TOPIC_OUT, json.dumps(out))
        print("Decision:", out)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

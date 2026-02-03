import json
import time
import sqlite3
import paho.mqtt.client as mqtt

BROKER = "10.215.255.119"
PORT = 1883

TOPIC_IN = "cx/iotbox01/sensors"
DB_FILE = "sensor.db"

# establish SQL data base
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensor_log (
        time INTEGER,
        temperature REAL,
        humidity REAL,
        window REAL
    )
    """)
    conn.commit()
    conn.close()

# Data Record
def insert_row(t, temp, hum, win):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sensor_log (time, temperature, humidity, window) VALUES (?, ?, ?, ?)",
        (t, temp, hum, win)
    )
    conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC_IN)
    print("Subscribed to", TOPIC_IN)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        t = int(data.get("timestamp", time.time()))
        temp = float(data["temperature"])
        hum = float(data["humidity"])
        win = float(data["window"])

        insert_row(t, temp, hum, win)
        print("Logged:", t, temp, hum, win)

    except Exception as e:
        print("Error parsing/logging:", e)

if __name__ == "__main__":
    init_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

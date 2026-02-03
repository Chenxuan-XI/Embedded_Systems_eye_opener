import sqlite3
import time
import numpy as np

DB_FILE = "sensor.db"

def load_recent(minutes=30):
    since = int(time.time()) - minutes*60
    conn = sqlite3.connect(DB_FILE)
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
        # If small database, use default values
        return {
            "T_cold": 18.0,
            "H_dry": 30.0,
            "W_open": 300.0
        }

    temps = np.array([r[0] for r in rows], dtype=float)
    hums  = np.array([r[1] for r in rows], dtype=float)
    wins  = np.array([r[2] for r in rows], dtype=float)

    mean_temp = temps.mean()
    T_cold = mean_temp - 1.0

    H_dry = float(np.percentile(hums, 20))
    W_open = float(np.percentile(wins, 70)) 

    return {
        "T_cold": round(T_cold, 2),
        "H_dry": round(H_dry, 2),
        "W_open": round(W_open, 2)
    }

if __name__ == "__main__":
    rows = load_recent(minutes=30)
    th = compute_thresholds(rows)
    print("Adaptive thresholds:", th)

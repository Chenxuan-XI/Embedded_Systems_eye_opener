import sqlite3

# check the latest 10 data stored in sensor.db

conn = sqlite3.connect("sensor.db")
cur = conn.cursor()

cur.execute("SELECT time, temperature, humidity, window FROM sensor_log ORDER BY time DESC LIMIT 10")
rows = cur.fetchall()

print("10 Latest Data: ")

for r in rows:
    print(r)

conn.close()

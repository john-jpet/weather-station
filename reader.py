import serial
import sqlite3
import json
from datetime import datetime

PORT = "COM6"
BAUD = 9600

conn = sqlite3.connect("weather.db")

# Create table with all columns, or migrate if it already exists
conn.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT,
        temperature REAL,
        humidity    REAL,
        dew_point   REAL,
        heat_index  REAL
    )
""")

# Migrate old DBs that are missing the new columns
for col in ("dew_point", "heat_index"):
    try:
        conn.execute(f"ALTER TABLE readings ADD COLUMN {col} REAL")
    except Exception:
        pass  # Column already exists

conn.commit()

ser = serial.Serial(PORT, BAUD, timeout=2)
print("Reading from serial...")

while True:
    line = ser.readline().decode("utf-8").strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("error"):
            print("Sensor error — skipping")
            continue
        t   = d["t"]
        h   = d["h"]
        dp  = d["dp"]
        hi  = d["hi"]
        ts  = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO readings VALUES (NULL, ?, ?, ?, ?, ?)",
            (ts, t, h, dp, hi)
        )
        conn.commit()
        print(f"{ts}  T:{t}°C  H:{h}%  DP:{dp}°C  HI:{hi}°C")
    except Exception as e:
        print(f"Parse error: {e}  raw: {line!r}")
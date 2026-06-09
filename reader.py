import serial
import sqlite3
import json
import math
from datetime import datetime
import sys

PORT = "COM6"
BAUD = 9600

# Initialize Database Engine
conn = sqlite3.connect("weather.db")

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

# Backwards compatibility check for legacy schemas
for col in ("dew_point", "heat_index"):
    try:
        conn.execute(f"ALTER TABLE readings ADD COLUMN {col} REAL")
    except Exception:
        pass

conn.commit()

# --- Advanced Meteorological Math Engines ---
def calculate_dew_point(t, rh):
    """Calculates Dew Point (°C) using the high-accuracy Magnus-Tetens formula."""
    if rh <= 0: 
        return t
    a, b = 17.625, 243.04
    alpha = ((a * t) / (b + t)) + math.log(rh / 100.0)
    return round((b * alpha) / (a - alpha), 1)

def calculate_heat_index(t, rh):
    """Calculates Heat Index (°C) using the complete NOAA multi-regression polynomial."""
    # The standard formula is optimized for Fahrenheit, so we temporarily convert
    tf = (t * 9.0 / 5.0) + 32.0
    
    # Simple steady-state check for milder climates where heat index doesn't apply
    if tf < 80.0:
        hi_f = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (rh * 0.094))
    else:
        # Full NOAA polynomial regression
        c1, c2, c3 = -42.379, 2.04901523, 10.14333127
        c4, c5, c6 = -0.22475541, -0.00683783, -0.05481717
        c7, c8, c9 = 0.00122874, 0.00085282, -0.00000199
        
        hi_f = (c1 + (c2 * tf) + (c3 * rh) + (c4 * tf * rh) + 
                (c5 * tf**2) + (c6 * rh**2) + (c7 * tf**2 * rh) + 
                (c8 * tf * rh**2) + (c9 * tf**2 * rh**2))
        
        # High-humidity adjustments
        if (rh < 13.0) and (80.0 <= tf <= 112.0):
            adjustment = ((13.0 - rh) / 4.0) * math.sqrt((17.0 - abs(tf - 95.0)) / 17.0)
            hi_f -= adjustment
        elif (rh > 85.0) and (80.0 <= tf <= 87.0):
            adjustment = ((rh - 85.0) / 10.0) * ((87.0 - tf) / 5.0)
            hi_f += adjustment

    # Convert back to Celsius for data uniformity
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(hi_c, 1)

# Connect to target COM Port
try:
    ser = serial.Serial(PORT, BAUD, timeout=3)
    print(f"Successfully connected to {PORT}. Awaiting STM32 packets...")
except Exception as e:
    print(f"Could not open port {PORT}: {e}")
    sys.exit(1)

# Primary Logging Loop
while True:
    try:
        raw_bytes = ser.readline()
        if not raw_bytes:
            print("Serial timeout: No data received from STM32 for 3 seconds...")
            continue
            
        # Decode and scrub framing anomalies
        line = raw_bytes.decode("utf-8", errors="ignore").strip()
        if not line:
            continue

        # Intercept legacy error flags safely
        if "[ERR:" in line:
            print(f"Hardware Alert -> STM32 reported: {line}")
            continue

        # Process active telemetry packets
        d = json.loads(line)
        if d.get("error"):
            print("Sensor reported an error flag — skipping database save.")
            continue
            
        # Parse the raw, fractional inputs arriving from the STM32
        t = float(d["t"])
        h = float(d["h"])
        ts = datetime.now().isoformat()
        
        # Calculate real-time metrics using Python's FPU
        dp = calculate_dew_point(t, h)
        hi = calculate_heat_index(t, h)
        
        # Write clean parameters to the database
        conn.execute(
            """
            INSERT INTO readings (timestamp, temperature, humidity, dew_point, heat_index) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (ts, t, h, dp, hi)
        )
        conn.commit()
        
        print(f"{ts} -> Temp: {t}°C | Hum: {h}% | DewPoint: {dp}°C | HeatIndex: {hi}°C")
        
    except json.JSONDecodeError:
        print(f"Non-JSON string caught: {line!r}")
    except Exception as e:
        print(f"Unexpected script processing error: {e}")
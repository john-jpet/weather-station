# Cyber-Weather Station

A full-stack IoT weather monitoring system that captures ambient data from an Arduino-connected DHT11 sensor, logs it to an SQLite database via a Python bridge, and visualizes it through a high-performance Flask dashboard.

## Key Features

* **Real-time Sensing:** Captures Temperature and Humidity using a DHT11 sensor.
* **Calculated Metrics:** On-device calculation of Dew Point and Heat Index (perceived temperature).
* **Data Persistence:** A Python bridge script listens to the Serial port and saves data to a local SQLite database.
* **Dynamic Dashboard:** A Flask-based web interface featuring animated digit displays, interactive charts with Chart.js, and historical time-window filtering.

## Tech Stack

* **Hardware:** Arduino, DHT11 Sensor (Breakout Board).
* **Backend:** Python 3, Flask, SQLite3.
* **Frontend:** JavaScript (ES6+), Chart.js, HTML5/CSS3.
* **Communication:** JSON over Serial (USB).

## System Architecture

1. **Arduino Firmware:** Reads sensors every 2 seconds and outputs a JSON string to Serial.
2. **Serial Bridge (reader.py):** Parses Serial JSON, handles schema migrations, and inserts records into `weather.db`.
3. **Web Server (app.py):** Serves a REST API and the frontend dashboard.

## Installation and Setup

### 1. Hardware Setup
Connect your 3-pin DHT11 breakout board directly to the Arduino:
* **GND (-)** to **GND**
* **VCC (+)** to **5V** (or 3.3V depending on board)
* **DATA (S)** to **Digital Pin 2**

### 2. Arduino Libraries
Open the Arduino Library Manager (**Ctrl+Shift+I**) and install:
* **DHT sensor library** by Adafruit
* **Adafruit Unified Sensor**

### 3. Python Environment
Install the necessary dependencies:

`pip install pyserial flask`

### 4. Configuration
In `reader.py`, ensure the `PORT` variable matches your Arduino's address (e.g., `"COM6"` for Windows or `"/dev/ttyUSB0"` for Linux).

## Execution

1. **Connect the Arduino** via USB.
2. **Start the Data Logger:**

`python reader.py`

3. **Start the Web Dashboard:**

`python app.py`

4. **View the Data:**
Open `http://127.0.0.1:5000` in your web browser.

## API Reference

The Flask server provides an endpoint for data retrieval:
* **Endpoint:** `/data?window=<time>`
* **Parameters:** `10m`, `30m`, `1h`, `6h`, `24h`, `7d`.
* **Returns:** A JSON array of readings including temperature, humidity, dew point, and heat index.

## Repository Notes
The local database `weather.db` and Python virtual environments should not be committed to version control. Refer to the `.gitignore` file for exclusion rules.
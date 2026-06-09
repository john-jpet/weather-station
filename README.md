# Cyber-Weather Station

A full-stack IoT weather monitoring system that captures ambient data from a DHT11 sensor, logs it to an SQLite database via a Python bridge, and visualizes it through a high-performance Flask dashboard.

Two firmware implementations are provided — one for **Arduino (Elegoo Uno)** using the Adafruit DHT library, and one for **STM32 (Nucleo-F446RE)** written entirely in bare-metal C with no HAL or external libraries.

## Key Features

* **Real-time Sensing:** Captures Temperature and Humidity using a DHT11 sensor.
* **Calculated Metrics:** Dew Point and Heat Index computed on the Arduino implementation; transmitted as placeholder values on STM32 (recalculated client-side).
* **Data Persistence:** A Python bridge script listens to the Serial port and saves data to a local SQLite database.
* **Dynamic Dashboard:** A Flask-based web interface featuring animated digit displays, interactive charts with Chart.js, historical time-window filtering, and gap detection for periods where the sensor was offline.

## Tech Stack

* **Hardware:** Arduino Uno (Elegoo) or STM32 Nucleo-F446RE, DHT11 Sensor (Breakout Board).
* **Firmware (Arduino):** Arduino C++, Adafruit DHT library.
* **Firmware (STM32):** Bare-metal C — direct register writes, no HAL, no CMSIS, no external libraries.
* **Backend:** Python 3, Flask, SQLite3.
* **Frontend:** JavaScript (ES6+), Chart.js, HTML5/CSS3.
* **Communication:** JSON over Serial (USB).

## System Architecture

1. **Firmware:** Reads the DHT11 every 2 seconds and outputs a JSON string over serial.
2. **Serial Bridge (reader.py):** Parses the JSON, handles schema migrations, and inserts records into `weather.db`.
3. **Web Server (app.py):** Serves a REST API and the frontend dashboard.

## Installation and Setup

### 1. Hardware Setup

#### Arduino (Elegoo Uno)
Connect your 3-pin DHT11 breakout board directly to the Arduino:
* **GND (-)** to **GND**
* **VCC (+)** to **5V** (or 3.3V depending on board)
* **DATA (S)** to **Digital Pin 2**

#### STM32 (Nucleo-F446RE)
Connect your 3-pin DHT11 breakout board to the Nucleo:
* **GND (-)** to **GND**
* **VCC (+)** to **3.3V**
* **DATA (S)** to **PA1**

Serial output (UART2 TX) is routed through the onboard ST-Link to the USB virtual COM port automatically — no additional wiring needed.

### 2. Firmware Setup

#### Arduino
Open the Arduino Library Manager (**Ctrl+Shift+I**) and install:
* **DHT sensor library** by Adafruit
* **Adafruit Unified Sensor**

Flash `tempreader/tempreader.ino` to the Arduino.

#### STM32
Open `temperature_monitor/` in STM32CubeIDE. Build and flash using **Run → Run As → STM32 C/C++ Application**. Press the reset button after flashing.

No external libraries are required. The firmware configures all peripherals (TIM1, GPIOA, USART2) directly via memory-mapped registers.

### 3. Python Environment
Install the necessary dependencies:

`pip install pyserial flask`

### 4. Configuration
In `reader.py`, ensure the `PORT` variable matches your device's COM port (e.g., `"COM6"` for Windows or `"/dev/ttyUSB0"` for Linux). The same `reader.py` and `app.py` work with both firmware implementations — the JSON output format is identical.

## Execution

1. **Connect the device** via USB.
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
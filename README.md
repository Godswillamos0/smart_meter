=============== Smart Energy Meter (PZEM-004T v3.0) =====================

An ESP32-based smart energy monitoring system** that measures voltage, current, power, and energy consumption using the PZEM-004T v3.0 module, displays readings on an I2C LCD, and sends real-time data to a 
FastAPI backend server over Wi-Fi.

This project is suitable for smart metering, power monitoring, IoT energy analytics, and remote energy logging applications.

==================== Features =================

 Real-time measurement of:

  * Voltage (V)
  * Current (A)
  * Power (W)
  * Energy (kWh)
  *  16×2 I2C LCD with auto-scrolling display pages
  *  Wi-Fi connectivity using ESP32
  *  Periodic data upload to a FastAPI backend (JSON payload)

=====================- Hardware Requirements ===========================

| Component       | Description              |
| --------------- | ------------------------ |
| ESP32 Dev Board | Main microcontroller     |
| PZEM-004T v3.0  | Energy monitoring module |
| 16×2 I2C LCD    | Display unit             |
| Wi-Fi Router    | Local network access     |
| AC Load         | For energy measurement   |
| Jumper Wires    | Connections              |

=================  Pin Configuration =======================

 ESP32 ↔ PZEM-004T

| ESP32 Pin | PZEM Pin |
| --------- | -------- |
| GPIO 16   | RX       |
| GPIO 17   | TX       |

 ESP32 ↔ LCD (I2C)

| ESP32 Pin | LCD |
| --------- | --- |
| GPIO 21   | SDA |
| GPIO 22   | SCL |

 Wi-Fi Status Indicator

| ESP32 Pin | Function            |
| --------- | ------------------- |
| GPIO 23   | Wi-Fi status output |

---

## 📡 Network Configuration

Update the Wi-Fi credentials in the code:

```cpp
const char* ssid = "ssid";
const char* password = "password";
```

---
Server Configuration: The ESP32 sends data to a FastAPI endpoint in JSON format.

### Base URL

```cpp
const char* serverBase = "https://***********************";
const char* device_id  = "001";
```


============ JSON Payload Structure ===================

```json
{
  "voltage": 230.12,
  "current": 1.245,
  "power": 286.38,
  "energy": 0.534
}
```

=================== LCD Display Pages ===================

The LCD cycles automatically every second through:

1. Voltage (V)
2. Current (A)
3. Power (W)
4. Energy (kWh)

================ Data Transmission Interval ============

* Data is sent to the server every **5 seconds**
* Controlled by:

```cpp
const unsigned long sendInterval = 5000;
```

---

============== Software & Libraries Used ======================

Install the following libraries via Arduino Library Manager:

* `WiFi.h`
* `HTTPClient.h`
* `ArduinoJson`
* `PZEM004Tv30`
* `LiquidCrystal_I2C`
* `Wire.h`

---

=================== Debugging & Monitoring =====================

* Open Serial Monitor at 115200 baud
* Logs include:

  * Wi-Fi connection status
  * JSON payload being sent
  * HTTP response code
  * Server response body

---

============== Error Handling ==========

* NaN readings from PZEM are replaced with `0.00`
* Wi-Fi connection is checked before sending data
* HTTP response is logged for debugging

---


================= Author ==============

=Jaiyeola Emmanuel
Godswill Amos

 
 =================== License ============================

This project is released under the MIT License.
Feel free to use, modify, and distribute.

---

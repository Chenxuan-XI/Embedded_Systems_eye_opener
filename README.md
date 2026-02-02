# Embedded_Systems_Eye_Opener
An embedded IoT system that detects window open/closed states using an ultrasonic proximity sensor and external ADC, and combines temperature and humidity data to provide user recommendations on when to open or close the heater.

---

## What it does
**This project implements a smart indoor energy-awareness system that helps users avoid unnecessary heating energy waste caused by opening windows while heating is on.**

The system continuously monitors the indoor environment using multiple sensors, including **temperature**, **humidity**, and **window state (open/closed)**. These raw sensor readings are transmitted wirelessly via MQTT to a client application, where they are processed and fused to infer the current environmental context.

Based on the fused sensor data, the system controls the motor to turn on/off the heater and provides **clear, actionable recommendations** to the user, such as:

* closing the window when heating is active,
* turning off heating when ventilation is detected,
* or maintaining the current state when conditions are energy-efficient.

This embedded-system product is desgined to be **scalable and extensible**, supporting additional sensors, multiple rooms, and future integration with smart heating systems or building management platforms.

---

## System overview

The system consists of three main layers: an embedded sensor node, a communication layer, and a client-side processing and user interface layer.

### 1. Embedded sensor node (Raspberry Pi)

The embedded device acts as an autonomous sensor node responsible for:

* reading multiple environmental sensors via **low-level I²C communication**,
* sampling data at a fixed and appropriate interval,
* packaging sensor readings into a structured **JSON** format,
* publishing the data to an **MQTT broker**.

### 2. Communication layer (MQTT)

An MQTT broker is used as the communication backbone of the system.
The embedded sensor node publishes sensor data to predefined MQTT topics, while client applications subscribe to these topics to receive updates in real time, 
which enables **low-latency communication** and **scalability to multiple snesors and users**

### 3. Client application and user interface

The client side subscribes to the MQTT data stream and performs:

* parsing and validation of incoming JSON data,
* **sensor data fusion and decision logic** using SQL database,
* presentation of high-level information and recommendations to the user through a web-based interface.
* Real time motor control to turn on/off the heater 

### System data flow

```
Sensors (Temp / Humidity / Window State)
        ↓  I²C
Raspberry Pi (Sensor Node)
        ↓  MQTT (JSON)
     MQTT Broker
        ↓
Client Application / Web UI
        ↓
User Recommendations / Motor Control
```

---

## Hardware & sensors

### Hardware platform

The embedded sensor node is implemented on a **Raspberry Pi** running Linux and Python.
It acts as a standalone IoT device, responsible for sensor acquisition and data transmission.

All sensors are connected via the **I²C bus**, and sensor communication is implemented at the **byte level**.

### Sensor selection

The system uses multiple sensors to capture different aspects of the indoor environment:

| Sensor                                       | Measured quantity        | Purpose in system                                             |
| -------------------------------------------- | ------------------------ | ------------------------------------------------------------- |
| **Si7021**                                   | Temperature, Humidity    | Monitoring indoor comfort and humidity/temperature conditions |
| **ADS1115 (ADC)**                            | Analogue input           | Interface for distance / window state sensing                 |
| **Adafruit 984/HRLV-EZ1 Acoustic proximity** | Window open/closed state | Detecting ventilation while heating is active                 |

### I²C communication

* All sensors are accessed via the Raspberry Pi’s I²C interface.
* Communication is performed using **explicit register-level read/write operations**.
* Sensor data is converted from raw readings into physical units (e.g. °C, %RH) before transmission.

---

## Data pipeline (MQTT + JSON)

### MQTT architecture

* The Raspberry Pi sensor node acts as an **MQTT publisher**.
* Client applications and the web interface act as **MQTT subscribers**.
* An MQTT broker decouples data producers from consumers, enabling scalable and flexible system expansion.

This publish–subscribe model allows multiple clients to receive the same sensor data stream without modifying the embedded device.

### Topic structure

Sensor data is published to a dedicated topic, for example:

```
home/room1/sensors
```

This topic hierarchy is designed to support:

* multiple rooms or sensor nodes,
* future user or building-level extensions,
* simple filtering and subscription by clients.

### Data format

Sensor data is packaged into a single JSON message containing all relevant measurements from one sampling cycle.

Example payload:

```json
{
  "timestamp": "2026-02-01T18:32:10",
  "temperature": 21.4,
  "humidity": 46.2,
  "window_distance": 128,
  "window_state": "open"
}
```

### Data rate and reliability

Sensor data is published at a fixed interval (2s) chosen to match the dynamics of indoor environments.
MQTT’s lightweight design ensures:

* low network overhead,
* reliable delivery within a local network,
* tolerance to temporary client disconnections.

The system architecture allows new subscribers to join at any time and immediately begin receiving live data.

---

## Decision / fusion logic

## Web UI

## How to run
### Sensor node (Raspberry Pi)
### Client / Web UI

## Demo
- Marketing website:
- Demo video:

## Future work (advanced features)


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



## Hardware & sensors

## Data pipeline (MQTT + JSON)

## Decision / fusion logic

## Web UI

## How to run
### Sensor node (Raspberry Pi)
### Client / Web UI

## Demo
- Marketing website:
- Demo video:

## Repository structure

## Future work (advanced features)

## Contributors


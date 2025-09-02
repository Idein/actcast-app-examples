#!/usr/bin/python
# -*- coding:utf-8 -*-
import actfw_core
import time
import bme680

app = actfw_core.Application()


def build_error(device: str, exc: Exception) -> dict:
    return {
        "device": device,
        "type": exc.__class__.__name__,
        "message": str(exc),
    }


while True:
    time.sleep(5)

    actfw_core.heartbeat()
    timestamp = time.time()

    sensor_data = {
        "timestamp": timestamp,
        "pressure": -9999,
        "temperature": -9999.0,
        "humidity": -9999.0,
        "bme688_valid": False,
    }

    error = None

    # BME688/BME680
    try:
        # Try both I2C addresses: 0x76 (PRIMARY) then 0x77 (SECONDARY)
        last_exc = None
        sensor = None
        for addr in (bme680.I2C_ADDR_PRIMARY, bme680.I2C_ADDR_SECONDARY):
            try:
                sensor = bme680.BME680(addr)
                sensor_addr = addr
                break
            except Exception as e:
                last_exc = e
                continue
        if sensor is None:
            raise last_exc if last_exc else RuntimeError("BME680 not found on 0x76/0x77")

        # Configure oversampling and gas heater
        sensor.set_humidity_oversample(bme680.OS_2X)
        sensor.set_pressure_oversample(bme680.OS_4X)
        sensor.set_temperature_oversample(bme680.OS_8X)
        sensor.set_filter(bme680.FILTER_SIZE_3)
        sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        sensor.set_gas_heater_temperature(320)
        sensor.set_gas_heater_duration(150)
        sensor.select_gas_heater_profile(0)

        # Read current data
        # Some libraries require an explicit read call; if available, try it.
        if hasattr(sensor, "get_sensor_data"):
            try:
                sensor.get_sensor_data()
            except Exception:
                pass

        sensor_data["temperature"] = round(sensor.data.temperature, 2)
        sensor_data["pressure"] = round(sensor.data.pressure, 2)
        sensor_data["humidity"] = round(sensor.data.humidity, 2)
        sensor_data["bme688_valid"] = True
        # Include which I2C address worked
        sensor_data["bme688_addr"] = hex(sensor_addr)
        if getattr(sensor.data, "heat_stable", False):
            sensor_data["gas_resistance"] = int(sensor.data.gas_resistance)
    except Exception as e:
        sensor_data["bme688_valid"] = False
        error = build_error("bme688", e)

    payload = {
        "bme_Sensor Data": sensor_data,
    }
    if error:
        payload["error"] = error

    actfw_core.notify([payload])

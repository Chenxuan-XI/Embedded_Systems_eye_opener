import time
from smbus2 import SMBus, i2c_msg

bus = SMBus(1)

# ADS1115 definitions
ADS1115_ADDR = 0x48
REG_CONVERSION = 0x00
REG_CONFIG     = 0x01
ADS1115_CONFIG = 0xC283

def read_ads1115():
    bus.write_i2c_block_data(
        ADS1115_ADDR,
        REG_CONFIG,
        [(ADS1115_CONFIG >> 8) & 0xFF, ADS1115_CONFIG & 0xFF]
    )

    time.sleep(0.02)

    data = bus.read_i2c_block_data(ADS1115_ADDR, REG_CONVERSION, 2)
    raw = (data[0] << 8) | data[1]

    if raw & 0x8000:
        raw -= 0x10000

    return raw

# Si7021 definitions
SI7021_ADDR = 0x40
SI7021_READ_TEMPERATURE = 0xF3
SI7021_READ_HUMIDITY = 0xF5

def read_si7021_temperature():
    write = i2c_msg.write(SI7021_ADDR, [SI7021_READ_TEMPERATURE])
    bus.i2c_rdwr(write)

    time.sleep(0.1)

    read = i2c_msg.read(SI7021_ADDR, 2)
    bus.i2c_rdwr(read)

    data = list(read)
    raw = (data[0] << 8) | data[1]

    temperature = (175.72 * raw) / 65536.0 - 46.85
    return temperature


def read_si7021_humidity():
    write = i2c_msg.write(SI7021_ADDR, [SI7021_READ_HUMIDITY])
    bus.i2c_rdwr(write)

    time.sleep(0.1)

    read = i2c_msg.read(SI7021_ADDR, 2)
    bus.i2c_rdwr(read)

    data = list(read)
    raw = (data[0] << 8) | data[1]

    humidity = (125.0 * raw) / 65536.0 - 6.0
    return humidity


# Main loop
while True:
    try:
        adc_value = read_ads1115()
        temperature = read_si7021_temperature()
        humidity = read_si7021_humidity()

        print(f"ADC raw: {adc_value}")
        print(f"Temperature: {temperature:.2f} °C")
        print(f"Humidity: {humidity:.2f} %RH")
        print("-" * 30)

        time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
        break


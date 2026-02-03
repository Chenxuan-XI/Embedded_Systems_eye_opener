from smbus2 import SMBus
import time

bus = SMBus(1)
ADDR = 0x48

REG_CONVERSION = 0x00
REG_CONFIG     = 0x01

CONFIG = 0xC283

def read_ads1115():
    bus.write_i2c_block_data(
        ADDR,
        REG_CONFIG,
        [(CONFIG >> 8) & 0xFF, CONFIG & 0xFF]
    )

    time.sleep(0.02)

    # read conversion
    data = bus.read_i2c_block_data(ADDR, REG_CONVERSION, 2)
    raw = (data[0] << 8) | data[1]

    if raw & 0x8000:
        raw -= 0x10000

    return raw

while True:
    try:
        value = read_ads1115()
        print("ADC raw:", value)
        time.sleep(0.5)
    except Exception as e:
        print("Error:", e)
        break

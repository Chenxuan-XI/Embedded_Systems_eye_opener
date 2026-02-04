import time
from smbus2 import SMBus

ADDR = 0x5A

REG_MEAS_MODE  = 0x01
REG_ALG_RESULT = 0x02
REG_HW_ID      = 0x20
REG_APP_START  = 0xF4
REG_SW_RESET   = 0xFF

DATA_READY_MASK = 0x08
ERROR_MASK      = 0x01


def init_ccs811(bus):
    if bus.read_byte_data(ADDR, REG_HW_ID) != 0x81:
        raise RuntimeError("CCS811 not found")

    bus.write_i2c_block_data(ADDR, REG_APP_START, [])
    time.sleep(0.1)

    # Drive mode 1 (1s)
    bus.write_byte_data(ADDR, REG_MEAS_MODE, 0b00010000)
    time.sleep(1.0)


def read_valid(bus):
    data = bus.read_i2c_block_data(ADDR, REG_ALG_RESULT, 8)

    status = data[4]
    if status & ERROR_MASK or not (status & DATA_READY_MASK):
        return None

    eco2 = (data[0] << 8) | data[1]
    tvoc = (data[2] << 8) | data[3]

    if eco2 >= 32768:  # invalid marker
        return None

    return eco2, tvoc


def main():
    with SMBus(3) as bus:
        init_ccs811(bus)

        while True:
            try:
                result = read_valid(bus)
                if result:
                    eco2, tvoc = result
                    print(f"eCO2={eco2} ppm  TVOC={tvoc} ppb")
                time.sleep(0.5)
            except OSError:
                time.sleep(0.2)


if __name__ == "__main__":
    main()

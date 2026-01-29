import pigpio
import time

TRIG = 23
ECHO = 24

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpiod not running. Start with: sudo pigpiod")

pi.set_mode(TRIG, pigpio.OUTPUT)
pi.set_mode(ECHO, pigpio.INPUT)

# Keep trigger low
pi.write(TRIG, 0)
time.sleep(0.05)

start_tick = None
pulse_len_us = None

def cbf(gpio, level, tick):
    global start_tick, pulse_len_us
    if gpio != ECHO:
        return
    if level == 1:               # rising edge
        start_tick = tick
    elif level == 0 and start_tick is not None:  # falling edge
        pulse_len_us = pigpio.tickDiff(start_tick, tick)

cb = pi.callback(ECHO, pigpio.EITHER_EDGE, cbf)

def read_distance_cm(timeout_s=0.03):
    """Returns distance in cm, or None on timeout."""
    global pulse_len_us, start_tick
    pulse_len_us = None
    start_tick = None

    # 10us trigger pulse
    pi.gpio_trigger(TRIG, 10, 1)

    t0 = time.time()
    while pulse_len_us is None:
        if time.time() - t0 > timeout_s:
            return None
        time.sleep(0.0001)

    # Speed of sound ~343 m/s => 29.1 us per cm round trip is 58.2 us per cm? (common formula)
    # Distance(cm) = pulse_us / 58.0
    return pulse_len_us / 58.0

try:
    while(True):
        d = read_distance_cm()
        if d is None:
            print("Timeout")
        else:
            print(f"{d:.1f} cm")
        time.sleep(2)
finally:
    cb.cancel()
    pi.stop()

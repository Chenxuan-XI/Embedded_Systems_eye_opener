import pigpio, time

pi = pigpio.pi()          # connects to local pigpiod
GPIO = 18                 # servo signal wire here

pi.set_mode(GPIO, pigpio.OUTPUT)

# SG90 typical range: 500–2500 us (some prefer 600–2400)
for pw in (500, 1500, 2500, 1500):
    pi.set_servo_pulsewidth(GPIO, pw)
    time.sleep(1)

pi.set_servo_pulsewidth(GPIO, 0)   # stop pulses
pi.stop()

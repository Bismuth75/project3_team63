import time
import math
from robot import IMU

imu = IMU()
#imu.calibrate()
imu.start()

try:
    while True:
        x, y, z = imu.get_rates()
        heading = math.degrees(imu.get_heading())
        print(f"X: {x:7.2f}  Y: {y:7.2f}  Z: {z:7.2f} deg/s   Heading: {heading:7.2f} deg")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("terminated")
finally:
    imu.running = False

import math
import threading
import time
#import constants as c
from utils import wrap
#from grove.grove_imu_9dof_icm20600_ak09918 import GroveIMU9DOFICM20600
from smbus2 import SMBus

class IMU:
    def __init__(self, hz=200):
        #self.imu = GroveIMU9DOFICM20600()
        self.imu = ICM20600()
        self.period = 1.0 / hz
        self.bias_X = 0.0
        self.bias_Y = 0.0
        self.bias_Z = 0.0
        self.heading = 0.0
        self.rates = (0.0, 0.0, 0.0)
        self.lock = threading.Lock()
        self.running = False
        
    def stop(self):
        self.running = False
        
    def calibrate(self, seconds=3):
        sums = [0,0,0]
        n = 0
        t_end = time.monotonic() + seconds
        while time.monotonic() < t_end:
            gx, gy, gz = self.imu.get_gyro()
            sums[0] += gx
            sums[1] += gy
            sums[2] += gz
            n += 1
            time.sleep(0.005)
        self.bias_X, self.bias_Y, self.bias_Z = (s/n for s in sums)
        print("calibrated")
        
    def start(self):
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        last = time.monotonic()
        while self.running:
            gx, gy, gz = self.imu.get_gyro()
            ax, ay, az = self.imu.get_accel()
            gx -= self.bias_X
            gy -= self.bias_Y
            gz -= self.bias_Z
            now = time.monotonic()
            dt = now - last
            last = now
            with self.lock:
                self.heading -= math.radians(gz) * dt
                self.rates = (gx, gy, gz)
            time.sleep(self.period)
    
    def get_heading(self):
        with self.lock:
            return wrap(self.heading)
        
    def get_heading_rate(self):
        with self.lock:
            return -math.radians(self.rates[2])
        
    def get_rates(self):
        with self.lock:
            return self.rates  

#claude wrote this because the pi wasn't reading through the I2C properly?
#idk something weird was going on hopefully we figure it out but this is the replacement for now
class ICM20600:
    """Minimal driver: gyro in deg/s, accel in mg (same as grove.py)."""
    def __init__(self, bus=1, addr=0x69):
        self.bus = SMBus(bus)
        self.addr = addr
        who = self.bus.read_byte_data(addr, 0x75)     # WHO_AM_I register
        if who != 0x11:
            raise RuntimeError(f"Unexpected chip ID 0x{who:02X} at address 0x{addr:02X}")
        self.bus.write_byte_data(addr, 0x6B, 0x01)    # wake up, best clock source
        time.sleep(0.05)
        self.bus.write_byte_data(addr, 0x1A, 0x03)    # low-pass filter ~41 Hz
        self.bus.write_byte_data(addr, 0x1B, 0x08)    # gyro range ±500 deg/s
        self.bus.write_byte_data(addr, 0x1C, 0x00)    # accel range ±2 g

    def _read3(self, reg):
        d = self.bus.read_i2c_block_data(self.addr, reg, 6)
        out = []
        for i in (0, 2, 4):
            v = (d[i] << 8) | d[i + 1]                # combine high and low bytes
            if v >= 0x8000:
                v -= 0x10000                          # convert to signed
            out.append(v)
        return out

    def get_gyro(self):
        return tuple(v / 65.5 for v in self._read3(0x43))           # deg/s

    def get_accel(self):
        return tuple(v / 16384 * 1000 for v in self._read3(0x3B))   # mg
    
if __name__ == "__main__":
    imu = IMU()
    imu.calibrate()
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
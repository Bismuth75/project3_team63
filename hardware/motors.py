import constants as c
from utils import clamp
import math
import time
from buildhat import Motor

class Motors:
    def __init__(self):
        self.motor_L = Motor('A')
        self.motor_R = Motor('B')
        #self.motor_L.set_speed_unit_rpm(True)
        #self.motor_R.set_speed_unit_rpm(True)
        self.last_L = None
        self.last_R = None
    
    def set_rpm(self, rpm_L, rpm_R):
        sL = round(clamp(c.L_DIR * rpm_L, -c.MAX_RPM, c.MAX_RPM), 1)
        sR = round(clamp(c.R_DIR * rpm_R, -c.MAX_RPM, c.MAX_RPM), 1)
        if sL != self.last_L:
            self.motor_L.start(sL)
            self.last_L = sL
        if sR != self.last_R:
            self.motor_R.start(sR)
            self.last_R = sR
    
    def hold(self):
        self.motor_L.start(0)
        self.motor_R.start(0)
        time.sleep(c.BRAKE_TIME)
        self.release()
        
    def release(self):
        self.motor_L.stop()
        self.motor_R.stop()
        self.last_L = None
        self.last_R = None
    
    def get_encoder_R(self):
        return c.R_DIR * math.radians(self.motor_R.get_position())

    def get_encoder_L(self):
        return c.L_DIR * math.radians(self.motor_L.get_position())
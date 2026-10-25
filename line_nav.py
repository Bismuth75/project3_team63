import math
import time
import constants as c
from utils import wrap, clamp

class Line_Nav:
    def __init__(self, drive, imu, line):
        self.drive = drive
        self.imu = imu
        self.line = line
        self.line_zero_heading = None
        self.x0 = None
        self.measured_width = None

    def localize(self):
        #finds horizontal and angular displacement relative to a piece of line
        if self.line.get_line_R() or self.line.get_line_L():
            return False #sensor started on line
        h0 = self.imu.get_heading()
        angle_R = None
        angle_L = None
        while angle_R is None or angle_L is None:
            turned = wrap(self.imu.get_heading() - h0)
            if abs(turned) > c.MAX_SCAN_ANGLE:
                self.drive.stop()
                return False
            if angle_R is None and self.line.get_line_R():
                angle_R = turned
            if angle_L is None and self.line.get_line_L():
                angle_L = turned
            self.drive.set_velocity(0, c.OMEGA_LINE_SCAN)
            time.sleep(c.LOOP_SLEEP)
        self.drive.stop()

        S = angle_R + angle_L
        half_D = 0.5 * (angle_R - angle_L)
        k = c.SENSOR_RADIUS * math.cos(half_D)
        q = k * k - c.LINE_HALF_WIDTH ** 2
        if k <= 0 or q < 0: 
            return False #edge case errors?
        psi = math.atan2(math.sqrt(q), c.LINE_HALF_WIDTH)
        angular_offset = psi - S / 2
        self.line_zero_heading = wrap(h0 - angular_offset)
        self.x0 = c.SENSOR_RADIUS * math.sin(psi) * math.sin(half_D)
        return True
    
    def localize_advanced(self):
        on_R = self.line.get_line_R()
        on_L = self.line.get_line_L()
        if on_R or on_L:
            return False
        h0 = self.imu.get_heading()
        R_in = R_out = L_in = L_out = None
        prev_R = on_R
        prev_L = on_L
        while L_out is None or R_out is None:
            turned = wrap(self.imu.get_heading() - h0)     # CW+
            if abs(turned) > c.MAX_SCAN_ANGLE:
                self.drive.stop()
                return False
            on_R = self.line.get_line_R()
            on_L = self.line.get_line_L()
            
            if R_in is None and on_R and not prev_R:
                R_in = turned
            elif R_in is not None and R_out is None and prev_R and not on_R:
                R_out = turned
            if L_in is None and on_L and not prev_L:
                L_in = turned
            elif L_in is not None and L_out is None and prev_L and not on_L:
                L_out = turned
            
            prev_R, prev_L = on_R, on_L
            self.drive.set_velocity(0, c.OMEGA_LINE_SCAN)
            time.sleep(c.LOOP_SLEEP)
        self.drive.stop()
        
        a1 = math.pi / 2 - (R_in + L_out) / 2     #right edge
        a2 = math.pi / 2 - (R_out + L_in) / 2     #left edge
        if abs(a1 - a2) > c.MAX_HEADING_DISAGREEMENT: #could be used to detect curve/gaps
            return False                        
        a = 0.5 * (a1 + a2) #average two values
        
        cosRin = math.cos(R_in + a) #(w − x0)/r
        cosRout = math.cos(R_out + a) #(-w - x0)/r
        cosLin = math.cos(L_in + a) #(w + x0)/r
        cosLout = math.cos(L_out + a) #(-w + x0)/r
        
        x0 = c.SENSOR_RADIUS / 4 * ((cosLin - cosRin) + (cosLout - cosRout)) #double average to find x offset
        width = c.SENSOR_RADIUS / 2 * ((cosRin + cosLin) - (cosRout + cosLout)) #could be useful for some things later / error deteciton
        
        self.line_zero_heading = wrap(h0 - a)
        self.x0 = x0
        self.measured_width = width
        return True  
    
    def line_center(self):
        if abs(self.x0) >= c.LINE_CENTER_THRESHOLD:
            approach = wrap(self.line_zero_heading - c.APPROACH_ANGLE * math.copysign(1, self.x0))
            dist = abs(self.x0) / math.sin(c.APPROACH_ANGLE)
            if not self.drive.turn_to(approach):
                return False
            if not self.drive.drive_distance(dist, c.APPROACH_V, approach):
                return False
        return self.drive.turn_to(self.line_zero_heading)
    
    def primitive_line_follow(self, v):
        on_R = self.line.get_line_R()
        on_L = self.line.get_line_L()
        if on_R and not on_L:
            omega = c.OMEGA_FOLLOW
        elif on_L and not on_R:
            omega = -c.OMEGA_FOLLOW
        else:
            omega = 0
        self.drive.set_velocity(v, omega)
        
if __name__ == "__main__":
    from hardware.imu import IMU
    from hardware.motors import Motors
    from hardware.line_finder import Line
    from drive import Drive

    imu = IMU()
    imu.calibrate()
    imu.start()
    drive = Drive(imu, Motors())
    nav = Line_Nav(drive, imu, Line())
    
    try:
        while True:
            nav.primitive_line_follow(20)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.release()
        imu.stop()
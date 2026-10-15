import time
import math
import constants as c
from collections import deque
from utils import wrap, clamp
from imu import IMU
from ultrasonic import Ultrasonic
from line_finder import Line
from hall_sensor import Hall
from button import Switch
from buildhat import Motor


#hardware init
motor_L = Motor('A')
motor_R = Motor('B')
motor_L.set_speed_unit_rpm(True)
motor_R.set_speed_unit_rpm(True)



#global fx
def get_encoder_R():
    return c.R_DIR * math.radians(motor_R.get_position())

def get_encoder_L():
    return c.L_DIR * math.radians(motor_L.get_position())

#classes   
class Drive:
    def __init__(self, imu):
        self.imu = imu
        self.last_R = None
        self.last_L = None
    
    def set_velocity(self, v, omega):
        vL = v + omega * c.TRACK_RADIUS
        vR = v - omega * c.TRACK_RADIUS
        sL = round(clamp(c.L_DIR * vL / c.WHEEL_RADIUS / c.RPM_TO_RADS, -c.MAX_RPM, c.MAX_RPM),1)
        sR = round(clamp(c.R_DIR * vR / c.WHEEL_RADIUS / c.RPM_TO_RADS, -c.MAX_RPM, c.MAX_RPM),1)
        if sL != self.last_L:
            motor_L.start(sL)
            self.last_L = sL
        if sR != self.last_R:
            motor_R.start(sR)
            self.last_R = sR
    
    def stop(self):
        motor_L.start(0)
        motor_R.start(0)
        self.last_L = 0
        self.last_R = 0
        
    def release(self):
        motor_L.stop()
        motor_R.stop()
    
    def turn_to(self, target, error_margin=math.radians(1), timeout=3):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            err = wrap(target - self.imu.get_heading())
            if abs(err) < error_margin:
                self.stop()
                return True
            w = clamp(c.P_TURN * err, -c.OMEGA_MAX, c.OMEGA_MAX) #keeps target omega in range
            w = math.copysign(max(c.OMEGA_MIN, abs(w)), err) #prevents |omega| from going under min movement speed
            self.set_velocity(0, w)
            time.sleep(c.LOOP_SLEEP)
        self.stop()
        return False
        
    def turn_by(self, turn_amount, **kw):
        return self.turn_to(wrap(self.imu.get_heading() + turn_amount), **kw)
        
    def drive_distance(self, dist, v_target, hold_heading, error_margin=0.1, timeout=10):
        t0 = time.monotonic()
        start_R = get_encoder_R()
        start_L = get_encoder_L()
        while time.monotonic() - t0 < timeout:
            angle_err = wrap(hold_heading - self.imu.get_heading())
            traveled = ((get_encoder_R() - start_R) + (get_encoder_L() - start_L)) * c.WHEEL_RADIUS / 2
            distance_err = dist - traveled
            if abs(distance_err) < error_margin:
                self.stop()
                return True
            v = clamp(c.P_STRAIGHT * distance_err, -v_target, v_target) #keeps target v in range
            v = math.copysign(max(c.V_MIN, abs(v)), distance_err) #prevents |v| from going under min movement speed
            self.set_velocity(v, clamp(c.P_TURN * angle_err, -c.OMEGA_MAX, c.OMEGA_MAX))
            time.sleep(c.LOOP_SLEEP)
        self.stop()
        return False
    
    def driv_indefinite(self, v_target, hold_heading):
        pass

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

class Obstacle:
    def __init__(self, drive, ultra):
        self.drive = drive
        self.ultra = ultra
        self.history = deque(maxlen=c.OBSTACLE_EVENT_STRICTNESS)
        
    def obstacle_detect(self):
        dist = self.ultra.get_distance()
        if dist is not None:
            self.history.append(dist < c.OBSTACLE_THRESHOLD)
        return len(self.history) == c.OBSTACLE_EVENT_STRICTNESS and all(self.history)
    
class Cargo:
    def __init__(self, drive, hall, imu):
        self.drive = drive
        self.hall = hall
        self.imu = imu
        self.cargo = []
        
    def homing(self):
        heading_hold = self.imu.get_heading()
        while not self.hall.get_hall():
            self.drive.set_velocity(c.HOMING_V)
            
        
    

if __name__ == "__main__":
    
    imu = IMU()
    imu.calibrate()
    imu.start()

    line = Line()
    ultra = Ultrasonic()
    hall = Hall()
    button = Switch()
    
    drive = Drive(imu)
    nav = Line_Nav(drive, imu, line)
    obstacle = Obstacle(drive, ultra)
    
    
# STATE LIST
# start: something that runs at the beginning
# end: stops robot
# localize: actively turning to localize
# center: moving to center of line
# follow: line following behavior
# follow2: following if the line is dotted or dashed?
# obstacle: sees an obstacle
# traversing: going over obstacle
# recovery: finding its way back to line
# navigating: turning at a fork?
# delivering: dropping off cargo

    state = "start"
    try:
        while state != "end":
            if state == "start":
                #idk maybe something here
                state = "localize"
            elif state == "localize":
                state = "center" if nav.localize_advanced() else "x"
            elif state == "center":
                state = "follow" if nav.line_center() else "x"
            elif state == "follow":
                nav.primitive_line_follow(c.V_MAX)
                if obstacle.obstacle_detect():
                    state = "obstacle"
            elif state == "obstacle":
                pass
            time.sleep(c.LOOP_SLEEP)
    finally:
        drive.stop()
        drive.release()
        imu.stop()
                
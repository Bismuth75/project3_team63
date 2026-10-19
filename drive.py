import time
import math
import constants as c
from utils import wrap, clamp

class Drive:
    def __init__(self, imu, motors):
        self.imu = imu
        self.m = motors
        self.driving = False

    def set_velocity(self, v, omega):
        vL = v + omega * c.TRACK_RADIUS
        vR = v - omega * c.TRACK_RADIUS
        k = c.RADS_TO_RPM / c.WHEEL_RADIUS
        self.m.set_rpm(vL * k, vR * k)

    def stop(self):
        self.m.hold()

    def release(self):
        self.m.release()
    
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
        start_R = self.m.get_encoder_R()
        start_L = self.m.get_encoder_L()
        while time.monotonic() - t0 < timeout:
            angle_err = wrap(hold_heading - self.imu.get_heading())
            traveled = ((self.m.get_encoder_R() - start_R) + (self.m.get_encoder_L() - start_L)) * c.WHEEL_RADIUS / 2
            distance_err = dist - traveled
            if abs(distance_err) < error_margin:
                self.stop()
                return True
            v = clamp(c.P_STRAIGHT * distance_err, -v_target, v_target) #keeps target v in range
            v = math.copysign(max(c.V_MIN, abs(v)), distance_err) #prevents |v| from going under min movement speed
            self.set_velocity(v, clamp(c.P_HEADING * angle_err, -c.OMEGA_MAX, c.OMEGA_MAX))
            time.sleep(c.LOOP_SLEEP)
        self.stop()
        return False
    
    def drive_straight(self, v):
        if not self.driving:
            hold_heading = self.imu.get_heading()
        self.driving = True
        angle_err = wrap(hold_heading - self.imu.get_heading())
        omega = clamp(c.P_TURN * angle_err, -c.OMEGA_MAX, c.OMEGA_MAX)
        self.set_velocity(v, omega)
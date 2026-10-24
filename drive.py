import time
import math
import constants as c
from utils import wrap, clamp

class Drive:
    def __init__(self, imu, motors):
        self.imu = imu
        self.m = motors
        self.hold_heading = None
        self.v_last = 0.0

    def ramp(self, v_target, dt):
        step = c.ACCEL_MAX * dt
        self.v_last = clamp(v_target, self.v_last - step, self.v_last + step)
        return self.v_last

    def set_velocity(self, v, omega):
        vL = v + omega * c.TRACK_RADIUS
        vR = v - omega * c.TRACK_RADIUS
        k = c.RADS_TO_RPM / c.WHEEL_RADIUS
        self.m.set_rpm(vL * k, vR * k)

    def stop(self):
        self.m.hold()
        self.hold_heading = None
        self.v_last = 0.0

    def release(self):
        self.m.release()
        self.hold_heading = None
    
    def turn_to(self, target, error_margin=math.radians(1), timeout=3):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            err = wrap(target - self.imu.get_heading())
            if abs(err) < error_margin:
                self.stop()
                return True
            w = c.P_TURN * err - c.D_TURN * self.imu.get_heading_rate()
            w = clamp(w, -c.OMEGA_MAX, c.OMEGA_MAX) #keeps target omega in range
            w = math.copysign(max(c.OMEGA_MIN, abs(w)), w) #prevents |omega| from going under min movement speed
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
        prev_traveled = 0.0
        prev_t = t0
        v_meas = 0.0
        starting = True
        while time.monotonic() - t0 < timeout:
            now = time.monotonic()
            traveled = ((self.m.get_encoder_R() - start_R) + (self.m.get_encoder_L() - start_L)) * c.WHEEL_RADIUS / 2
            
            #encoder noise filter
            dt = now - prev_t
            if dt > 0:
                v_raw = (traveled - prev_traveled) / dt
                v_meas = c.V_FILTER * v_meas + (1 - c.V_FILTER) * v_raw
                prev_traveled, prev_t = traveled, now
            
            distance_err = dist - traveled
            if abs(distance_err) < error_margin:
                self.stop()
                return True

            v = c.P_STRAIGHT * distance_err - c.D_STRAIGHT * v_meas
            v = clamp(v, -v_target, v_target)
            v = math.copysign(max(c.V_MIN, abs(v)), v)
            if starting:
                ramped = self.ramp(v, dt)
                if abs(ramped - v) < 0.01:
                    starting = False
                v = ramped
            angle_err = wrap(hold_heading - self.imu.get_heading())
            omega = c.P_HEADING * angle_err - c.D_HEADING * self.imu.get_heading_rate()
            omega = clamp(omega, -c.OMEGA_MAX, c.OMEGA_MAX)
            self.set_velocity(v, omega)
            time.sleep(c.LOOP_SLEEP)
        self.stop()
        return False
    

    def drive_straight(self, v):
        if self.hold_heading is None:
            self.hold_heading = self.imu.get_heading()
        angle_err = wrap(self.hold_heading - self.imu.get_heading())
        omega = clamp(c.P_HEADING * angle_err - c.D_HEADING * self.imu.get_heading_rate(), -c.OMEGA_MAX, c.OMEGA_MAX)
        self.set_velocity(v, omega)
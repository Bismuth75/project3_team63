from buildhat import Motor
from basehat import UltrasonicSensor
import math
import time
import sys

ULTRASONIC_PORT = 18
RPM_PER_UNIT = 1.5
TRACK_RADIUS = 8
WHEEL_RADIUS = 4
RADS_TO_RPM = 30 / math.pi
CRUISE_SPEED = 5
SLOW_THRESHOLD = 35
SLOW_SPEED = 1
TURN_THRESHOLD = 20

class Ultrasonic:
    
    def __init__(self):
        self.ultra = UltrasonicSensor(ULTRASONIC_PORT)

    def get_distance(self):
        return self.ultra.getDist

   
def set_rpm(rpm_L, rpm_R):
    motor_L.start(-rpm_L / RPM_PER_UNIT)
    motor_R.start(rpm_R / RPM_PER_UNIT)
    
def set_velocity(v, omega):
    vL = v + omega * TRACK_RADIUS
    vR = v - omega * TRACK_RADIUS
    k = RADS_TO_RPM / WHEEL_RADIUS
    set_rpm(vL * k, vR * k)
    
def hold():
    motor_L.start(0)
    motor_R.start(0)
    motor_L.stop()
    motor_R.stop()

def turn_off():
    set_velocity(0, 0.6)
    time.sleep(3)
    set_velocity(10, 0)
    time.sleep(2)
    set_velocity(0, -0.6)
    time.sleep(3)
    hold()
    

#hardware init
motor_L = Motor('A')
motor_R = Motor('B')

ultra = Ultrasonic()

state = "cruise"
obstacles = []
try:
    while True:
        if state == "cruise":
            set_velocity(CRUISE_SPEED, 0)
        elif state == "slow":
            set_velocity(SLOW_SPEED, 0)
        elif state == "turn":
            turn_off()
            sys.exit()
        dist = ultra.get_distance()
        if dist is None:
            dist = SLOW_THRESHOLD + 1
        if dist < TURN_THRESHOLD:
            obstacles.append(True)
            if all(obstacles[-5:]):
                state = "turn"
        elif dist < SLOW_THRESHOLD:
            obstacles.append(False)
            state = "slow"
        elif dist >= SLOW_THRESHOLD:
            obstacles.append(False)
            state = "cruise"
        
except KeyboardInterrupt:
    print("terminated")
finally:
    hold()
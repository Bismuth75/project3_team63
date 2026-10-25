import constants as c
import time
import math
from hardware.imu import IMU
from utils import wrap, clamp
from hardware.button import Switch
from hardware.motors import Motors
from drive import Drive

def straight_drive(drive, imu, button, v): #use to tune P_HEADING
    while True:
        while not button.on:
            time.sleep(c.LOOP_SLEEP)
        hold_heading = imu.get_heading()
        while button.on:
            angle_err = wrap(hold_heading - imu.get_heading())
            omega = clamp(c.P_HEADING * angle_err, -c.OMEGA_MAX, c.OMEGA_MAX)
            drive.set_velocity(v, omega)
            time.sleep(c.LOOP_SLEEP)
        drive.stop()

def turn_test(drive, button, imu, turn_amount, wait):#use to tune P_TURN and OMEGA_MIN
   turns = 1
   first_heading = imu.get_heading()
   while True:
        target = wrap(first_heading + math.radians(turn_amount) * turns)
        drive.turn_to(first_heading + math.radians(turn_amount) * turns)
        turns += 1
        current = imu.get_heading()
        print(f"Target: {target} Current: {current}")
        time.sleep(wait)
        
def distance_test(drive, imu, button, distance, v):
    while True:
        while not button.on:
            time.sleep(c.LOOP_SLEEP)
        while button.on:
            drive.drive_distance(distance, v, imu.get_heading())

def min_test(drive, v, omega):
    while True:
        drive.set_velocity(v, omega)
        if button.on:
            v += 0.1
            omega += 0.02
        print(f"v: {v} omega: {omega}")
            
if __name__ == "__main__":
    imu = IMU()
    imu.calibrate()
    imu.start()
    motors = Motors()
    drive = Drive(imu, motors)
    button = Switch()
    
    try:
        #straight_drive(drive, imu, button, -10)
        #drive.drive_distance(60, 30, imu.get_heading())
        #turn_test(drive, button, imu, 90, 3)
        #min_test(drive, 4, 0)
        #distance_test(drive, imu, button, 20, 5)
        #drive.drive_distance(90, 60, imu.get_heading())
        while True:
            drive.drive_straight(30)
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.release()
        imu.stop()
    
    
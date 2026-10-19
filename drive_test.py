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
            omega = clamp(c.P_TURN * angle_err, -c.OMEGA_MAX, c.OMEGA_MAX)
            drive.set_velocity(v, omega)
            time.sleep(c.LOOP_SLEEP)
        drive.stop()

def turn_test(drive, button, turn_amount, wait): #use to tune P_TURN and OMEGA_MIN
    while True:
        while not button.on:
            time.sleep(c.LOOP_SLEEP)
        while button.on:
            drive.turn_by(math.radians(turn_amount))
            time.sleep(wait)
        
def distance_test(drive, imu, button, distance, v):
    while True:
        while not button.on:
            time.sleep(c.LOOP_SLEEP)
        while button.on:
            drive.drive_distance(distance, v, imu.get_heading())
            
if __name__ == "__main__":
    imu = IMU()
    imu.calibrate()
    imu.start()
    motors = Motors()
    drive = Drive(imu, motors)
    button = Switch()
    
    try:
        straight_drive(drive, imu, button, 5)
        #turn_test(drive, button, 90, 3)
        #distance_test(drive, imu, button, 20, 5)
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.release()
        imu.stop()
    
    
import time
import constants as c

# hardware
from hardware.imu import IMU
from hardware.motors import Motors
from hardware.line_finder import Line
from hardware.ultrasonic import Ultrasonic
from hardware.hall_sensor import Hall
from hardware.button import Switch

# behavior
from drive import Drive
from line_nav import Line_Nav
from obstacle import Obstacle
from cargo import Cargo

#classes

if __name__ == "__main__":
    
    imu = IMU()
    imu.calibrate()
    imu.start()

    line = Line()
    ultra = Ultrasonic()
    hall = Hall()
    button = Switch()
    motors = Motors()
    
    drive = Drive(imu, motors)
    nav = Line_Nav(drive, imu, line)
    obstacle = Obstacle(drive, ultra)
    cargo = Cargo(drive, hall, imu)
    
    
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
# navigate: choosing which way to go
# turn: turning at fork
# cargo: finding cargo site
# drop: releasing cargo
# return: going back to line

    state = "start"
    try:
        while state != "end":
            if state == "start":
                #idk maybe something here
                state = "follow"
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
                
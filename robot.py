import time
import constants as c

# hardware
from hardware.imu import IMU
from hardware.motors import Motors
from hardware.line_finder import Line
from hardware.ultrasonic import Ultrasonic
from hardware.hall_sensor import Hall
#from hardware.button import Switch
from hardware.arm import Arm

# behavior
from drive import Drive
from line_nav import Line_Nav
from obstacle import Obstacle
from cargo import Cargo

#classes

if __name__ == "__main__":
    
    prev_hall = False
    count = 0
    site = int(input("Enter site number: "))
    match site:
        case 1:
            print("Navitgating to Site Alpha")
        case 2:
            print("Navitgating to Site Beta")
        case 3:
            print("Navitgating to Site Gamma")
        case _:
            print("Invalid Site ID")
    
    imu = IMU()
    imu.calibrate()
    imu.start()

    line = Line()
    ultra = Ultrasonic()
    hall = Hall()
    #button = Switch()
    motors = Motors()
    arm = Arm()
    
    drive = Drive(imu, motors)
    nav = Line_Nav(drive, imu, line)
    obstacle = Obstacle(drive, ultra)
    cargo = Cargo(drive, hall, arm)
    
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
# return: going back to line

    state = "start"
    try:
        while state != "end":
            last = state
            if state == "start":
                #idk maybe something here
                state = "follow"
            elif state == "follow":
                nav.primitive_line_follow(c.V_MAX)
                hall_now = hall.get_hall()
                if obstacle.obstacle_detect():
                    drive.stop()
                    state = "obstacle"
                elif hall_now and not prev_hall:
                    state = "mag"
                prev_hall = hall_now
            elif state == "obstacle":
                if obstacle.obstacle_clear():
                    state = "follow"
            elif state == "mag":
                count += 1
                if count < site:
                    state = "follow"
                elif count == site:
                    #turn off track
                    state = "follow" 
                else:
                    #deposit cargo and return to track
                    state = "return"
            elif state == "return":
                nav.primitive_line_follow(c.V_MAX)
                #some sort of condition to get back on the main track
            if last != state:
                print(f"State: {state}")
            time.sleep(c.LOOP_SLEEP)
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.stop()
        drive.release()
        imu.stop()
                
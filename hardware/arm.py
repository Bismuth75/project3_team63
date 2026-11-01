import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants as c
from buildhat import Motor

class Arm:
    def __init__(self):
        self.motor = Motor('C')
        self.is_open = None

    def open_(self):
        self.motor.run_to_position(c.ARM_OPEN, c.ARM_SPEED, blocking=False)
        self.is_open = True

    def close(self):
        self.motor.run_to_position(c.ARM_CLOSE, c.ARM_SPEED, blocking=False)
        self.is_open = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open_()
            
if __name__ == "__main__":
    
    arm = Arm()
    
    try:
        while True:
            arm.toggle()
            if arm.is_open:
                print("Open")
            else:
                print("Closed")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("terminated")
    finally:
        arm.motor.stop()
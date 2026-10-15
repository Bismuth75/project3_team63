from gpiozero import DigitalInputDevice
import constants as c
import time

class Hall:
    def __init__(self):
        self.hall = DigitalInputDevice(c.HALL_PORT)
        
    def get_hall(self):
        if self.hall.value != None:
            return not self.hall.value
        return False
    
if __name__ == "__main__":
    sensor = Hall()
    try:
        while True:
            print(sensor.hall.value)
            print(sensor.get_hall())
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("teminated")
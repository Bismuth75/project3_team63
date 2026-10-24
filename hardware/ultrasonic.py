from basehat import UltrasonicSensor
import time, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import constants as c

class Ultrasonic:
    
    def __init__(self):
        self.ultra = UltrasonicSensor(c.ULTRASONIC_PORT)

    def get_distance(self):
        return self.ultra.getDist
  
#testing
if __name__ == "__main__":
    sensor = Ultrasonic()
    try:
        while True:
            print(sensor.get_distance())
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("terminated")



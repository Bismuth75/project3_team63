from basehat import UltrasonicSensor
import constants as c
import time

class Ultrasonic:
    
    def __init__(self):
        self.ultra = UltrasonicSensor(c.ULTRASONIC_PORT)

    def get_distance(self):
        return self.ultra.getDist
  
#testing
if __name__ == "__main__":
    sensor = Ultrasonic()
    while True:
        print(sensor.obstacle_detect())
        time.sleep(0.1)



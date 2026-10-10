from basehat import UltrasonicSensor
from collections import deque
import constants as c
import time

class ultrasonic:
    
    def __init__(self):
        self.ultra = UltrasonicSensor(c.ULTRASONIC_PORT)
        self.history = deque(maxlen=c.OBSTACLE_EVENT_STRICTNESS)
    
    def obstacle_detect(self):
        value = self.ultra.getDist
        if value is not None:
            self.history.append(value < c.OBSTACLE_THRESHOLD)
        return len(self.history) == c.OBSTACLE_EVENT_STRICTNESS and all(self.history)
    
sensor = ultrasonic()

while True:
    print(sensor.obstacle_detect())
    time.sleep(0.1)



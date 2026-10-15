import constants as c
import time
from grove.gpio import GPIO

class Line:
    
    def __init__(self):
        self.line_R = GPIO(c.LINE_R_PORT, GPIO.IN)
        self.line_L = GPIO(c.LINE_L_PORT, GPIO.IN) 

    def get_line_R(self):
        return bool(self.line_R.value)

    def get_line_L(self):
        return bool(self.line_L.value)


if __name__ == "__main__":
    try:
        while True:
            print("Right: {get_line_R()} Left: {get_line_L()}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("terminated")
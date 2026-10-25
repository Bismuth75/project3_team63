from grove.gpio import GPIO
import time, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import constants as c

class Line:
    
    def __init__(self):
        self.line_R = GPIO(c.LINE_R_PORT, GPIO.IN)
        self.line_L = GPIO(c.LINE_L_PORT, GPIO.IN) 
        #self.line_M = GPIO(c.LINE_M_PORT, GPIO.IN)

    def get_line_R(self):
        return not bool(self.line_R.read())

    def get_line_L(self):
        return not bool(self.line_L.read())
    
    # def get_line_M(self):
    #     return bool(self.line_M.read())

if __name__ == "__main__":
    sensor = Line()
    try:
        while True:
            right = sensor.get_line_R()
            left = sensor.get_line_L()
            #middle = sensor.get_line_M()
            print(f"Right: {right} Left: {left}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("terminated")
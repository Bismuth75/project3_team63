import time
import constants as c
from collections import deque

class Obstacle:
    def __init__(self, drive, ultra):
        self.drive = drive
        self.ultra = ultra
        self.history = deque(maxlen=c.OBSTACLE_EVENT_STRICTNESS)

    def obstacle_detect(self):
        dist = self.ultra.get_distance()
        if dist is not None:
            self.history.append(dist < c.OBSTACLE_THRESHOLD)
        return len(self.history) == c.OBSTACLE_EVENT_STRICTNESS and all(self.history)


if __name__ == "__main__":
    from hardware.imu import IMU
    from hardware.motors import Motors
    from hardware.ultrasonic import Ultrasonic
    from drive import Drive

    imu = IMU()
    imu.calibrate()
    imu.start()
    drive = Drive(imu, Motors())
    obstacle = Obstacle(drive, Ultrasonic())

    try:
        while not obstacle.obstacle_detect():
            drive.drive_straight(20)
            print(obstacle.ultra.get_distance())
            time.sleep(c.LOOP_SLEEP)
        drive.stop()
        print("Obstacle detected at", obstacle.ultra.get_distance(), "cm")
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.release()
        imu.stop()
import time
import constants as c

class Cargo:
    def __init__(self, drive, hall, arm):
        self.drive = drive
        self.hall = hall
        self.arm = arm

    def homing(self, timeout=10):
        self.drive.hold_heading = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if self.hall.get_hall():
                self.drive.stop()
                return True
            self.drive.drive_straight(c.HOMING_V)
            time.sleep(c.LOOP_SLEEP)
        self.drive.stop()
        return False
    
    def drop(self):
        self.drive.turn_by(180)
        self.drive.drive_distance(c.HALL_TO_CARGO_DIST, 20)
        self.arm.toggle()
        self.drive.drive_distance(20, 20)
        self.arm.toggle()

if __name__ == "__main__":
    from hardware.imu import IMU
    from hardware.motors import Motors
    from hardware.hall_sensor import Hall
    from drive import Drive

    imu = IMU()
    imu.calibrate()
    imu.start()
    drive = Drive(imu, Motors())
    cargo = Cargo(drive, Hall(), imu)

    try:
        print("homing:", cargo.homing())
    except KeyboardInterrupt:
        print("terminated")
    finally:
        drive.release()
        imu.stop()
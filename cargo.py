import time
import constants as c

class Cargo:
    def __init__(self, drive, hall, imu):
        self.drive = drive
        self.hall = hall
        self.imu = imu
        self.cargo = []

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
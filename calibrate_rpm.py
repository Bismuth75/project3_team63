from buildhat import Motor
import time

rpms = []

m = Motor('B')

try:
    for i in range(5):
        p0 = m.get_position()
        m.start(50)
        time.sleep(30)
        m.stop()
        deg = m.get_position() - p0
        rpm = abs(deg) / 360 / 30 * 60
        rpms.append(rpm)
        print(rpms)
        time.sleep(2)
except KeyboardInterrupt:
    m.stop()
    print("terminated")

avg = sum(rpms) / len(rpms)
print(f"RPM at speed 50: {avg:.1f}   RPM_PER_UNIT = {avg / 50:.3f}")

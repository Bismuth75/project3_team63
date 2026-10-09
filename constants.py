import math

LOOP_SLEEP = 0.01

#physical constants
TRACK_WIDTH = 10
WHEEL_RADIUS = 4
SENSOR_RADIUS = 4
LINE_HALF_WIDTH = 1.27
L_DIR = -1
R_DIR = 1
RPM_TO_RADS = math.pi / 30

#localization parameters
LINE_CENTER_THRESHOLD = 0.2
APPROACH_ANGLE = math.radians(15)
APPROACH_V = 3
OMEGA_LINE_SCAN = 0.5
MAX_SCAN_ANGLE = math.radians(160)
MAX_HEADING_DISAGREEMENT = math.radians(3) #maybe?

#sensors
LINE_R_PORT = 1
LINE_L_PORT = 2


#base movment parameters
OMEGA_MAX = 4 #rad/s
OMEGA_MIN = 0.2 #rad/s
OMEGA_FOLLOW = 2
V_MAX = 15 #cm/s
V_MIN = 0.1 #cm/s

#PID
P_TURN = 4
P_STRAIGHT = 1.5

import math

LOOP_SLEEP = 0.01
BRAKE_TIME = 0.15

#physical constants
TRACK_RADIUS = 12
RADS_TO_RPM = 30 / math.pi
WHEEL_RADIUS = 4
SENSOR_RADIUS = 4
LINE_HALF_WIDTH = 1.27
L_DIR = -1
R_DIR = 1
HALL_TO_CARGO_DIST = 20
#RPM_TO_RADS = math.pi / 30
#MAX_RPM = 100
L_RPM_PER_UNIT = 1.5
R_RPM_PER_UNIT = 1.589


#localization parameters
LINE_CENTER_THRESHOLD = 0.2
APPROACH_ANGLE = math.radians(15)
APPROACH_V = 3
OMEGA_LINE_SCAN = 0.5
MAX_SCAN_ANGLE = math.radians(160)
MAX_HEADING_DISAGREEMENT = math.radians(3) #maybe?

#homing parameters
HOMING_V = 3

#sensor ports
LINE_R_PORT = 26
LINE_L_PORT = 24
ULTRASONIC_PORT = 18
HALL_PORT = 5
BUTTON_PORT = 16

#sensor constants
OBSTACLE_THRESHOLD = 4.5 #cm
OBSTACLE_EVENT_STRICTNESS = 5 #number of "True" readings until considered positive detection
HALL_THRESHOLD = 5 #magnetic field strength

#base movment parameters
ACCEL_MAX = 12 #cm/s^2
OMEGA_MAX = 4 #rad/s
OMEGA_MIN = 0.5 #rad/s
OMEGA_FOLLOW = 1
V_MAX = 10 #cm/s
V_MIN = 4 #cm/s

#arm parameters
ARM_OPEN = 0
ARM_CLOSE = 130
ARM_SPEED = 50

#PID
V_FILTER = 0.7 #noise filter for encoders

P_TURN = 3
D_TURN = 0.5

P_STRAIGHT = 1.5
D_STRAIGHT = 0.4
P_HEADING = 7
D_HEADING = 0.1

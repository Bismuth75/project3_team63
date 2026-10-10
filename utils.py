import math

def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


"""
utils.py

General helper functions used throughout the package.
"""

import math

import time


########################################################

def clamp(value, minimum, maximum):

    return max(minimum, min(value, maximum))


########################################################

def radians(angle):

    return math.radians(angle)


########################################################

def degrees(angle):

    return math.degrees(angle)


########################################################

def euclidean_distance(x1, y1, x2, y2):

    return math.sqrt(

        (x2 - x1)**2 +

        (y2 - y1)**2

    )


########################################################

def heading_difference(a, b):
    """
    Smallest difference between headings.
    """

    diff = (a - b + 180.0) % 360.0 - 180.0

    return abs(diff)


########################################################

def moving_average(values):

    if len(values) == 0:

        return 0.0

    return sum(values) / len(values)


########################################################

class Timer:

    """
    Useful for profiling mapping performance.
    """

    def __init__(self):

        self.start = time.perf_counter()

    def elapsed(self):

        return time.perf_counter() - self.start
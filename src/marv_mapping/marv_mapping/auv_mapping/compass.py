"""
compass.py

Utilities for heading normalization and compass reference handling.

This module contains no ROS dependencies and may be unit tested
independently.
"""

from math import atan2, degrees
from typing import Optional


class Compass:
    """
    Maintains a compass reference frame.

    The Pixhawk reports an absolute magnetic heading.
    The mapper operates in a local reference frame where
    the initial heading is considered zero.
    """

    def __init__(self):

        self._reference_heading: Optional[float] = None

    #########################################################

    @staticmethod
    def normalize(angle: float) -> float:
        """
        Normalize heading into [0,360)
        """

        return angle % 360.0

    #########################################################

    @staticmethod
    def normalize_signed(angle: float) -> float:
        """
        Normalize heading into [-180,180]
        """

        return (angle + 180.0) % 360.0 - 180.0

    #########################################################

    def set_reference(self, heading: float):

        self._reference_heading = self.normalize(heading)

    #########################################################

    @property
    def initialized(self):

        return self._reference_heading is not None

    #########################################################

    def relative_heading(self, heading: float):

        if self._reference_heading is None:
            raise RuntimeError(
                "Compass reference has not been initialized."
            )

        relative = heading - self._reference_heading

        return self.normalize_signed(relative)

    #########################################################

    @staticmethod
    def quaternion_to_yaw(x, y, z, w):
        """
        Convert quaternion into yaw angle.

        Useful if the flight controller publishes
        sensor_msgs/Imu.
        """

        siny = 2.0 * (w * z + x * y)

        cosy = 1.0 - 2.0 * (y * y + z * z)

        yaw = degrees(atan2(siny, cosy))

        return yaw % 360.0
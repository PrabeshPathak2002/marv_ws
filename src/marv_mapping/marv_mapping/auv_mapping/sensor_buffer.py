"""
sensor_buffer.py

Maintains the latest sensor values received from ROS.

The ROS node updates this object whenever a callback
fires. MappingEngine simply asks for the latest snapshot.

No ROS imports required.
"""

import time

from .types import (
    SonarDetection,
    VisionDetection,
    SensorSnapshot,
)


class SensorBuffer:

    def __init__(self):

        self.heading = 0.0

        self.distance = 0.0

        self.depth = None

        self.sonar = None

        self.vision = None

        self.last_update = time.time()

    ########################################################

    def update_heading(
        self,
        heading
    ):

        self.heading = heading

        self.last_update = time.time()

    ########################################################

    def update_distance(
        self,
        distance
    ):
        """
        Dead reckoning distance since previous update.

        This will likely come from your Pixhawk,
        DVL, or future velocity estimator.
        """

        self.distance = distance

        self.last_update = time.time()

    ########################################################

    def update_depth(
        self,
        depth
    ):

        self.depth = depth

        self.last_update = time.time()

    ########################################################

    def update_sonar(
        self,
        sonar: SonarDetection
    ):

        self.sonar = sonar

        self.last_update = time.time()

    ########################################################

    def update_vision(
        self,
        vision: VisionDetection
    ):

        self.vision = vision

        self.last_update = time.time()

    ########################################################

    def clear_transient(self):
        """
        Clear sensors that represent a single observation.

        Heading remains valid.

        Pose remains valid.

        Sonar and vision are assumed to represent
        individual observations.
        """

        self.sonar = None

        self.vision = None

    ########################################################

    def snapshot(self):

        return SensorSnapshot(

            timestamp=self.last_update,

            heading=self.heading,

            distance_traveled=self.distance,

            sonar=self.sonar,

            vision=self.vision,

            depth=self.depth

        )
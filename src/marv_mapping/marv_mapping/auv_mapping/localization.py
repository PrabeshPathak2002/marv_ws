"""
localization.py

Dead reckoning and landmark-assisted localization.
"""

from .types import Pose
from .coordinate_transform import polar_to_cartesian, distance


class Localizer:

    def __init__(self):

        self.pose = Pose()

    #########################################################

    def reset(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
        heading=0.0
    ):

        self.pose.x = x
        self.pose.y = y
        self.pose.z = z

        self.pose.yaw = heading

    #########################################################

    def update_dead_reckoning(
        self,
        heading,
        distance_traveled
    ):
        """
        Move the estimated vehicle position.

        Uses current heading and estimated
        distance traveled.
        """

        x, y = polar_to_cartesian(

            self.pose.x,

            self.pose.y,

            heading,

            distance_traveled

        )

        self.pose.x = x
        self.pose.y = y
        self.pose.yaw = heading

        return self.pose

    #########################################################

    def correct_from_landmark(
        self,
        landmark,
        measured_distance,
        heading
    ):
        """
        Correct vehicle pose using a known landmark.
        """

        x, y = polar_to_cartesian(

            landmark.x,

            landmark.y,

            heading + 180.0,

            measured_distance

        )

        self.pose.x = x
        self.pose.y = y
        self.pose.yaw = heading

        return self.pose

    #########################################################

    def nearest_landmark(
        self,
        database,
        label,
        radius=1.5
    ):

        matches = database.by_label(label)

        best = None

        best_distance = 1e9

        for landmark in matches:

            d = distance(

                self.pose.x,

                self.pose.y,

                landmark.x,

                landmark.y

            )

            if d < radius and d < best_distance:

                best = landmark

                best_distance = d

        return best
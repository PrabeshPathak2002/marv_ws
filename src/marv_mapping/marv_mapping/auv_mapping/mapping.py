"""
mapping.py

High-level mapping engine.

The ROS node should only interact with this class.

All sensor fusion, localization, occupancy updates,
and landmark management are coordinated here.
"""

from .occupancy_grid import OccupancyGrid
from .landmarks import LandmarkDatabase
from .localization import Localizer
from .compass import Compass
from .coordinate_transform import polar_to_cartesian


class MappingEngine:

    def __init__(self):

        self.grid = OccupancyGrid()

        self.landmarks = LandmarkDatabase()

        self.localizer = Localizer()

        self.compass = Compass()

    #########################################################

    @property
    def pose(self):

        return self.localizer.pose

    #########################################################

    def initialize_heading(
        self,
        heading
    ):
        """
        Call once after arming or mission start.
        """

        self.compass.set_reference(heading)

        self.localizer.reset(
            heading=0.0
        )

    #########################################################

    def update(
        self,
        heading,
        distance_traveled,
        sonar_detection=None,
        vision_detection=None
    ):
        """
        Main mapping update.

        This should be called whenever new sensor
        information becomes available.

        Parameters
        ----------

        heading

            Current compass heading.

        distance_traveled

            Dead reckoning estimate since previous update.

        sonar_detection

            SonarDetection object.

        vision_detection

            VisionDetection object.
        """

        relative_heading = self.compass.relative_heading(
            heading
        )

        pose = self.localizer.update_dead_reckoning(

            relative_heading,

            distance_traveled

        )

        if sonar_detection is None:
            return

        obstacle_x, obstacle_y = polar_to_cartesian(

            pose.x,

            pose.y,

            relative_heading,

            sonar_detection.distance

        )

        row, col = self.grid.world_to_grid(

            obstacle_x,

            obstacle_y

        )

        if not self.grid.in_bounds(row, col):
            return

        self.grid.increase(
            row,
            col
        )

        if vision_detection is None:
            return

        self.grid.add_label(

            row,

            col,

            vision_detection.label

        )

        self.landmarks.add(

            vision_detection.label,

            obstacle_x,

            obstacle_y,

            vision_detection.confidence

        )

        landmark = self.localizer.nearest_landmark(

            self.landmarks,

            vision_detection.label

        )

        if landmark is not None:

            self.localizer.correct_from_landmark(

                landmark,

                sonar_detection.distance,

                relative_heading

            )

    ##########################################################################################
    # Optional update function change
    
    # def update(...):

    # relative_heading = self._update_pose(...)

    # if sonar_detection is not None:
    #     self._update_occupancy(
    #         relative_heading,
    #         sonar_detection
    #     )

    # if (
    #     sonar_detection is not None and
    #     vision_detection is not None
    # ):
    #     self._associate_landmark(
    #         relative_heading,
    #         sonar_detection,
    #         vision_detection
    #     )
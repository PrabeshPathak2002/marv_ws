"""
constants.py

Project-wide constants.

Keeping every configurable parameter here makes tuning
the mapping algorithm much easier without searching
through the entire project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MappingConstants:
    """
    Global configuration values.

    All distances are meters.
    All angles are degrees unless otherwise specified.
    """

    # ---------------------------------------------------
    # Occupancy Grid
    # ---------------------------------------------------

    CELL_SIZE = 0.10          # 10 cm resolution

    UNKNOWN = 0.50
    FREE = 0.0
    OCCUPIED = 1.0

    GRID_LENGTH = 300         # 30 m
    GRID_WIDTH = 300          # 30 m

    # ---------------------------------------------------
    # Vision
    # ---------------------------------------------------

    YOLO_CONFIDENCE = 0.50

    CAMERA_FOV = 90.0

    # ---------------------------------------------------
    # Sonar
    # ---------------------------------------------------

    SONAR_FOV = 25.0

    MAX_SONAR_RANGE = 50.0

    # ---------------------------------------------------
    # Localization
    # ---------------------------------------------------

    LANDMARK_MATCH_DISTANCE = 1.0

    # ---------------------------------------------------
    # Bayesian Occupancy Updates
    # ---------------------------------------------------

    OCCUPANCY_INCREMENT = 0.15

    OCCUPANCY_DECREMENT = 0.05

    MAX_OCCUPANCY = 1.0

    MIN_OCCUPANCY = 0.0
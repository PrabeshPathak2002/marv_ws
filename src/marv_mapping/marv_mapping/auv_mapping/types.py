"""
types.py

Data structures shared throughout the mapping library.
"""

from dataclasses import dataclass, field

from typing import List, Optional


# ---------------------------------------------------------
# Vehicle Pose
# ---------------------------------------------------------

@dataclass
class Pose:

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


# ---------------------------------------------------------
# Sonar Detection
# ---------------------------------------------------------

@dataclass
class SonarDetection:

    distance: float

    angle: float

    valid: bool = True


# ---------------------------------------------------------
# Vision Detection
# ---------------------------------------------------------

@dataclass
class VisionDetection:

    label: str

    confidence: float

    pixel_x: int

    pixel_y: int


# ---------------------------------------------------------
# Landmark
# ---------------------------------------------------------

@dataclass
class Landmark:

    label: str

    x: float

    y: float

    z: float = 0.0

    confidence: float = 1.0

    observations: int = 1


# ---------------------------------------------------------
# Occupancy Grid Cell
# ---------------------------------------------------------

@dataclass
class Cell:

    occupancy: float = 0.5

    explored: bool = False

    object_label: str | None = None


# ---------------------------------------------------------
# Complete Map
# ---------------------------------------------------------

@dataclass
class OccupancyGrid:

    width: int

    height: int

    cell_size: float

    cells: List[List[Cell]] = field(default_factory=list)

@dataclass
class SensorSnapshot:
    """
    Complete synchronized view of the vehicle.

    This is the only object passed into MappingEngine.update().
    """

    timestamp: float

    heading: float

    distance_traveled: float

    sonar: Optional[SonarDetection] = None

    vision: Optional[VisionDetection] = None

    depth: Optional[float] = None
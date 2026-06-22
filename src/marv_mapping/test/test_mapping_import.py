"""Smoke test: vendored auv_mapping imports and basic engine use."""

from marv_mapping.auv_mapping.mapping import MappingEngine
from marv_mapping.auv_mapping.types import SonarDetection, VisionDetection


def test_mapping_engine_dead_reckon():
    engine = MappingEngine()
    engine.initialize_heading(90.0)
    engine.update(
        heading=90.0,
        distance_traveled=1.0,
        sonar_detection=SonarDetection(distance=2.0, angle=0.0, valid=True),
        vision_detection=None,
    )
    assert engine.pose.x != 0.0 or engine.pose.y != 0.0


def test_vision_detection_type():
    det = VisionDetection(label='gate', confidence=0.9, pixel_x=640, pixel_y=360)
    assert det.label == 'gate'

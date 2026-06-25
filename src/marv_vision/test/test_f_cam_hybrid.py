"""Tests for hybrid OpenCV + YOLO detection merge."""

from marv_vision.lib.f_cam_data import merge_detections_by_class


def test_merge_detections_by_class_keeps_highest_confidence():
  merged = merge_detections_by_class([
      {'class_name': 'gate', 'confidence': 0.55},
      {'class_name': 'gate', 'confidence': 0.82},
      {'class_name': 'obstacle', 'confidence': 0.70},
      {'class_name': 'neon_orange', 'confidence': 0.60},
  ])
  by_name = {d['class_name']: d for d in merged}
  assert len(by_name) == 3
  assert by_name['gate']['confidence'] == 0.82
  assert by_name['obstacle']['confidence'] == 0.70
  assert by_name['neon_orange']['confidence'] == 0.60

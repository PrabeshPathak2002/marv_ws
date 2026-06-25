"""Unit tests for detection string format."""

from marv_vision.lib.detection_format import format_detection_string, parse_detection_string


def test_format_and_parse_includes_area():
  detections = [{
      'class_name': 'gate',
      'confidence': 0.85,
      'x': 0.42,
      'y': 0.55,
      'area': 0.1234,
  }]
  text = format_detection_string(detections)
  assert 'area:0.1234' in text
  parsed = parse_detection_string(text)
  assert len(parsed) == 1
  assert parsed[0]['area'] == 0.1234
  assert parsed[0]['x'] == 0.42

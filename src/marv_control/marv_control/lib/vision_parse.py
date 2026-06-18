"""Parse vision detection strings from marv_vision."""

from marv_vision.lib.detection_format import parse_detection_string


def best_detection(detections, class_names):
    """Return highest-confidence detection matching any of class_names."""
    matches = [
        d for d in detections
        if d.get('class_name', '').lower() in {n.lower() for n in class_names}
    ]
    if not matches:
        return None
    return max(matches, key=lambda d: d.get('confidence', 0.0))


def parse_vision_string(vision_data):
    """Parse f_cam/detections string into detection list."""
    return parse_detection_string(vision_data or '')

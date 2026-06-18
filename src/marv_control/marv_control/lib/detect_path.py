"""Path detection and following."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string

PATH_CLASSES = ('path',)
CONF_MIN = 0.35
SURGE_SPEED = 0.25


def detect_path(node, vision_data=None):
    """Follow a detected path marker — drive forward."""
    detections = parse_vision_string(vision_data)
    path = best_detection(detections, PATH_CLASSES)
    if path is None or path.get('confidence', 0.0) < CONF_MIN:
        return None

    x = path.get('x', 0.5)
    yaw = (0.5 - x) * 0.3
    node.get_logger().debug(f'detect_path: surge={SURGE_SPEED:.2f} yaw={yaw:.2f}')
    return {'surge': SURGE_SPEED, 'sway': 0.0, 'heave': 0.0, 'yaw': yaw}

"""Obstacle avoidance behavior."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string

OBSTACLE_CLASSES = ('obstacle',)
CONF_MIN = 0.4
SWAY_GAIN = 0.35


def avoid_obstacles(node, vision_data=None):
    """Sway away from a detected obstacle. Returns cmd dict or None."""
    detections = parse_vision_string(vision_data)
    obstacle = best_detection(detections, OBSTACLE_CLASSES)
    if obstacle is None or obstacle.get('confidence', 0.0) < CONF_MIN:
        return None

    x = obstacle.get('x', 0.5)
    sway = -SWAY_GAIN if x > 0.5 else SWAY_GAIN
    node.get_logger().debug(f'avoid_obstacles: sway={sway:.2f}')
    return {'surge': 0.0, 'sway': sway, 'heave': 0.0, 'yaw': 0.0}

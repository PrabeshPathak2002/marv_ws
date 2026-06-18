"""Obstacle avoidance behavior (vision + forward Ping1D)."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string

OBSTACLE_CLASSES = ('obstacle',)
CONF_MIN = 0.4
SWAY_GAIN = 0.35
DEFAULT_STOP_M = 0.8
DEFAULT_BACKUP_SURGE = -0.15


def avoid_obstacles(
    node,
    vision_data=None,
    forward_range_m=None,
    stop_m=DEFAULT_STOP_M,
):
  """Stop or sway away from obstacles using vision and/or forward Ping range."""
  if forward_range_m is not None and forward_range_m < stop_m:
    node.get_logger().debug(
        f'avoid_obstacles: ping stop range={forward_range_m:.2f} m')
    return {
        'surge': DEFAULT_BACKUP_SURGE,
        'sway': 0.0,
        'heave': 0.0,
        'yaw': 0.0,
    }

  detections = parse_vision_string(vision_data)
  obstacle = best_detection(detections, OBSTACLE_CLASSES)
  if obstacle is None or obstacle.get('confidence', 0.0) < CONF_MIN:
    return None

  x = obstacle.get('x', 0.5)
  sway = -SWAY_GAIN if x > 0.5 else SWAY_GAIN
  node.get_logger().debug(f'avoid_obstacles: sway={sway:.2f}')
  return {'surge': 0.0, 'sway': sway, 'heave': 0.0, 'yaw': 0.0}

"""Gate traversal behavior."""

from marv_control.lib.ping_helpers import scale_surge_by_range
from marv_control.lib.vision_parse import best_detection, parse_vision_string

GATE_CLASSES = ('gate',)
CONF_MIN = 0.35
CENTER_DEADBAND = 0.08
SURGE_APPROACH = 0.3
SWAY_KP = 0.45
YAW_KP = 0.2


def traverse_gate(node, vision_data=None, forward_range_m=None,
                  approach_slow_m=2.5, stop_m=0.6):
  """Align to gate center (x) and drive forward."""
  detections = parse_vision_string(vision_data)
  gate = best_detection(detections, GATE_CLASSES)
  if gate is None or gate.get('confidence', 0.0) < CONF_MIN:
    return None

  x = gate.get('x', 0.5)
  x_err = x - 0.5
  sway = 0.0
  yaw = 0.0
  if abs(x_err) > CENTER_DEADBAND:
    sway = -SWAY_KP * x_err
    yaw = -YAW_KP * x_err

  surge = scale_surge_by_range(
      SURGE_APPROACH, forward_range_m, approach_slow_m, stop_m)

  node.get_logger().debug(
      f'traverse_gate: x={x:.2f} surge={surge:.2f} sway={sway:.2f} '
      f'range={forward_range_m}')
  return {'surge': surge, 'sway': sway, 'heave': 0.0, 'yaw': yaw}

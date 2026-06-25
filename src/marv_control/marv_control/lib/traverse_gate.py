"""Gate traversal behavior."""

from marv_control.lib.ping_helpers import scale_surge_by_range
from marv_control.lib.vision_parse import best_detection, parse_vision_string

DEFAULT_GATE_CLASSES = ('gate',)
CONF_MIN = 0.35
CENTER_DEADBAND = 0.08
SURGE_APPROACH = 0.32
SWAY_KP = 0.45
YAW_KP = 0.26
GATE_MAX_YAW = 0.16


def traverse_gate(node, vision_data=None, forward_range_m=None,
                  approach_slow_m=2.5, stop_m=0.6,
                  gate_classes=DEFAULT_GATE_CLASSES,
                  conf_min=CONF_MIN,
                  center_deadband=CENTER_DEADBAND,
                  surge_approach=SURGE_APPROACH,
                  sway_kp=SWAY_KP,
                  yaw_kp=YAW_KP,
                  gate_max_yaw=GATE_MAX_YAW,
                  target_x_offset=0.0):
  """Align to gate center (x) and drive forward."""
  detections = parse_vision_string(vision_data)
  gate = best_detection(detections, gate_classes)
  if gate is None or gate.get('confidence', 0.0) < conf_min:
    return {'surge': 0.12, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.15}

  x = gate.get('x', 0.5)
  x_err = x - 0.5 - float(target_x_offset)
  sway = 0.0
  yaw = 0.0
  if abs(x_err) > center_deadband:
    sway = -sway_kp * x_err
    yaw = max(-gate_max_yaw, min(gate_max_yaw, -yaw_kp * x_err))

  surge = scale_surge_by_range(
      surge_approach, forward_range_m, approach_slow_m, stop_m)

  node.get_logger().debug(
      f'traverse_gate: x={x:.2f} err={x_err:.2f} area={gate.get("area", 0):.3f} '
      f'surge={surge:.2f} yaw={yaw:.2f} range={forward_range_m}')
  return {'surge': surge, 'sway': sway, 'heave': 0.0, 'yaw': yaw}


def gate_ready_to_commit(gate, commit_area=0.12, commit_deadband=0.30,
                         target_x_offset=0.0, conf_min=CONF_MIN):
  """Eagle-style commit when gate fills enough of the frame and is centered."""
  if gate is None or gate.get('confidence', 0.0) < conf_min:
    return False
  x_err = gate.get('x', 0.5) - 0.5 - float(target_x_offset)
  area = gate.get('area', 0.0)
  return area >= commit_area and abs(x_err) <= commit_deadband

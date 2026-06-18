"""Gate traversal behavior."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string

GATE_CLASSES = ('gate',)
CONF_MIN = 0.35
CENTER_DEADBAND = 0.08
SURGE_APPROACH = 0.3
SWAY_KP = 0.45
YAW_KP = 0.2


def traverse_gate(node, vision_data=None):
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

    node.get_logger().debug(
        f'traverse_gate: x={x:.2f} surge={SURGE_APPROACH:.2f} sway={sway:.2f}')
    return {'surge': SURGE_APPROACH, 'sway': sway, 'heave': 0.0, 'yaw': yaw}

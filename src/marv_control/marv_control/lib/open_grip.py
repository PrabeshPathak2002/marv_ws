"""Open gripper actuator command."""

GRIPPER_OPEN_PWM = 1900


def open_grip(node):
    """Request gripper open. Returns actuator dict for future MAVLink servo output."""
    node.get_logger().debug('open_grip requested')
    return {'actuator': 'gripper', 'pwm': GRIPPER_OPEN_PWM, 'state': 'open'}

"""Close gripper actuator command."""

GRIPPER_CLOSE_PWM = 1100


def close_grip(node):
    """Request gripper close. Returns actuator dict for future MAVLink servo output."""
    node.get_logger().debug('close_grip requested')
    return {'actuator': 'gripper', 'pwm': GRIPPER_CLOSE_PWM, 'state': 'close'}

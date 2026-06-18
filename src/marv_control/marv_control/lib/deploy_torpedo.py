"""Torpedo deployment behavior."""

TORPEDO_FIRE_PWM = 1900


def deploy_torpedo(node, target=None):
    """Request torpedo fire. Returns actuator dict for future servo output."""
    node.get_logger().debug('deploy_torpedo requested')
    return {
        'actuator': 'torpedo',
        'pwm': TORPEDO_FIRE_PWM,
        'state': 'fire',
        'target': target,
    }

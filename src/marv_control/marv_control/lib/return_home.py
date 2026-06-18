"""Return-to-home behavior."""

HOME_XY = (0.0, 0.0)
ARRIVE_RADIUS_M = 0.3
SPEED = 0.25


def return_home(node, position=None, home_xy=HOME_XY):
    """Navigate toward home using horizontal pose (x, y)."""
    if position is None:
        return None

    x = position.pose.pose.position.x
    y = position.pose.pose.position.y
    dx = home_xy[0] - x
    dy = home_xy[1] - y
    dist = (dx * dx + dy * dy) ** 0.5
    if dist < ARRIVE_RADIUS_M:
        return None

    surge = max(-SPEED, min(SPEED, SPEED * dx / dist))
    sway = max(-SPEED, min(SPEED, SPEED * dy / dist))
    node.get_logger().debug(f'return_home: dist={dist:.2f} surge={surge:.2f}')
    return {'surge': surge, 'sway': sway, 'heave': 0.0, 'yaw': 0.0}

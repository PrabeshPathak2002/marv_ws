"""Timed forward surge (pass through gate)."""

SURGE_SPEED = 0.35


def pass_forward(node, surge_speed=SURGE_SPEED):
  """Drive straight ahead at surge_speed."""
  return {'surge': surge_speed, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}

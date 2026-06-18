"""Forward Ping1D range helpers for motion behaviors."""


def scale_surge_by_range(surge, range_m, slow_start_m=2.5, stop_m=0.6):
  """Reduce forward speed as the sub approaches an obstacle/gate."""
  if range_m is None or range_m >= slow_start_m:
    return surge
  if range_m <= stop_m:
    return 0.0
  scale = (range_m - stop_m) / max(slow_start_m - stop_m, 0.01)
  return surge * max(0.0, min(1.0, scale))


def is_gate_cleared(range_m, gate_clear_m, min_elapsed_s, elapsed_s):
  """True when Ping shows open water ahead after gate approach."""
  if range_m is None:
    return False
  return elapsed_s >= min_elapsed_s and range_m >= gate_clear_m

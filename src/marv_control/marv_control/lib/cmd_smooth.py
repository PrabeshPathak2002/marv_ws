"""Rate-limit motion commands (Eagle mission_manager.command_smooth)."""


def limit_command_step(current, target, max_step):
  delta = float(target) - float(current)
  if abs(delta) <= max_step:
    return float(target)
  return float(current) + max_step if delta > 0 else float(current) - max_step


def smooth_command(last_cmd, new_cmd, max_step=0.035):
  """Blend toward new_cmd with per-axis step limits."""
  last = last_cmd or {}
  new = new_cmd or {}
  keys = ('surge', 'sway', 'heave', 'yaw')
  return {
      key: limit_command_step(last.get(key, 0.0), new.get(key, 0.0), max_step)
      for key in keys
  }

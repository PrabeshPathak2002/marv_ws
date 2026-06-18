"""Unit tests for command smoothing."""

from marv_control.lib.cmd_smooth import limit_command_step, smooth_command


def test_limit_command_step_clamps_delta():
  assert limit_command_step(0.0, 1.0, 0.035) == 0.035
  assert limit_command_step(0.5, 0.52, 0.035) == 0.52


def test_smooth_command_applies_per_axis():
  last = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
  new = {'surge': 0.5, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
  out = smooth_command(last, new, max_step=0.1)
  assert out['surge'] == 0.1

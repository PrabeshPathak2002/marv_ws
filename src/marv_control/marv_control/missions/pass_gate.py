"""Surge forward through the gate after alignment."""

from marv_control.lib.pass_forward import pass_forward
from marv_control.lib.ping_helpers import is_gate_cleared, scale_surge_by_range
from marv_control.missions.base import Mission, MissionContext, MissionResult


class PassGateMission(Mission):
  name = 'pass_gate'
  behavior_key = 'pass_gate'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._surge_speed = float(config.get('surge_speed', 0.35))
    self._duration_s = float(config.get('duration_s', 6.0))
    self._gate_clear_m = float(config.get('gate_clear_m', 2.5))
    self._approach_slow_m = float(config.get('approach_slow_m', 2.5))
    self._stop_m = float(config.get('stop_m', 0.6))
    self._use_ping_complete = bool(config.get('use_ping_complete', True))

  def step(self, ctx: MissionContext) -> MissionResult:
    range_m = ctx.extras.get('forward_range_m')
    surge = scale_surge_by_range(
        self._surge_speed, range_m, self._approach_slow_m, self._stop_m)
    cmd = pass_forward(self._node, surge_speed=surge)

    if self._use_ping_complete and is_gate_cleared(
        range_m, self._gate_clear_m, min_elapsed_s=1.0, elapsed_s=ctx.elapsed_s):
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message=f'gate cleared (ping {range_m:.2f} m)',
      )

    if ctx.elapsed_s >= self._duration_s:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message='gate pass surge complete (timeout)',
      )
    return MissionResult(cmd=cmd)

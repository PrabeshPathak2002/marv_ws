"""Wait submerged at depth before starting pre-qual run."""

from marv_control.missions.base import Mission, MissionContext, MissionResult


class WaitSubmergedMission(Mission):
  name = 'wait_submerged'
  behavior_key = 'wait_submerged'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._duration_s = float(config.get('duration_s', 3.0))

  def step(self, ctx: MissionContext) -> MissionResult:
    if ctx.elapsed_s >= self._duration_s:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message='submerged and ready',
      )
    return MissionResult(cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0})

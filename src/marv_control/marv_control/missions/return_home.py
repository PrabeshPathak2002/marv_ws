"""Return-to-home mission."""

from marv_control.lib.return_home import return_home
from marv_control.missions.base import Mission, MissionContext, MissionResult


class ReturnHomeMission(Mission):
  name = 'return_home'
  behavior_key = 'return_home'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    home = config.get('home_xy', [0.0, 0.0])
    self._home_xy = (float(home[0]), float(home[1]))
    self._arrive_radius_m = float(config.get('arrive_radius_m', 0.3))

  def step(self, ctx: MissionContext) -> MissionResult:
    if ctx.pose is None:
      return MissionResult()

    cmd = return_home(self._node, ctx.pose, home_xy=self._home_xy)
    if cmd is None:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message='arrived at home',
      )

    return MissionResult(cmd=cmd)

  def cleanup(self):
    super().cleanup()
    self._node.get_logger().info('return_home mission cleanup')

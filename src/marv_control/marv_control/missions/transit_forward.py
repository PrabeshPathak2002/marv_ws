"""Dead-reckoning transit toward the marker using pose delta."""

from marv_control.lib.pass_forward import pass_forward
from marv_control.lib.pose_utils import horizontal_distance
from marv_control.missions.base import Mission, MissionContext, MissionResult


class TransitForwardMission(Mission):
  name = 'transit_forward'
  behavior_key = 'transit_forward'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._target_distance_m = float(config.get('target_distance_m', 10.0))
    self._surge_speed = float(config.get('surge_speed', 0.3))
    self._start_pose = None

  def step(self, ctx: MissionContext) -> MissionResult:
    if ctx.pose is None:
      return MissionResult(cmd=pass_forward(self._node, surge_speed=self._surge_speed))

    if self._start_pose is None:
      self._start_pose = ctx.pose

    traveled = horizontal_distance(self._start_pose, ctx.pose) or 0.0
    cmd = pass_forward(self._node, surge_speed=self._surge_speed)

    if traveled >= self._target_distance_m:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message=f'transit complete ({traveled:.1f} m)',
      )

    return MissionResult(cmd=cmd)

  def cleanup(self):
    super().cleanup()
    self._start_pose = None

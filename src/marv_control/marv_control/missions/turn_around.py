"""Turn in place toward the return gate heading."""

from marv_control.lib.pose_utils import normalize_angle, yaw_from_pose
from marv_control.missions.base import Mission, MissionContext, MissionResult


class TurnAroundMission(Mission):
  name = 'turn_around'
  behavior_key = 'turn_around'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._target_delta_rad = float(config.get('target_delta_rad', 3.14159))
    self._yaw_rate = float(config.get('yaw_rate', 0.3))
    self._tolerance_rad = float(config.get('tolerance_rad', 0.25))
    self._start_yaw = None

  def step(self, ctx: MissionContext) -> MissionResult:
    yaw = yaw_from_pose(ctx.pose)
    if yaw is None:
      return MissionResult(cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': self._yaw_rate})

    if self._start_yaw is None:
      self._start_yaw = yaw

    turned = abs(normalize_angle(yaw - self._start_yaw))
    if turned >= self._target_delta_rad - self._tolerance_rad:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message=f'turned {turned:.2f} rad',
      )

    return MissionResult(cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': self._yaw_rate})

  def cleanup(self):
    super().cleanup()
    self._start_yaw = None

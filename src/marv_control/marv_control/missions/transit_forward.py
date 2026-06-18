"""Timed transit toward marker with vision-based early exit (Eagle TRANSIT_TO_MARKER)."""

from marv_control.lib.pass_forward import pass_forward
from marv_control.lib.pose_utils import horizontal_distance
from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


class TransitForwardMission(Mission):
  name = 'transit_forward'
  behavior_key = 'transit_forward'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._target_distance_m = float(config.get('target_distance_m', 10.0))
    self._surge_speed = float(config.get('surge_speed', 0.42))
    self._min_transit_s = float(config.get('min_transit_s', 6.0))
    self._max_transit_s = float(config.get('max_transit_s', 20.0))
    self._marker_classes = tuple(
        config.get('marker_classes', ('yellow_pole', 'circle', 'Circle', 'cross')))
    self._conf_min = float(config.get('conf_min', 0.25))
    self._use_timed_transit = bool(config.get('use_timed_transit', True))
    self._start_pose = None

  def _marker_visible(self, ctx):
    detections = parse_vision_string(ctx.vision_data)
    marker = best_detection(detections, self._marker_classes)
    return marker is not None and marker.get('confidence', 0.0) >= self._conf_min

  def step(self, ctx: MissionContext) -> MissionResult:
    cmd = pass_forward(self._node, surge_speed=self._surge_speed)
    stop = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}

    if self._use_timed_transit:
      if self._marker_visible(ctx) and ctx.elapsed_s >= self._min_transit_s:
        return MissionResult(
            cmd=stop,
            complete=True,
            success=True,
            message='marker spotted during transit',
        )
      if ctx.elapsed_s >= self._max_transit_s:
        return MissionResult(
            cmd=stop,
            complete=True,
            success=False,
            message='transit timeout without marker',
        )
      return MissionResult(cmd=cmd)

    if ctx.pose is None:
      return MissionResult(cmd=cmd)

    if self._start_pose is None:
      self._start_pose = ctx.pose

    traveled = horizontal_distance(self._start_pose, ctx.pose) or 0.0
    if traveled >= self._target_distance_m:
      return MissionResult(
          cmd=stop,
          complete=True,
          success=True,
          message=f'transit complete ({traveled:.1f} m)',
      )

    return MissionResult(cmd=cmd)

  def cleanup(self):
    super().cleanup()
    self._start_pose = None

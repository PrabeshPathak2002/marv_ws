"""Circle the vertical marker (vision-centered orbit or timed yaw)."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


class CircleMarkerMission(Mission):
  name = 'circle_marker'
  behavior_key = 'circle_marker'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._marker_classes = tuple(
        config.get('marker_classes', ('circle', 'Circle', 'cross')))
    self._conf_min = float(config.get('conf_min', 0.30))
    self._yaw_rate = float(config.get('yaw_rate', 0.25))
    self._surge_speed = float(config.get('surge_speed', 0.15))
    self._orbit_duration_s = float(config.get('orbit_duration_s', 45.0))
    self._sway_kp = float(config.get('sway_kp', 0.4))

  def step(self, ctx: MissionContext) -> MissionResult:
    detections = parse_vision_string(ctx.vision_data)
    marker = best_detection(detections, self._marker_classes)

    sway = 0.0
    if marker is not None and marker.get('confidence', 0.0) >= self._conf_min:
      x_err = marker.get('x', 0.5) - 0.5
      sway = -self._sway_kp * x_err

    cmd = {
        'surge': self._surge_speed,
        'sway': sway,
        'heave': 0.0,
        'yaw': self._yaw_rate,
    }

    if ctx.elapsed_s >= self._orbit_duration_s:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message='orbit complete',
      )

    return MissionResult(cmd=cmd)

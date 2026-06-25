"""Inverted-U orbit around the vertical marker (Eagle ORBIT_MARKER)."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


def _clamp(value, lo, hi):
  return max(lo, min(hi, value))


class CircleMarkerMission(Mission):
  name = 'circle_marker'
  behavior_key = 'circle_marker'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._marker_classes = tuple(
        config.get('marker_classes', ('obstacle', 'yellow_pole', 'circle', 'Circle', 'cross')))
    self._conf_min = float(config.get('conf_min', 0.30))
    self._orbit_duration_s = float(config.get('orbit_duration_s', 24.0))
    self._side_step_duration_s = float(config.get('side_step_duration_s', 5.0))
    self._side_pass_duration_s = float(config.get('side_pass_duration_s', 7.0))
    self._cross_behind_duration_s = float(config.get('cross_behind_duration_s', 7.0))
    self._u_sway_speed = float(config.get('u_sway_speed', -0.32))
    self._u_cross_sway_speed = float(config.get('u_cross_sway_speed', 0.36))
    self._u_forward_speed = float(config.get('u_forward_speed', 0.26))
    self._search_yaw = float(config.get('search_yaw', 0.12))
    self._yaw_kp = float(config.get('yaw_kp', 0.55))
    self._max_yaw = float(config.get('max_yaw', 0.28))

  def _marker_yaw(self, marker):
    if marker is None:
      return self._search_yaw
    x_err = marker.get('x', 0.5) - 0.5
    return _clamp(-self._yaw_kp * x_err, -self._max_yaw, self._max_yaw)

  def step(self, ctx: MissionContext) -> MissionResult:
    if ctx.elapsed_s >= self._orbit_duration_s:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message='inverted-U orbit complete',
      )

    detections = parse_vision_string(ctx.vision_data)
    marker = best_detection(detections, self._marker_classes)
    yaw = self._marker_yaw(
        marker if marker and marker.get('confidence', 0.0) >= self._conf_min else None)

    elapsed = ctx.elapsed_s
    if elapsed < self._side_step_duration_s:
      cmd = {'surge': 0.0, 'sway': self._u_sway_speed, 'heave': 0.0, 'yaw': yaw}
    elif elapsed < self._side_step_duration_s + self._side_pass_duration_s:
      cmd = {
          'surge': self._u_forward_speed,
          'sway': self._u_sway_speed * 0.25,
          'heave': 0.0,
          'yaw': yaw,
      }
    elif elapsed < (
        self._side_step_duration_s + self._side_pass_duration_s + self._cross_behind_duration_s):
      cmd = {
          'surge': self._u_forward_speed * 0.45,
          'sway': self._u_cross_sway_speed,
          'heave': 0.0,
          'yaw': yaw,
      }
    else:
      cmd = {
          'surge': self._u_forward_speed * 0.5,
          'sway': 0.0,
          'heave': 0.0,
          'yaw': yaw,
      }

    return MissionResult(cmd=cmd)

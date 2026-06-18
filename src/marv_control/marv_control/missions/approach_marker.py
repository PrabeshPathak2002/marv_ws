"""Center on marker and close distance using bbox area (Eagle approach_marker)."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


def _clamp(value, lo, hi):
  return max(lo, min(hi, value))


class ApproachMarkerMission(Mission):
  name = 'approach_marker'
  behavior_key = 'approach_marker'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._marker_classes = tuple(
        config.get('marker_classes', ('yellow_pole', 'circle', 'Circle', 'cross')))
    self._conf_min = float(config.get('conf_min', 0.25))
    self._center_deadband = float(config.get('center_deadband', 0.12))
    self._close_area = float(config.get('close_area', 0.055))
    self._area_kp = float(config.get('area_kp', 9.0))
    self._max_surge = float(config.get('max_surge', 0.25))
    self._min_surge = float(config.get('min_surge', 0.08))
    self._yaw_kp = float(config.get('yaw_kp', 0.55))
    self._max_yaw = float(config.get('max_yaw', 0.28))
    self._search_yaw = float(config.get('search_yaw', 0.12))
    self._forward_surge = float(config.get('forward_surge', 0.22))

  def step(self, ctx: MissionContext) -> MissionResult:
    detections = parse_vision_string(ctx.vision_data)
    marker = best_detection(detections, self._marker_classes)

    if marker is None or marker.get('confidence', 0.0) < self._conf_min:
      return MissionResult(cmd={
          'surge': self._forward_surge,
          'sway': 0.0,
          'heave': 0.0,
          'yaw': self._search_yaw,
      })

    x_err = marker.get('x', 0.5) - 0.5
    area = marker.get('area', 0.0)
    yaw = _clamp(-self._yaw_kp * x_err, -self._max_yaw, self._max_yaw)

    if area >= self._close_area and abs(x_err) <= self._center_deadband:
      return MissionResult(
          cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0},
          complete=True,
          success=True,
          message=f'marker close (area={area:.3f})',
      )

    if abs(x_err) > self._center_deadband:
      return MissionResult(cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': yaw})

    area_error = self._close_area - area
    surge = _clamp(self._area_kp * area_error, self._min_surge, self._max_surge)
    return MissionResult(cmd={'surge': surge, 'sway': 0.0, 'heave': 0.0, 'yaw': yaw})

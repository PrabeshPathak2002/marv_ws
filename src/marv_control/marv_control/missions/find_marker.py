"""Creep forward while searching for the yellow marker."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult

_HOLD = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}


class FindMarkerMission(Mission):
  name = 'find_marker'
  behavior_key = 'find_marker'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._marker_classes = tuple(
        config.get('marker_classes', ('yellow_pole', 'circle', 'Circle', 'cross')))
    self._conf_min = float(config.get('conf_min', 0.25))
    self._search_yaw = float(config.get('search_yaw', 0.12))
    self._forward_surge = float(config.get('forward_surge', 0.22))

  def step(self, ctx: MissionContext) -> MissionResult:
    detections = parse_vision_string(ctx.vision_data)
    marker = best_detection(detections, self._marker_classes)
    if marker is not None and marker.get('confidence', 0.0) >= self._conf_min:
      return MissionResult(
          cmd=_HOLD,
          complete=True,
          success=True,
          message='marker found',
      )

    cmd = {
        'surge': self._forward_surge,
        'sway': 0.0,
        'heave': 0.0,
        'yaw': self._search_yaw,
    }
    return MissionResult(cmd=cmd)

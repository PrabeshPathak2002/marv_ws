"""Search for the gate with yaw (and optional forward creep)."""

from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult

_HOLD = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}


class FindGateMission(Mission):
  name = 'find_gate'
  behavior_key = 'find_gate'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._gate_classes = tuple(config.get('gate_classes', ('gate',)))
    self._conf_min = float(config.get('conf_min', 0.20))
    self._search_yaw = float(config.get('search_yaw', 0.12))
    self._forward_surge = float(config.get('forward_surge', 0.0))

  def step(self, ctx: MissionContext) -> MissionResult:
    detections = parse_vision_string(ctx.vision_data)
    gate = best_detection(detections, self._gate_classes)
    if gate is not None and gate.get('confidence', 0.0) >= self._conf_min:
      return MissionResult(
          cmd=_HOLD,
          complete=True,
          success=True,
          message='gate found',
      )

    cmd = {'surge': self._forward_surge, 'sway': 0.0, 'heave': 0.0, 'yaw': self._search_yaw}
    return MissionResult(cmd=cmd)

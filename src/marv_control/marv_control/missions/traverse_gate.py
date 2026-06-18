"""Gate traversal mission."""

from marv_control.lib.traverse_gate import traverse_gate
from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


class TraverseGateMission(Mission):
  name = 'traverse_gate'
  behavior_key = 'traverse_gate'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._gate_classes = tuple(config.get('gate_classes', ('gate',)))
    self._conf_min = float(config.get('conf_min', 0.35))
    self._center_deadband = float(config.get('center_deadband', 0.08))
    self._aligned_frames_required = int(config.get('aligned_frames_required', 15))
    self._approach_slow_m = float(config.get('approach_slow_m', 2.5))
    self._stop_m = float(config.get('stop_m', 0.6))

  def step(self, ctx: MissionContext) -> MissionResult:
    range_m = ctx.extras.get('forward_range_m')
    cmd = traverse_gate(
        self._node, ctx.vision_data, forward_range_m=range_m,
        approach_slow_m=self._approach_slow_m, stop_m=self._stop_m)
    detections = parse_vision_string(ctx.vision_data)
    gate = best_detection(detections, self._gate_classes)

    if gate is not None and gate.get('confidence', 0.0) >= self._conf_min:
      x_err = abs(gate.get('x', 0.5) - 0.5)
      if x_err <= self._center_deadband:
        self._aligned_frames += 1
      else:
        self._aligned_frames = 0
    else:
      self._aligned_frames = 0

    if self._aligned_frames >= self._aligned_frames_required:
      return MissionResult(
          cmd=cmd,
          complete=True,
          success=True,
          message='gate aligned',
      )

    return MissionResult(cmd=cmd)

  def cleanup(self):
    super().cleanup()
    self._node.get_logger().info('traverse_gate mission cleanup')

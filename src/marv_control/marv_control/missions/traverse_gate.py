"""Gate traversal mission."""

from marv_control.lib.traverse_gate import gate_ready_to_commit, traverse_gate
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
    self._commit_area = float(config.get('commit_area', 0.12))
    self._commit_deadband = float(config.get('commit_deadband', 0.30))
    self._target_x_offset = float(config.get('target_x_offset', 0.0))
    self._aligned_frames_required = int(config.get('aligned_frames_required', 0))
    self._approach_slow_m = float(config.get('approach_slow_m', 2.5))
    self._stop_m = float(config.get('stop_m', 0.6))
    self._surge_approach = float(config.get('surge_approach', 0.32))
    self._yaw_kp = float(config.get('yaw_kp', 0.26))
    self._gate_max_yaw = float(config.get('gate_max_yaw', 0.16))

  def step(self, ctx: MissionContext) -> MissionResult:
    range_m = ctx.extras.get('forward_range_m')
    cmd = traverse_gate(
        self._node, ctx.vision_data, forward_range_m=range_m,
        approach_slow_m=self._approach_slow_m, stop_m=self._stop_m,
        gate_classes=self._gate_classes,
        conf_min=self._conf_min,
        center_deadband=self._center_deadband,
        surge_approach=self._surge_approach,
        yaw_kp=self._yaw_kp,
        gate_max_yaw=self._gate_max_yaw,
        target_x_offset=self._target_x_offset)
    detections = parse_vision_string(ctx.vision_data)
    gate = best_detection(detections, self._gate_classes)

    if gate_ready_to_commit(
        gate,
        commit_area=self._commit_area,
        commit_deadband=self._commit_deadband,
        target_x_offset=self._target_x_offset,
        conf_min=self._conf_min,
    ):
      return MissionResult(
          cmd=cmd,
          complete=True,
          success=True,
          message='gate ready to commit',
      )

    if self._aligned_frames_required > 0 and gate is not None:
      if gate.get('confidence', 0.0) >= self._conf_min:
        x_err = abs(gate.get('x', 0.5) - 0.5 - self._target_x_offset)
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

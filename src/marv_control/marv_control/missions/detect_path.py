"""Path following mission."""

from marv_control.lib.detect_path import detect_path
from marv_control.lib.vision_parse import best_detection, parse_vision_string
from marv_control.missions.base import Mission, MissionContext, MissionResult


class DetectPathMission(Mission):
  name = 'detect_path'
  behavior_key = 'detect_path'

  def __init__(self, node, **config):
    super().__init__(node, **config)
    self._path_classes = tuple(config.get('path_classes', ('path',)))
    self._conf_min = float(config.get('conf_min', 0.35))
    self._lost_frames_limit = int(config.get('lost_frames_limit', 30))
    self._min_runtime_s = float(config.get('min_runtime_s', 5.0))
    self._lost_frames = 0

  def step(self, ctx: MissionContext) -> MissionResult:
    cmd = detect_path(self._node, ctx.vision_data)
    detections = parse_vision_string(ctx.vision_data)
    path = best_detection(detections, self._path_classes)

    if path is None or path.get('confidence', 0.0) < self._conf_min:
      self._lost_frames += 1
    else:
      self._lost_frames = 0

    if (ctx.elapsed_s >= self._min_runtime_s and
        self._lost_frames >= self._lost_frames_limit):
      return MissionResult(
          cmd=cmd,
          complete=True,
          success=True,
          message='path segment complete (marker lost)',
      )

    return MissionResult(cmd=cmd)

  def cleanup(self):
    super().cleanup()
    self._lost_frames = 0
    self._node.get_logger().info('detect_path mission cleanup')

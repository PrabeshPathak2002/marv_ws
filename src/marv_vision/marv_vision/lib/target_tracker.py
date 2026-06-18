"""Exponential smoothing for vision detections (Eagle target_localizer pattern)."""


class DetectionTracker:
  """Smooth x, y, area, and confidence per class name."""

  def __init__(self, alpha=0.35):
    self._alpha = float(alpha)
    self._state = {}

  def smooth(self, detection):
    if detection is None:
      return None
    key = detection.get('class_name', '?')
    prev = self._state.get(key)
    if prev is None:
      self._state[key] = dict(detection)
      return detection

    smoothed = dict(detection)
    blend = self._alpha
    for field in ('x', 'y', 'area', 'confidence'):
      if field in detection and field in prev:
        smoothed[field] = blend * float(detection[field]) + (1.0 - blend) * float(prev[field])
    self._state[key] = smoothed
    return smoothed

  def smooth_all(self, detections):
    return [self.smooth(det) for det in detections]

  def reset(self):
    self._state.clear()

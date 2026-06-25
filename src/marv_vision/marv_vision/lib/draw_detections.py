"""Draw detection bounding boxes on a BGR frame."""

import cv2

_CLASS_COLORS = {
    'black_gate': (0, 255, 0),
    'gate': (0, 0, 255),
    'obstacle': (0, 140, 255),
    'neon_orange': (0, 140, 255),
    'yellow_pole': (0, 255, 255),
}
_PILLAR_COLORS = {
    'left': (255, 120, 0),
    'right': (0, 120, 255),
}


def draw_detections(frame, detections):
  """Return a copy of frame with xyxy boxes and labels drawn."""
  if frame is None:
    return None

  annotated = frame.copy()
  for det in detections:
    pillars = det.get('pillars')
    if pillars:
      for side, pillar in pillars.items():
        xyxy = pillar.get('xyxy')
        if not xyxy:
          continue
        x1, y1, x2, y2 = [int(round(v)) for v in xyxy]
        color = _PILLAR_COLORS.get(side, (200, 200, 200))
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated, side, (x1, max(y1 - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    xyxy = det.get('xyxy')
    if not xyxy:
      continue
    x1, y1, x2, y2 = [int(round(v)) for v in xyxy]
    x1 = max(0, min(x1, annotated.shape[1] - 1))
    x2 = max(0, min(x2, annotated.shape[1] - 1))
    y1 = max(0, min(y1, annotated.shape[0] - 1))
    y2 = max(0, min(y2, annotated.shape[0] - 1))
    if x2 <= x1 or y2 <= y1:
      continue
    name = det.get('class_name', 'obj')
    conf = det.get('confidence', 0.0)
    color = _CLASS_COLORS.get(name, (255, 255, 255))
    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
    label = f'{name}:{conf:.2f}'
    cv2.putText(
        annotated, label, (x1, max(y1 - 8, 12)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
    if 'x' in det and 'y' in det:
      cx = int(float(det['x']) * annotated.shape[1])
      cy = int(float(det['y']) * annotated.shape[0])
      cv2.circle(annotated, (cx, cy), 5, color, -1)
  return annotated

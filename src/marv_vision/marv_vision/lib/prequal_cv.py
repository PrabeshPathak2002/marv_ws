"""OpenCV detectors for pre-qual: black gate + yellow pole.

Publishes the same detection dict format as YOLO for f_cam/detections compatibility.
"""

from pathlib import Path

import cv2
import numpy as np
import yaml

DEFAULT_CONFIG = {
    'yellow_h_low': 18,
    'yellow_h_high': 42,
    'yellow_s_min': 80,
    'yellow_v_min': 80,
    'yellow_min_height_frac': 0.12,
    'yellow_min_aspect': 1.4,
    'gate_v_max': 70,
    'gate_s_max': 120,
    'gate_min_width_frac': 0.20,
    'gate_max_height_frac': 0.45,
    'gate_roi_top_frac': 0.15,
    'min_confidence': 0.30,
}


def load_prequal_cv_config(config_path=None):
  """Load HSV tuning from YAML; fall back to defaults."""
  cfg = dict(DEFAULT_CONFIG)
  if not config_path:
    return cfg
  path = Path(config_path)
  if not path.is_file():
    return cfg
  with path.open(encoding='utf-8') as handle:
    data = yaml.safe_load(handle) or {}
  section = data.get('prequal_cv', data)
  cfg.update({k: section[k] for k in cfg if k in section})
  return cfg


def _bbox_confidence(mask, x1, y1, x2, y2):
  """Fraction of bbox pixels set in binary mask."""
  roi = mask[y1:y2, x1:x2]
  if roi.size == 0:
    return 0.0
  return float(np.count_nonzero(roi)) / float(roi.size)


def detect_yellow_pole(frame, cfg):
  """Find tallest yellow blob (vertical pole)."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  lower = np.array([cfg['yellow_h_low'], cfg['yellow_s_min'], cfg['yellow_v_min']])
  upper = np.array([cfg['yellow_h_high'], 255, 255])
  mask = cv2.inRange(hsv, lower, upper)

  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
  mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

  contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  min_h = h * cfg['yellow_min_height_frac']
  best_box = None
  best_score = 0.0

  for cnt in contours:
    x, y, bw, bh = cv2.boundingRect(cnt)
    if bh < min_h or bw < 4:
      continue
    aspect = bh / max(bw, 1)
    if aspect < cfg['yellow_min_aspect']:
      continue
    score = bh * aspect
    if score > best_score:
      best_score = score
      best_box = (x, y, x + bw, y + bh)

  if best_box is None:
    return None

  x1, y1, x2, y2 = best_box
  conf = _bbox_confidence(mask, x1, y1, x2, y2)
  if conf < cfg['min_confidence']:
    return None

  return {
      'class_name': 'yellow_pole',
      'confidence': min(0.99, conf),
      'xyxy': [float(x1), float(y1), float(x2), float(y2)],
  }


def detect_black_gate(frame, cfg):
  """Find wide dark region (gate opening) in lower ROI."""
  h, w = frame.shape[:2]
  y0 = int(h * cfg['gate_roi_top_frac'])
  roi = frame[y0:, :]
  rh = roi.shape[0]

  hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
  mask = cv2.inRange(
      hsv,
      np.array([0, 0, 0]),
      np.array([180, cfg['gate_s_max'], cfg['gate_v_max']]),
  )

  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
  mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

  contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  min_w = w * cfg['gate_min_width_frac']
  max_h = rh * cfg['gate_max_height_frac']
  best_box = None
  best_score = 0.0

  for cnt in contours:
    x, y, bw, bh = cv2.boundingRect(cnt)
    if bw < min_w or bh > max_h or bh < 8:
      continue
    aspect = bw / max(bh, 1)
    if aspect < 1.2:
      continue
    score = bw * aspect
    if score > best_score:
      best_score = score
      best_box = (x, y + y0, x + bw, y + bh + y0)

  if best_box is None:
    return None

  x1, y1, x2, y2 = best_box
  conf = _bbox_confidence(mask, x1, y1 - y0, x2, y2 - y0)
  if conf < cfg['min_confidence']:
    return None

  return {
      'class_name': 'black_gate',
      'confidence': min(0.99, conf),
      'xyxy': [float(x1), float(y1), float(x2), float(y2)],
  }


def process_prequal_cv(frame, config_path=None, min_confidence=None):
  """Run OpenCV pre-qual detectors. Returns list of detection dicts."""
  if frame is None:
    return []

  cfg = load_prequal_cv_config(config_path)
  if min_confidence is not None:
    cfg['min_confidence'] = float(min_confidence)

  detections = []
  gate = detect_black_gate(frame, cfg)
  if gate is not None:
    detections.append(gate)
  pole = detect_yellow_pole(frame, cfg)
  if pole is not None:
    detections.append(pole)
  return detections

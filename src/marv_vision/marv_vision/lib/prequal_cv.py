"""OpenCV pre-qual detectors (EagleAUV ros2_ws patterns).

Gate: competition red/black panel pair OR black full bar OR black leg pair.
Marker: yellow pole.
"""

from pathlib import Path

import cv2
import numpy as np
import yaml

DEFAULT_CONFIG = {
    'yellow_h_low': 18,
    'yellow_h_high': 38,
    'yellow_s_min': 70,
    'yellow_v_min': 80,
    'yellow_min_height_frac': 0.12,
    'yellow_min_aspect': 1.4,
    'gate_v_max': 95,
    'gate_s_max': 255,
    'gate_roi_top_frac': 0.0,
    'red_h_low1': 0,
    'red_h_high1': 12,
    'red_h_low2': 168,
    'red_h_high2': 180,
    'red_s_min': 70,
    'red_v_min': 60,
    'leg_min_height_px': 25,
    'leg_min_width_frac': 0.12,
    'leg_min_aspect': 1.5,
    'full_min_width_frac': 0.12,
    'full_min_aspect': 0.45,
    'pair_min_separation_frac': 0.16,
    'task1_pair_min_separation_frac': 0.18,
    'pair_height_ratio_min': 0.50,
    'pair_vertical_delta_frac': 0.45,
    'pair_min_width_height_ratio': 0.60,
    'min_confidence': 0.20,
}


def load_prequal_cv_config(config_path=None):
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
  roi = mask[y1:y2, x1:x2]
  if roi.size == 0:
    return 0.0
  return float(np.count_nonzero(roi)) / float(roi.size)


def _box_to_xyxy(box):
  return [
      float(box['x']),
      float(box['y']),
      float(box['x'] + box['width']),
      float(box['y'] + box['height']),
  ]


def _gate_detection_from_target(target, frame_w, frame_h, class_name):
  boxes = target['boxes']
  x1 = min(b['x'] for b in boxes)
  y1 = min(b['y'] for b in boxes)
  x2 = max(b['x'] + b['width'] for b in boxes)
  y2 = max(b['y'] + b['height'] for b in boxes)
  area_norm = float(target['area']) / float(frame_w * frame_h)
  conf = min(0.99, area_norm * 4.0)
  conf = max(conf, 0.20)
  cx = target['center_x']
  cy = target['center_y']
  return {
      'class_name': class_name,
      'confidence': conf,
      'xyxy': [float(x1), float(y1), float(x2), float(y2)],
      'x': cx / max(frame_w, 1.0),
      'y': cy / max(frame_h, 1.0),
      'area': area_norm,
      'source': target.get('source', ''),
      'pillars': {
          'left': {
              'side': 'left',
              'xyxy': _box_to_xyxy(boxes[0]),
          },
          'right': {
              'side': 'right',
              'xyxy': _box_to_xyxy(boxes[1 if len(boxes) > 1 else 0]),
          },
      } if len(boxes) >= 2 else {},
  }


def _black_mask(hsv, cfg):
  return cv2.inRange(
      hsv,
      np.array([0, 0, 0]),
      np.array([180, cfg['gate_s_max'], cfg['gate_v_max']]),
  )


def _red_mask(hsv, cfg):
  low = cv2.inRange(
      hsv,
      np.array([cfg['red_h_low1'], cfg['red_s_min'], cfg['red_v_min']]),
      np.array([cfg['red_h_high1'], 255, 255]),
  )
  high = cv2.inRange(
      hsv,
      np.array([cfg['red_h_low2'], cfg['red_s_min'], cfg['red_v_min']]),
      np.array([cfg['red_h_high2'], 255, 255]),
  )
  return cv2.bitwise_or(low, high)


def _morph_mask(mask):
  kernel = np.ones((5, 5), np.uint8)
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
  return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def _contour_boxes(mask, width, cfg, min_area=80.0):
  contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  boxes = []
  for contour in contours:
    area_px = cv2.contourArea(contour)
    if area_px < min_area:
      continue
    x, y, bw, bh = cv2.boundingRect(contour)
    boxes.append({
        'area': area_px,
        'x': x,
        'y': y,
        'width': bw,
        'height': bh,
        'center_x': x + bw / 2.0,
        'center_y': y + bh / 2.0,
    })
  return boxes


def _cluster_vertical_panels(candidates, image_width):
  clusters = []
  max_center_delta = max(12.0, image_width * 0.04)
  for candidate in sorted(candidates, key=lambda item: item['center_x']):
    match = None
    for cluster in clusters:
      if abs(candidate['center_x'] - cluster['center_x']) <= max_center_delta:
        match = cluster
        break
    if match is None:
      clusters.append(candidate.copy())
      continue
    x_min = min(match['x'], candidate['x'])
    y_min = min(match['y'], candidate['y'])
    x_max = max(match['x'] + match['width'], candidate['x'] + candidate['width'])
    y_max = max(match['y'] + match['height'], candidate['y'] + candidate['height'])
    match['area'] += candidate['area']
    match['x'] = x_min
    match['y'] = y_min
    match['width'] = x_max - x_min
    match['height'] = y_max - y_min
    match['center_x'] = x_min + match['width'] / 2.0
    match['center_y'] = y_min + match['height'] / 2.0
  return [
      c for c in clusters
      if c['height'] >= 25 and c['height'] > c['width'] * 1.2
  ]


def _select_outer_panel_pair(clusters, image_width, min_sep_frac):
  if len(clusters) < 2:
    return None
  best_pair = None
  best_sep = 0.0
  for left in clusters:
    for right in clusters:
      if left is right or left['center_x'] >= right['center_x']:
        continue
      separation = right['center_x'] - left['center_x']
      if separation < image_width * min_sep_frac:
        continue
      if separation > best_sep:
        best_sep = separation
        best_pair = (left, right)
  if best_pair is None:
    return None
  left, right = best_pair
  return {
      'area': left['area'] + right['area'],
      'center_x': (left['center_x'] + right['center_x']) / 2.0,
      'center_y': (min(left['y'], right['y']) + max(
          left['y'] + left['height'], right['y'] + right['height'])) / 2.0,
      'boxes': [left, right],
      'source': 'red_black_outer_panel_pair',
  }


def _select_prequal_black_target(boxes, width, cfg):
  full_candidates = []
  leg_candidates = []
  for box in boxes:
    bw, bh = box['width'], box['height']
    if (
        bh >= cfg['leg_min_height_px']
        and bw >= width * cfg['full_min_width_frac']
        and bw >= bh * cfg['full_min_aspect']
    ):
      full_candidates.append(box)
    if bh < cfg['leg_min_height_px'] or bh <= bw * cfg['leg_min_aspect']:
      continue
    leg_candidates.append(box)

  if full_candidates:
    full_gate = max(full_candidates, key=lambda c: (c['area'], c['width']))
    return {
        'area': full_gate['area'],
        'center_x': full_gate['center_x'],
        'center_y': full_gate['center_y'],
        'boxes': [full_gate],
        'source': 'full_contour',
    }

  if len(leg_candidates) < 2:
    return None

  best_pair = None
  best_score = 0.0
  for left in leg_candidates:
    for right in leg_candidates:
      if left is right or left['center_x'] >= right['center_x']:
        continue
      separation = right['center_x'] - left['center_x']
      if separation < width * cfg['pair_min_separation_frac']:
        continue
      height_ratio = min(left['height'], right['height']) / max(
          left['height'], right['height'])
      if height_ratio < cfg['pair_height_ratio_min']:
        continue
      vertical_delta = abs(left['center_y'] - right['center_y'])
      if vertical_delta > max(left['height'], right['height']) * cfg['pair_vertical_delta_frac']:
        continue
      pair_width = (
          max(left['x'] + left['width'], right['x'] + right['width'])
          - min(left['x'], right['x']))
      pair_height = max(left['height'], right['height'])
      if pair_width < pair_height * cfg['pair_min_width_height_ratio']:
        continue
      score = left['area'] + right['area'] + separation
      if score > best_score:
        best_score = score
        best_pair = (left, right)

  if best_pair is None:
    return None
  left, right = best_pair
  y_min = min(left['y'], right['y'])
  y_max = max(left['y'] + left['height'], right['y'] + right['height'])
  return {
      'area': left['area'] + right['area'],
      'center_x': (left['center_x'] + right['center_x']) / 2.0,
      'center_y': (y_min + y_max) / 2.0,
      'boxes': [left, right],
      'source': 'leg_pair',
  }


def detect_gate(frame, cfg):
  """Eagle-style gate: black full bar / leg pair, else task1 red/black pair."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

  black_mask = _morph_mask(_black_mask(hsv, cfg))
  target = _select_prequal_black_target(
      _contour_boxes(black_mask, w, cfg, min_area=120.0), w, cfg)

  if target is None:
    gate_mask = _morph_mask(_black_mask(hsv, cfg) | _red_mask(hsv, cfg))
    panel_candidates = [
        b for b in _contour_boxes(gate_mask, w, cfg, min_area=80.0)
        if b['height'] >= 20 and b['height'] > b['width'] * 1.2
    ]
    clusters = _cluster_vertical_panels(panel_candidates, w)
    target = _select_outer_panel_pair(
        clusters, w, cfg['task1_pair_min_separation_frac'])

  if target is None:
    return None

  class_name = (
      'gate' if target.get('source') == 'red_black_outer_panel_pair' else 'black_gate')
  det = _gate_detection_from_target(target, w, h, class_name)
  if det['confidence'] < cfg['min_confidence']:
    return None
  return det


def gate_debug_overlay(frame, cfg):
  if frame is None:
    return None
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  overlay = frame.copy()
  roi_view = overlay
  dark = _black_mask(hsv, cfg)
  red = _red_mask(hsv, cfg)
  roi_view[dark > 0] = (0, 180, 0)
  roi_view[red > 0] = (255, 0, 255)
  cv2.addWeighted(frame, 0.55, overlay, 0.45, 0, overlay)
  det = detect_gate(frame, cfg)
  if det and det.get('pillars'):
    for side, pillar in det['pillars'].items():
      if not pillar.get('xyxy'):
        continue
      x1, y1, x2, y2 = [int(v) for v in pillar['xyxy']]
      color = (255, 120, 0) if side == 'left' else (0, 120, 255)
      cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
  return overlay


def detect_yellow_pole(frame, cfg):
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  mask = cv2.inRange(
      hsv,
      np.array([cfg['yellow_h_low'], cfg['yellow_s_min'], cfg['yellow_v_min']]),
      np.array([cfg['yellow_h_high'], 255, 255]),
  )
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

  area_norm = float((x2 - x1) * (y2 - y1)) / float(w * h)
  return {
      'class_name': 'yellow_pole',
      'confidence': min(0.99, conf),
      'xyxy': [float(x1), float(y1), float(x2), float(y2)],
      'x': (x1 + x2) / 2.0 / max(float(w), 1.0),
      'y': (y1 + y2) / 2.0 / max(float(h), 1.0),
      'area': area_norm,
  }


def process_prequal_cv(frame, config_path=None, min_confidence=None):
  if frame is None:
    return []
  cfg = load_prequal_cv_config(config_path)
  if min_confidence is not None:
    cfg['min_confidence'] = float(min_confidence)

  detections = []
  gate = detect_gate(frame, cfg)
  if gate is not None:
    detections.append(gate)
  pole = detect_yellow_pole(frame, cfg)
  if pole is not None:
    detections.append(pole)
  return detections

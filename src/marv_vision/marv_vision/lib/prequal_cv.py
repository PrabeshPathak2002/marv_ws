"""OpenCV pre-qual detectors (EagleAUV ros2_ws patterns).

Gate: split red/black outer legs (RoboSub checkerboard gate), 2x2 panel, or leg pair.
Marker: Rust-Oleum Neon Orange pole.
"""

from pathlib import Path

import cv2
import numpy as np
import yaml

DEFAULT_CONFIG = {
    'marker_h_low': 5,
    'marker_h_high': 24,
    'marker_s_min': 120,
    'marker_v_min': 110,
    'marker_min_height_frac': 0.12,
    'marker_min_aspect': 1.4,
    'yellow_h_low': 5,
    'yellow_h_high': 24,
    'yellow_s_min': 120,
    'yellow_v_min': 110,
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
    'checker_min_area_frac': 0.015,
    'checker_min_aspect': 0.35,
    'checker_max_aspect': 2.8,
    'checker_quad_min_fill': 0.10,
    'leg_split_min_fill': 0.18,
    'leg_dilate_width_px': 11,
    'blue_h_low': 85,
    'blue_h_high': 125,
    'blue_scene_min_frac': 0.30,
    'blue_screen_min_frac': 0.18,
    'blue_gate_r_delta': 22,
    'blue_gate_g_max': 155,
    'blue_gate_col_fill_min': 0.06,
    'blue_gate_min_run_width_frac': 0.04,
    'blue_gate_min_gap_frac': 0.10,
    'blue_gate_vert_close_px': 15,
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
  # Legacy yellow_* keys fill marker_* when only yellow is set in YAML.
  for key in ('h_low', 'h_high', 's_min', 'v_min', 'min_height_frac', 'min_aspect'):
    marker_key = f'marker_{key}'
    yellow_key = f'yellow_{key}'
    if yellow_key in section and marker_key not in section:
      cfg[marker_key] = section[yellow_key]
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


def _black_mask(hsv, cfg, bgr=None):
  mask = cv2.inRange(
      hsv,
      np.array([0, 0, 0]),
      np.array([180, cfg['gate_s_max'], cfg['gate_v_max']]),
  )
  if bgr is None:
    return mask
  gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
  _, dark = cv2.threshold(
      gray, int(cfg['gate_v_max']), 255, cv2.THRESH_BINARY_INV)
  b_chan, g_chan, r_chan = cv2.split(bgr)
  max_c = np.maximum(np.maximum(b_chan, g_chan), r_chan)
  _, ch_dark = cv2.threshold(
      max_c, int(cfg['gate_v_max']), 255, cv2.THRESH_BINARY_INV)
  return cv2.bitwise_or(mask, cv2.bitwise_and(dark, ch_dark))


def _red_mask(hsv, cfg, bgr=None):
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
  mask = cv2.bitwise_or(low, high)
  if bgr is None:
    return mask
  b_chan, g_chan, r_chan = cv2.split(bgr)
  rg = cv2.subtract(r_chan, g_chan)
  rb = cv2.subtract(r_chan, b_chan)
  _, rg_ok = cv2.threshold(rg, 25, 255, cv2.THRESH_BINARY)
  _, rb_ok = cv2.threshold(rb, 25, 255, cv2.THRESH_BINARY)
  red_dom = cv2.bitwise_and(rg_ok, rb_ok)
  return cv2.bitwise_or(mask, red_dom)


def _gate_color_mask(frame, hsv, cfg):
  """Red + black regions with horizontal dilation to merge split leg halves."""
  mask = cv2.bitwise_or(
      _black_mask(hsv, cfg, frame), _red_mask(hsv, cfg, frame))
  kw = max(3, int(cfg.get('leg_dilate_width_px', 11)))
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 3))
  mask = cv2.dilate(mask, kernel, iterations=1)
  return _morph_mask(mask)


def _blue_screen_mask(hsv, cfg):
  """Largest blue region (TV/pool-tank background behind the gate)."""
  blue = cv2.inRange(
      hsv,
      np.array([cfg['blue_h_low'], 70, 60]),
      np.array([cfg['blue_h_high'], 255, 255]),
  )
  blue = cv2.morphologyEx(
      blue, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)
  h, w = hsv.shape[:2]
  min_area = w * h * float(cfg['blue_screen_min_frac'])
  best = None
  best_area = 0.0
  for box in _contour_boxes(blue, w, cfg, min_area=min_area):
    if box['area'] > best_area:
      best_area = box['area']
      best = box
  if best is None:
    return None
  mask = np.zeros((h, w), dtype=np.uint8)
  x1, y1 = int(best['x']), int(best['y'])
  x2 = x1 + int(best['width'])
  y2 = y1 + int(best['height'])
  mask[y1:y2, x1:x2] = 255
  return mask


def _is_blue_screen_scene(hsv, cfg):
  blue = cv2.inRange(
      hsv,
      np.array([cfg['blue_h_low'], 70, 60]),
      np.array([cfg['blue_h_high'], 255, 255]),
  )
  frac = float(np.count_nonzero(blue)) / float(blue.size)
  return frac >= float(cfg['blue_scene_min_frac'])


def _blue_screen_gate_pixels(frame, blue_mask, cfg):
  """Gate marks on a blue screen: warm (red paint) + dark (black paint) vs blue bg."""
  b_chan, g_chan, r_chan = cv2.split(frame)
  r_delta = int(cfg['blue_gate_r_delta'])
  g_max = int(cfg['blue_gate_g_max'])
  warm = cv2.bitwise_and(cv2.compare(r_chan, cv2.add(b_chan, r_delta), cv2.CMP_GT), blue_mask)
  dark = cv2.bitwise_and(cv2.compare(g_chan, g_max, cv2.CMP_LT), blue_mask)
  dark = cv2.bitwise_and(dark, cv2.compare(r_chan, 200, cv2.CMP_LT))
  gate = cv2.bitwise_or(warm, dark)
  vk = max(5, int(cfg['blue_gate_vert_close_px']))
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, vk))
  return cv2.morphologyEx(gate, cv2.MORPH_CLOSE, kernel)


def _column_fill_runs(col_fill, width, cfg):
  """Return [(x_start, x_end), ...] for columns with enough gate pixels."""
  thresh = float(cfg['blue_gate_col_fill_min'])
  min_w = max(8, int(width * float(cfg['blue_gate_min_run_width_frac'])))
  runs = []
  start = None
  for x, fill in enumerate(col_fill):
    if fill >= thresh:
      if start is None:
        start = x
    elif start is not None:
      if x - start >= min_w:
        runs.append((start, x - 1))
      start = None
  if start is not None and width - start >= min_w:
    runs.append((start, width - 1))
  return runs


def _box_from_column_run(gate_mask, x0, x1):
  segment = gate_mask[:, x0:x1 + 1]
  ys = np.where(segment.sum(axis=1) > 0)[0]
  if ys.size == 0:
    return None
  y0, y1 = int(ys[0]), int(ys[-1])
  area = float(np.count_nonzero(segment))
  bw = x1 - x0 + 1
  bh = y1 - y0 + 1
  return {
      'area': area,
      'x': x0,
      'y': y0,
      'width': bw,
      'height': bh,
      'center_x': x0 + bw / 2.0,
      'center_y': y0 + bh / 2.0,
  }


def _detect_blue_screen_gate(frame, cfg):
  """Gate on solid blue TV/tank background (bench): two vertical side columns + opening."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  if not _is_blue_screen_scene(hsv, cfg):
    return None
  blue_mask = _blue_screen_mask(hsv, cfg)
  if blue_mask is None:
    return None
  gate_mask = _blue_screen_gate_pixels(frame, blue_mask, cfg)
  y_margin = int(h * 0.08)
  band = gate_mask[y_margin:h - y_margin, :]
  col_fill = band.sum(axis=0) / 255.0 / max(band.shape[0], 1)
  runs = _column_fill_runs(col_fill, w, cfg)
  if len(runs) < 2:
    return None
  min_gap = w * float(cfg['blue_gate_min_gap_frac'])
  left_run, right_run = runs[0], runs[-1]
  gap = right_run[0] - left_run[1]
  if gap < min_gap:
    return None
  left = _box_from_column_run(gate_mask, left_run[0], left_run[1])
  right = _box_from_column_run(gate_mask, right_run[0], right_run[1])
  if left is None or right is None:
    return None
  min_h = h * 0.12
  if left['height'] < min_h or right['height'] < min_h:
    return None
  return {
      'area': left['area'] + right['area'],
      'center_x': (left['center_x'] + right['center_x']) / 2.0,
      'center_y': (min(left['y'], right['y']) + max(
          left['y'] + left['height'], right['y'] + right['height'])) / 2.0,
      'boxes': [left, right],
      'source': 'blue_screen_gate',
  }


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


def _panel_red_black_labels(hsv, box, cfg, bgr=None):
  x, y, bw, bh = box['x'], box['y'], box['width'], box['height']
  roi_hsv = hsv[y:y + bh, x:x + bw]
  roi_bgr = bgr[y:y + bh, x:x + bw] if bgr is not None else None
  if roi_hsv.size == 0:
    return False, False
  red_px = cv2.countNonZero(_red_mask(roi_hsv, cfg, roi_bgr))
  black_px = cv2.countNonZero(_black_mask(roi_hsv, cfg, roi_bgr))
  total = float(roi_hsv.shape[0] * roi_hsv.shape[1])
  red = red_px > total * 0.08
  black = black_px > total * 0.08
  return red, black


def _region_color_label(hsv_roi, cfg, bgr_roi=None):
  """Classify an ROI as red (R), black (B), or unknown."""
  if hsv_roi.size == 0:
    return '?'
  red_px = cv2.countNonZero(_red_mask(hsv_roi, cfg, bgr_roi))
  black_px = cv2.countNonZero(_black_mask(hsv_roi, cfg, bgr_roi))
  total = float(hsv_roi.shape[0] * hsv_roi.shape[1])
  min_fill = float(cfg.get('leg_split_min_fill', 0.18))
  if red_px < total * min_fill and black_px < total * min_fill:
    return '?'
  if red_px > black_px * 1.15:
    return 'R'
  if black_px > red_px * 1.15:
    return 'B'
  return '?'


def _leg_vertical_split_colors(hsv, box, cfg, bgr=None):
  """Top/bottom colors for a vertical leg (competition gate split panels)."""
  x, y, bw, bh = box['x'], box['y'], box['width'], box['height']
  roi_hsv = hsv[y:y + bh, x:x + bw]
  roi_bgr = bgr[y:y + bh, x:x + bw] if bgr is not None else None
  if roi_hsv.size == 0 or bh < 16:
    return '?', '?'
  mid_y = bh // 2
  top_hsv, bot_hsv = roi_hsv[0:mid_y, :], roi_hsv[mid_y:bh, :]
  top_bgr = roi_bgr[0:mid_y, :] if roi_bgr is not None else None
  bot_bgr = roi_bgr[mid_y:bh, :] if roi_bgr is not None else None
  return (
      _region_color_label(top_hsv, cfg, top_bgr),
      _region_color_label(bot_hsv, cfg, bot_bgr),
  )


def _is_split_rb_leg(hsv, box, cfg, bgr=None):
  top, bottom = _leg_vertical_split_colors(hsv, box, cfg, bgr)
  return top in ('R', 'B') and bottom in ('R', 'B') and top != bottom


def _is_competition_gate_pair(target, frame, cfg):
  """RoboSub gate: outer legs with complementary red/black vertical splits."""
  boxes = sorted(target.get('boxes') or [], key=lambda b: b['center_x'])
  if len(boxes) < 2:
    return False
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  left, right = boxes[0], boxes[-1]
  if _is_split_rb_leg(hsv, left, cfg, frame) and _is_split_rb_leg(hsv, right, cfg, frame):
    l_top, l_bot = _leg_vertical_split_colors(hsv, left, cfg, frame)
    r_top, r_bot = _leg_vertical_split_colors(hsv, right, cfg, frame)
    return l_top != r_top and l_bot != r_bot
  has_red = has_black = False
  for box in (left, right):
    red, black = _panel_red_black_labels(hsv, box, cfg, frame)
    has_red = has_red or red
    has_black = has_black or black
  if has_red and has_black:
    return True
  return has_red and not has_black


def _quadrant_color_label(hsv_quad, cfg, bgr_quad=None):
  """Classify one checkerboard cell as red, black, or unknown."""
  if hsv_quad.size == 0:
    return '?'
  red_px = cv2.countNonZero(_red_mask(hsv_quad, cfg, bgr_quad))
  black_px = cv2.countNonZero(_black_mask(hsv_quad, cfg, bgr_quad))
  total = float(hsv_quad.shape[0] * hsv_quad.shape[1])
  min_fill = float(cfg.get('checker_quad_min_fill', 0.12))
  if red_px < total * min_fill and black_px < total * min_fill:
    return '?'
  if red_px > black_px * 1.15:
    return 'R'
  if black_px > red_px * 1.15:
    return 'B'
  return '?'


def _is_checkerboard_4sq(hsv, x1, y1, x2, y2, cfg, bgr=None):
  """True when ROI is a 2x2 red/black checker (four squares, half each color)."""
  roi = hsv[y1:y2, x1:x2]
  roi_bgr = bgr[y1:y2, x1:x2] if bgr is not None else None
  if roi.size == 0:
    return False
  h, w = roi.shape[:2]
  if h < 24 or w < 24:
    return False
  mid_x, mid_y = w // 2, h // 2
  quads_hsv = (
      roi[0:mid_y, 0:mid_x],
      roi[0:mid_y, mid_x:w],
      roi[mid_y:h, 0:mid_x],
      roi[mid_y:h, mid_x:w],
  )
  if roi_bgr is not None:
    quads_bgr = (
        roi_bgr[0:mid_y, 0:mid_x],
        roi_bgr[0:mid_y, mid_x:w],
        roi_bgr[mid_y:h, 0:mid_x],
        roi_bgr[mid_y:h, mid_x:w],
    )
    labels = [
        _quadrant_color_label(qh, cfg, qb)
        for qh, qb in zip(quads_hsv, quads_bgr)]
  else:
    labels = [_quadrant_color_label(q, cfg) for q in quads_hsv]
  if labels.count('?') > 0:
    return False
  if labels.count('R') != 2 or labels.count('B') != 2:
    return False
  # Opposite corners match: TL==BR and TR==BL (either orientation).
  return labels[0] == labels[3] and labels[1] == labels[2] and labels[0] != labels[1]


def _detect_checkerboard_gate(frame, cfg):
  """Find gate panel with 2x2 red/black checkerboard (four squares)."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  gate_mask = _gate_color_mask(frame, hsv, cfg)
  min_area = w * h * float(cfg.get('checker_min_area_frac', 0.015))
  min_aspect = float(cfg.get('checker_min_aspect', 0.35))
  max_aspect = float(cfg.get('checker_max_aspect', 2.8))

  best = None
  best_area = 0.0
  for box in _contour_boxes(gate_mask, w, cfg, min_area=min_area):
    bw, bh = box['width'], box['height']
    aspect = bw / max(bh, 1)
    if aspect < min_aspect or aspect > max_aspect:
      continue
    x1, y1 = int(box['x']), int(box['y'])
    x2, y2 = x1 + int(bw), y1 + int(bh)
    if not _is_checkerboard_4sq(hsv, x1, y1, x2, y2, cfg, frame):
      continue
    if box['area'] > best_area:
      best_area = box['area']
      best = {
          'area': box['area'],
          'center_x': box['center_x'],
          'center_y': box['center_y'],
          'boxes': [box],
          'source': 'checkerboard_4sq',
      }
  return best


def _vertical_leg_candidates(frame, hsv, cfg, w, h):
  gate_mask = _gate_color_mask(frame, hsv, cfg)
  min_h = max(cfg['leg_min_height_px'], h * 0.10)
  candidates = [
      b for b in _contour_boxes(gate_mask, w, cfg, min_area=80.0)
      if b['height'] >= min_h and b['height'] > b['width'] * 1.1
  ]
  return _cluster_vertical_panels(candidates, w)


def _detect_split_leg_gate_pair(frame, cfg):
  """RoboSub gate back view: left leg R/B, right leg B/R; ignore center red pole."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  split_legs = [
      c for c in _vertical_leg_candidates(frame, hsv, cfg, w, h)
      if _is_split_rb_leg(hsv, c, cfg, frame)]
  if len(split_legs) < 2:
    return None
  split_legs.sort(key=lambda c: c['center_x'])
  left, right = split_legs[0], split_legs[-1]
  separation = right['center_x'] - left['center_x']
  if separation < w * cfg['task1_pair_min_separation_frac']:
    return None
  target = {
      'area': left['area'] + right['area'],
      'center_x': (left['center_x'] + right['center_x']) / 2.0,
      'center_y': (min(left['y'], right['y']) + max(
          left['y'] + left['height'], right['y'] + right['height'])) / 2.0,
      'boxes': [left, right],
      'source': 'split_leg_pair',
  }
  if not _is_competition_gate_pair(target, frame, cfg):
    return None
  return target


def detect_gate(frame, cfg):
  """Pre-qual gate: blue-screen bench, split legs, checkerboard, or leg pair."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

  target = _detect_blue_screen_gate(frame, cfg)

  if target is None:
    target = _detect_split_leg_gate_pair(frame, cfg)

  if target is None:
    target = _detect_checkerboard_gate(frame, cfg)

  if target is None:
    clusters = _vertical_leg_candidates(frame, hsv, cfg, w, h)
    target = _select_outer_panel_pair(
        clusters, w, cfg['task1_pair_min_separation_frac'])
    if target is not None and not _is_competition_gate_pair(target, frame, cfg):
      target = None

  if target is None:
    return None

  det = _gate_detection_from_target(target, w, h, 'gate')
  if det['confidence'] < cfg['min_confidence']:
    return None
  return det


def gate_debug_overlay(frame, cfg):
  if frame is None:
    return None
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  overlay = frame.copy()
  roi_view = overlay
  dark = _black_mask(hsv, cfg, frame)
  red = _red_mask(hsv, cfg, frame)
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


def detect_neon_orange_marker(frame, cfg):
  """Rust-Oleum Neon Orange vertical marker pole."""
  h, w = frame.shape[:2]
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  h_low = cfg.get('marker_h_low', cfg['yellow_h_low'])
  h_high = cfg.get('marker_h_high', cfg['yellow_h_high'])
  s_min = cfg.get('marker_s_min', cfg['yellow_s_min'])
  v_min = cfg.get('marker_v_min', cfg['yellow_v_min'])
  min_h_frac = cfg.get('marker_min_height_frac', cfg['yellow_min_height_frac'])
  min_aspect = cfg.get('marker_min_aspect', cfg['yellow_min_aspect'])
  mask = cv2.inRange(
      hsv,
      np.array([h_low, s_min, v_min]),
      np.array([h_high, 255, 255]),
  )
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
  mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

  contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  min_h = h * min_h_frac
  best_box = None
  best_score = 0.0

  for cnt in contours:
    x, y, bw, bh = cv2.boundingRect(cnt)
    if bh < min_h or bw < 4:
      continue
    aspect = bh / max(bw, 1)
    if aspect < min_aspect:
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
      'class_name': 'neon_orange',
      'confidence': min(0.99, conf),
      'xyxy': [float(x1), float(y1), float(x2), float(y2)],
      'x': (x1 + x2) / 2.0 / max(float(w), 1.0),
      'y': (y1 + y2) / 2.0 / max(float(h), 1.0),
      'area': area_norm,
  }


def detect_yellow_pole(frame, cfg):
  """Backward-compatible alias for neon orange marker detection."""
  det = detect_neon_orange_marker(frame, cfg)
  if det is None:
    return None
  legacy = dict(det)
  legacy['class_name'] = 'yellow_pole'
  return legacy


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
  pole = detect_neon_orange_marker(frame, cfg)
  if pole is not None:
    detections.append(pole)
  return detections

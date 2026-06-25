"""Unit tests for OpenCV pre-qual detectors."""

import cv2
import numpy as np

from marv_vision.lib.prequal_cv import (
    detect_gate,
    detect_yellow_pole,
    load_prequal_cv_config,
    process_prequal_cv,
)


def _blank_bgr(h=480, w=640):
  return np.full((h, w, 3), 128, dtype=np.uint8)


def _draw_gate_pillars(frame, color, left_x=60, right_x=540, top=120, bottom=400):
  cv2.rectangle(frame, (left_x, top), (left_x + 40, bottom), color, -1)
  cv2.rectangle(frame, (right_x, top), (right_x + 40, bottom), color, -1)


def test_detect_neon_orange_marker_on_synthetic_image():
  frame = _blank_bgr()
  cv2.rectangle(frame, (300, 80), (340, 400), (0, 120, 255), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.2
  from marv_vision.lib.prequal_cv import detect_neon_orange_marker
  det = detect_neon_orange_marker(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'neon_orange'
  assert det['confidence'] > 0.2


def test_detect_yellow_pole_on_synthetic_image():
  frame = _blank_bgr()
  cv2.rectangle(frame, (300, 80), (340, 400), (0, 120, 255), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.2
  det = detect_yellow_pole(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'yellow_pole'
  assert det['confidence'] > 0.2


def _draw_split_leg(frame, x, top, bottom, width, top_color, bottom_color):
  mid = (top + bottom) // 2
  cv2.rectangle(frame, (x, top), (x + width, mid), top_color, -1)
  cv2.rectangle(frame, (x, mid), (x + width, bottom), bottom_color, -1)


def test_detect_blue_screen_gate_photo():
  """Bench TV gate on blue background (user reference photo)."""
  import os
  photo = (
      '/home/eagleauv/.cursor/projects/home-eagleauv-marv-ws/assets/'
      'gate-1262d78f-2900-4b55-abf5-35f3ff31aec2.png')
  if not os.path.isfile(photo):
    return
  frame = cv2.imread(photo)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.10
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'gate'
  assert det.get('source') == 'blue_screen_gate'
  assert det['area'] > 0.02


def test_detect_competition_gate_split_legs():
  """RoboSub gate back: left R/B, right B/R, center red pole ignored."""
  frame = _blank_bgr()
  red, black = (0, 0, 220), (10, 10, 10)
  _draw_split_leg(frame, 55, 90, 390, 38, red, black)
  _draw_split_leg(frame, 545, 90, 390, 38, black, red)
  cv2.rectangle(frame, (310, 120), (330, 280), red, -1)  # center red pole
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'gate'
  assert det.get('source') in ('split_leg_pair', 'red_black_outer_panel_pair')
  assert det['area'] > 0.01


def test_detect_gate_red_black_leg_pair():
  frame = _blank_bgr()
  cv2.rectangle(frame, (60, 120), (100, 400), (0, 0, 220), -1)
  cv2.rectangle(frame, (540, 120), (580, 400), (10, 10, 10), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'gate'


def test_detect_checkerboard_gate():
  frame = _blank_bgr()
  x0, y0, size = 220, 140, 200
  hs = size // 2
  cv2.rectangle(frame, (x0, y0), (x0 + hs, y0 + hs), (0, 0, 220), -1)
  cv2.rectangle(frame, (x0 + hs, y0), (x0 + size, y0 + hs), (10, 10, 10), -1)
  cv2.rectangle(frame, (x0, y0 + hs), (x0 + hs, y0 + size), (10, 10, 10), -1)
  cv2.rectangle(frame, (x0 + hs, y0 + hs), (x0 + size, y0 + size), (0, 0, 220), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'gate'


def test_detect_gate_ignores_all_black_pillars():
  frame = _blank_bgr()
  _draw_gate_pillars(frame, (10, 10, 10))
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  assert detect_gate(frame, cfg) is None


def test_detect_gate_rejects_single_pillar():
  frame = _blank_bgr()
  cv2.rectangle(frame, (60, 120), (100, 400), (10, 10, 10), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  assert detect_gate(frame, cfg) is None


def test_detect_gate_with_both_red_pillars():
  frame = _blank_bgr()
  _draw_gate_pillars(frame, (0, 0, 220))
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'gate'


def test_process_prequal_cv_empty_frame():
  assert process_prequal_cv(None) == []

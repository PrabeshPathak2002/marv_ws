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


def test_detect_yellow_pole_on_synthetic_image():
  frame = _blank_bgr()
  cv2.rectangle(frame, (300, 80), (340, 400), (0, 255, 255), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.2
  det = detect_yellow_pole(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'yellow_pole'
  assert det['confidence'] > 0.2


def test_detect_gate_with_both_black_pillars():
  frame = _blank_bgr()
  _draw_gate_pillars(frame, (10, 10, 10))
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'black_gate'
  assert 'pillars' in det
  assert det['pillars']['left']['side'] == 'left'
  assert det['pillars']['right']['side'] == 'right'


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

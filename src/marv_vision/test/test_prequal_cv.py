"""Unit tests for OpenCV pre-qual detectors."""

import cv2
import numpy as np

from marv_vision.lib.prequal_cv import (
    detect_black_gate,
    detect_yellow_pole,
    load_prequal_cv_config,
    process_prequal_cv,
)


def _blank_bgr(h=480, w=640):
  return np.full((h, w, 3), 128, dtype=np.uint8)


def test_detect_yellow_pole_on_synthetic_image():
  frame = _blank_bgr()
  cv2.rectangle(frame, (300, 80), (340, 400), (0, 255, 255), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.2
  det = detect_yellow_pole(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'yellow_pole'
  assert det['confidence'] > 0.2


def test_detect_black_gate_on_synthetic_image():
  frame = _blank_bgr()
  cv2.rectangle(frame, (100, 200), (540, 320), (10, 10, 10), -1)
  cfg = load_prequal_cv_config()
  cfg['min_confidence'] = 0.15
  det = detect_black_gate(frame, cfg)
  assert det is not None
  assert det['class_name'] == 'black_gate'


def test_process_prequal_cv_empty_frame():
  assert process_prequal_cv(None) == []

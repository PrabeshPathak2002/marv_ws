#!/usr/bin/env python3
"""Live front-camera preview with pre-qual bounding boxes (no ROS required)."""

import argparse
import os
import sys

import cv2

from marv_vision.lib.camera_usb import open_v4l2_capture
from marv_vision.lib.draw_detections import draw_detections
from marv_vision.lib.prequal_cv import (
    gate_debug_overlay,
    load_prequal_cv_config,
    process_prequal_cv,
)


def _default_config():
  try:
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory('marv_bringup')
    path = os.path.join(share, 'config', 'prequal_cv.yaml')
    if os.path.isfile(path):
      return path
  except Exception:
    pass
  return None


def main():
  parser = argparse.ArgumentParser(description='Live f_cam debug viewer with bounding boxes')
  parser.add_argument('--device', default='/dev/video0')
  parser.add_argument('--width', type=int, default=1280)
  parser.add_argument('--height', type=int, default=720)
  parser.add_argument('--conf', type=float, default=0.20)
  parser.add_argument('--config', default=_default_config())
  parser.add_argument(
      '--show-mask',
      action='store_true',
      help='Overlay gate masks (green=dark, magenta=red) to tune HSV',
  )
  args = parser.parse_args()
  cfg = load_prequal_cv_config(args.config)

  cap = open_v4l2_capture(
      args.device, width=args.width, height=args.height, fps=30, fourcc='MJPG')
  if cap is None or not cap.isOpened():
    print(f'Failed to open camera {args.device}', file=sys.stderr)
    print('Stop prequal_bringup / f_cam_node first (camera busy).', file=sys.stderr)
    return 1

  cv2.namedWindow('f_cam debug', cv2.WINDOW_NORMAL)
  cv2.resizeWindow('f_cam debug', 960, 540)
  print('f_cam debug — press q to quit, m toggles mask overlay')
  show_mask = args.show_mask

  while True:
    ok, frame = cap.read()
    if not ok or frame is None:
      continue

    detections = process_prequal_cv(
        frame, config_path=args.config, min_confidence=args.conf)
    base = gate_debug_overlay(frame, cfg) if show_mask else frame
    annotated = draw_detections(base, detections)
    if detections:
      names = ', '.join(
          f"{d['class_name']}:{d['confidence']:.2f}" for d in detections)
      color = (0, 255, 0)
    else:
      names = 'no detections — try --show-mask, move closer, fill frame with gate'
      color = (0, 0, 255)
    cv2.putText(
        annotated, names, (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)

    cv2.imshow('f_cam debug', annotated)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
      break
    if key == ord('m'):
      show_mask = not show_mask

  cap.release()
  cv2.destroyAllWindows()
  return 0


if __name__ == '__main__':
  sys.exit(main())

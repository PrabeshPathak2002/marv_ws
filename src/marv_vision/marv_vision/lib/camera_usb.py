"""Open and read USB cameras (exploreHD / V4L2)."""

import cv2


def open_v4l2_capture(device, width=None, height=None, fps=None, fourcc='MJPG'):
  """Open a V4L2 USB camera; prefer MJPEG for exploreHD bandwidth."""
  source = device
  if isinstance(device, str) and device.isdigit():
    source = int(device)

  cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
  if not cap.isOpened() and isinstance(device, str) and not device.isdigit():
    cap = cv2.VideoCapture(device)

  if not cap.isOpened():
    return None

  if fourcc:
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc[:4]))
  if width:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
  if height:
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
  if fps:
    cap.set(cv2.CAP_PROP_FPS, float(fps))

  return cap


def describe_capture(cap):
  """Return human-readable capture settings."""
  if cap is None or not cap.isOpened():
    return 'closed'
  w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fps = cap.get(cv2.CAP_PROP_FPS)
  return f'{w}x{h} @ {fps:.1f} fps'

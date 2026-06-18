"""Tests for V4L2 camera helpers."""

import unittest
from unittest.mock import MagicMock, patch

from marv_vision.lib.camera_usb import describe_capture, open_v4l2_capture


class TestCameraUsb(unittest.TestCase):
  @patch('marv_vision.lib.camera_usb.cv2.VideoCapture')
  def test_open_v4l2_capture_sets_mjpeg(self, mock_vc):
    cap = MagicMock()
    cap.isOpened.return_value = True
    mock_vc.return_value = cap

    result = open_v4l2_capture('/dev/video0', width=1280, height=720, fps=30)

    mock_vc.assert_called_once_with('/dev/video0', unittest.mock.ANY)
    cap.set.assert_any_call(unittest.mock.ANY, unittest.mock.ANY)
    self.assertIs(result, cap)

  def test_describe_capture_closed(self):
    self.assertEqual(describe_capture(None), 'closed')


if __name__ == '__main__':
  unittest.main()

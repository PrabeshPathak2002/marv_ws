"""Unit tests for detect_path behavior."""

from marv_control.lib.detect_path import detect_path


class _FakeLogger:
  def debug(self, *_args, **_kwargs):
    pass


class _FakeNode:
  def get_logger(self):
    return _FakeLogger()


def test_detect_path_returns_cmd_for_path_marker():
  node = _FakeNode()
  vision = 'path:0.80,x:0.40,y:0.50'
  cmd = detect_path(node, vision)
  assert cmd is not None
  assert cmd['surge'] > 0

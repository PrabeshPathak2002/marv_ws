"""Unit tests for traverse_gate behavior."""

from marv_control.lib.traverse_gate import traverse_gate
from marv_control.missions.traverse_gate import TraverseGateMission
from marv_control.missions.base import MissionContext


class _FakeLogger:
  def debug(self, *_args, **_kwargs):
    pass

  def info(self, *_args, **_kwargs):
    pass


class _FakeNode:
  def get_logger(self):
    return _FakeLogger()


def test_traverse_gate_returns_cmd_for_gate_detection():
  node = _FakeNode()
  vision = 'gate:0.90,x:0.60,y:0.50'
  cmd = traverse_gate(node, vision)
  assert cmd is not None
  assert cmd['surge'] > 0


def test_traverse_gate_mission_completes_when_aligned():
  node = _FakeNode()
  mission = TraverseGateMission(node, aligned_frames_required=3)
  ctx = MissionContext(vision_data='gate:0.95,x:0.51,y:0.50')

  result = mission.step(ctx)
  assert not result.complete
  result = mission.step(ctx)
  assert not result.complete
  result = mission.step(ctx)
  assert result.complete
  assert result.success

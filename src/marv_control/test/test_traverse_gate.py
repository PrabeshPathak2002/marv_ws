"""Unit tests for traverse_gate behavior."""

from marv_control.lib.traverse_gate import gate_ready_to_commit, traverse_gate
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
  vision = 'black_gate:0.90,x:0.60,y:0.50,area:0.05'
  cmd = traverse_gate(node, vision, gate_classes=('black_gate', 'gate'))
  assert cmd is not None
  assert cmd['surge'] > 0


def test_gate_ready_to_commit_uses_area_and_center():
  gate = {'confidence': 0.9, 'x': 0.52, 'area': 0.14}
  assert gate_ready_to_commit(gate, commit_area=0.12, commit_deadband=0.30)
  gate['area'] = 0.08
  assert not gate_ready_to_commit(gate, commit_area=0.12, commit_deadband=0.30)


def test_traverse_gate_mission_completes_when_ready_to_commit():
  node = _FakeNode()
  mission = TraverseGateMission(node, commit_area=0.12, commit_deadband=0.30)
  ctx = MissionContext(vision_data='gate:0.95,x:0.51,y:0.50,area:0.15')
  result = mission.step(ctx)
  assert result.complete
  assert result.success

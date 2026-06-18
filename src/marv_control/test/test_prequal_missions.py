"""Unit tests for pre-qual mission behaviors."""

from marv_control.missions.pass_gate import PassGateMission
from marv_control.missions.transit_forward import TransitForwardMission
from marv_control.missions.base import MissionContext


class _FakeLogger:
  def info(self, *_a, **_k):
    pass


class _FakeNode:
  def get_logger(self):
    return _FakeLogger()


def test_pass_gate_completes_after_duration():
  node = _FakeNode()
  mission = PassGateMission(node, duration_s=1.0)
  ctx = MissionContext(elapsed_s=0.5)
  assert not mission.step(ctx).complete
  ctx.elapsed_s = 1.1
  assert mission.step(ctx).complete


def test_transit_forward_completes_at_distance():
  node = _FakeNode()

  class _Pose:
    def __init__(self, x, y):
      self.pose = type('P', (), {'pose': type('PP', (), {
          'position': type('Pos', (), {'x': x, 'y': y, 'z': 1.0})(),
          'orientation': type('O', (), {'x': 0, 'y': 0, 'z': 0, 'w': 1})(),
      })()})()

  mission = TransitForwardMission(node, target_distance_m=5.0)
  start = _Pose(0.0, 0.0)
  ctx = MissionContext(pose=start, elapsed_s=1.0)
  mission.step(ctx)
  ctx.pose = _Pose(5.5, 0.0)
  result = mission.step(ctx)
  assert result.complete

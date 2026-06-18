"""Unit tests for pre-qual mission behaviors."""

from marv_control.missions.approach_marker import ApproachMarkerMission
from marv_control.missions.find_gate import FindGateMission
from marv_control.missions.find_marker import FindMarkerMission
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


def test_transit_forward_spots_marker_after_min_time():
  node = _FakeNode()
  mission = TransitForwardMission(
      node, min_transit_s=1.0, max_transit_s=5.0, use_timed_transit=True)
  ctx = MissionContext(
      vision_data='yellow_pole:0.80,x:0.50,y:0.50,area:0.03',
      elapsed_s=0.5,
  )
  assert not mission.step(ctx).complete
  ctx.elapsed_s = 1.5
  result = mission.step(ctx)
  assert result.complete
  assert result.success


def test_transit_forward_times_out_without_marker():
  node = _FakeNode()
  mission = TransitForwardMission(
      node, min_transit_s=1.0, max_transit_s=2.0, use_timed_transit=True)
  ctx = MissionContext(elapsed_s=2.5)
  result = mission.step(ctx)
  assert result.complete
  assert not result.success


def test_find_gate_completes_when_gate_visible():
  node = _FakeNode()
  mission = FindGateMission(node)
  ctx = MissionContext(vision_data='black_gate:0.70,x:0.50,y:0.50,area:0.08')
  result = mission.step(ctx)
  assert result.complete
  assert result.success


def test_find_marker_searches_when_not_visible():
  node = _FakeNode()
  mission = FindMarkerMission(node)
  ctx = MissionContext()
  result = mission.step(ctx)
  assert not result.complete
  assert result.cmd['surge'] > 0


def test_approach_marker_completes_when_close():
  node = _FakeNode()
  mission = ApproachMarkerMission(node, close_area=0.05)
  ctx = MissionContext(vision_data='yellow_pole:0.90,x:0.51,y:0.50,area:0.06')
  result = mission.step(ctx)
  assert result.complete
  assert result.success

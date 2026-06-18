"""Mission name → class registry."""

from marv_control.missions.circle_marker import CircleMarkerMission
from marv_control.missions.depth_hold import DepthHoldMission
from marv_control.missions.detect_path import DetectPathMission
from marv_control.missions.hold import HoldMission
from marv_control.missions.pass_gate import PassGateMission
from marv_control.missions.return_home import ReturnHomeMission
from marv_control.missions.transit_forward import TransitForwardMission
from marv_control.missions.traverse_gate import TraverseGateMission
from marv_control.missions.turn_around import TurnAroundMission
from marv_control.missions.wait_submerged import WaitSubmergedMission

MISSION_REGISTRY = {
    'depth_hold': DepthHoldMission,
    'traverse_gate': TraverseGateMission,
    'detect_path': DetectPathMission,
    'return_home': ReturnHomeMission,
    'hold': HoldMission,
    'wait_submerged': WaitSubmergedMission,
    'pass_gate': PassGateMission,
    'transit_forward': TransitForwardMission,
    'circle_marker': CircleMarkerMission,
    'turn_around': TurnAroundMission,
}


def create_mission(behavior_key, node, config=None):
  """Instantiate a mission class by behavior key."""
  cls = MISSION_REGISTRY.get(behavior_key)
  if cls is None:
    raise KeyError(f'Unknown mission behavior: {behavior_key}')
  return cls(node, **(config or {}))

"""Depth-hold mission (no horizontal motion)."""

from marv_control.missions.base import Mission, MissionContext, MissionResult


class DepthHoldMission(Mission):
  name = 'depth_hold'
  behavior_key = 'depth_hold'

  def step(self, ctx: MissionContext) -> MissionResult:
    return MissionResult(cmd=None)

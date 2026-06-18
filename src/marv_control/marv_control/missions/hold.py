"""Idle hold mission — zero horizontal command, depth hold handled upstream."""

from marv_control.missions.base import Mission, MissionContext, MissionResult


class HoldMission(Mission):
  name = 'hold'
  behavior_key = 'hold'

  def step(self, ctx: MissionContext) -> MissionResult:
    return MissionResult(cmd={'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0})

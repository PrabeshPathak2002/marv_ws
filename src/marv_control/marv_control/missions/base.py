"""Mission lifecycle base (inspired by Inspiration Robotics template_mission)."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MissionResult:
  """One control-cycle output from a mission step."""

  cmd: Optional[Dict[str, float]] = None
  complete: bool = False
  success: bool = True
  message: str = ''


@dataclass
class MissionContext:
  """Shared runtime state passed into mission steps."""

  vision_data: Optional[str] = None
  pose: Any = None
  elapsed_s: float = 0.0
  step_count: int = 0
  extras: Dict[str, Any] = field(default_factory=dict)


class Mission:
  """Base mission with run/cleanup lifecycle (one step per control tick)."""

  name = 'mission'
  behavior_key = 'hold'

  def __init__(self, node, **config):
    self._node = node
    self.config = config
    self._aligned_frames = 0

  def step(self, ctx: MissionContext) -> MissionResult:
    """Compute motion for this tick. Override in subclasses."""
    return MissionResult()

  def cleanup(self):
    """Called when mission ends (success, failure, or timeout)."""
    self._aligned_frames = 0

  def stop(self):
    """Planner timeout hook — same as cleanup for Marv missions."""
    self.cleanup()

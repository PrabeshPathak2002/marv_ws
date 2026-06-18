"""Unit tests for Ping1D range helpers."""

from marv_control.lib.ping_helpers import is_gate_cleared, scale_surge_by_range


def test_scale_surge_reduces_near_obstacle():
  assert scale_surge_by_range(0.3, 0.5, slow_start_m=2.5, stop_m=0.6) == 0.0
  scaled = scale_surge_by_range(0.3, 1.5, slow_start_m=2.5, stop_m=0.6)
  assert 0.0 < scaled < 0.3


def test_is_gate_cleared():
  assert is_gate_cleared(3.0, 2.5, min_elapsed_s=1.0, elapsed_s=2.0)
  assert not is_gate_cleared(1.0, 2.5, min_elapsed_s=1.0, elapsed_s=2.0)

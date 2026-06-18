"""Unit tests for config loader."""

from pathlib import Path

from marv_control.lib.config_loader import behavior_config, control_config, load_marv_config


def test_load_marv_config_missing_returns_empty():
  assert load_marv_config('/nonexistent/marv.yaml') == {}


def test_behavior_config_defaults():
  cfg = {'behaviors': {'traverse_gate': {'conf_min': 0.4}}}
  assert behavior_config(cfg, 'traverse_gate')['conf_min'] == 0.4
  assert behavior_config(cfg, 'unknown') == {}


def test_control_config_defaults():
  ctrl = control_config({})
  assert ctrl['target_depth_m'] == 1.0
  assert ctrl['home_xy'] == [0.0, 0.0]

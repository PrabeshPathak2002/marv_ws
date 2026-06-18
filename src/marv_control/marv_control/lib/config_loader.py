"""Load vehicle and behavior config from YAML."""

from pathlib import Path

import yaml


def load_marv_config(config_path):
  """Load marv.yaml; returns empty dict if file missing."""
  path = Path(config_path)
  if not path.is_file():
    return {}
  with path.open('r', encoding='utf-8') as handle:
    data = yaml.safe_load(handle) or {}
  return data


def behavior_config(config, behavior_key):
  """Return behavior-specific dict from loaded config."""
  behaviors = config.get('behaviors', {})
  return dict(behaviors.get(behavior_key, {}))


def control_config(config):
  """Return control section with defaults."""
  section = dict(config.get('control', {}))
  section.setdefault('target_depth_m', 1.0)
  section.setdefault('depth_kp', 0.25)
  section.setdefault('home_xy', [0.0, 0.0])
  return section


def ping_config(config):
  """Return Ping1D tuning section with defaults."""
  section = dict(config.get('ping', {}))
  section.setdefault('obstacle_stop_m', 0.8)
  section.setdefault('approach_slow_m', 2.5)
  section.setdefault('gate_clear_m', 2.5)
  section.setdefault('stop_m', 0.6)
  return section

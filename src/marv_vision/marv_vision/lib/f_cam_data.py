"""Front camera frame processing."""

from pathlib import Path

from marv_vision.lib.model_config import (
    load_front_model_config,
    load_prequal_model_config,
    resolve_model_path,
)
from marv_vision.lib.yolo_inference import run_yolo_inference

_profile_cache = {}


def _get_config(profile='default', model_path=None):
  if model_path:
    path = Path(model_path)
    return {'model_path': resolve_model_path('default', override_path=path)}

  if profile in _profile_cache:
    return _profile_cache[profile]

  if profile == 'prequal':
    cfg = load_prequal_model_config()
  else:
    cfg = load_front_model_config()
  _profile_cache[profile] = cfg
  return cfg


def process_f_cam(frame, model_path=None, conf=0.25, vision_profile='default'):
  """Process front camera frame with YOLO. Returns list of detection dicts."""
  cfg = _get_config(profile=vision_profile, model_path=model_path)
  path = model_path or cfg['model_path']
  return run_yolo_inference(frame, path, conf=conf)

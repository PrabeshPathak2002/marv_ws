"""Load YOLO dataset / model metadata (front_model_data.yaml)."""

from pathlib import Path

import yaml

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / 'weights'
DEFAULT_MODEL_PATH = WEIGHTS_DIR / 'front_model.pt'
DEFAULT_DATA_YAML = WEIGHTS_DIR / 'front_model_data.yaml'
PREQUAL_MODEL_PATH = WEIGHTS_DIR / 'prequal_model.pt'
PREQUAL_DATA_YAML = WEIGHTS_DIR / 'prequal_model_data.yaml'


def resolve_model_path(profile='default', override_path=None):
  """Return weights path for default (14-class) or prequal (2-class) profile."""
  if override_path:
    path = Path(override_path)
    if path.is_file():
      return path
    raise FileNotFoundError(f'Model weights not found: {path}')

  if profile == 'prequal':
    if PREQUAL_MODEL_PATH.is_file() and PREQUAL_MODEL_PATH.stat().st_size > 0:
      return PREQUAL_MODEL_PATH
    if DEFAULT_MODEL_PATH.is_file():
      return DEFAULT_MODEL_PATH
    raise FileNotFoundError(
        f'No prequal weights at {PREQUAL_MODEL_PATH}. '
        'Train per VISION_PREQUAL.md or set model_path param.')

  if not DEFAULT_MODEL_PATH.is_file():
    raise FileNotFoundError(f'Front model not found: {DEFAULT_MODEL_PATH}')
  return DEFAULT_MODEL_PATH


def load_data_yaml(yaml_path=None):
    """Load Ultralytics-style data.yaml. Returns dict with nc and names."""
    path = Path(yaml_path) if yaml_path else DEFAULT_DATA_YAML
    if not path.is_file():
        raise FileNotFoundError(f'Vision data yaml not found: {path}')

    with path.open(encoding='utf-8') as handle:
        data = yaml.safe_load(handle)

    names = data.get('names', [])
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names, key=lambda x: int(x))]
    return {
        'path': path,
        'nc': int(data.get('nc', len(names))),
        'names': list(names),
        'raw': data,
    }


def load_prequal_model_config():
  """Pre-qual model: black_gate + yellow_pole."""
  config = load_data_yaml(PREQUAL_DATA_YAML)
  return {
      'model_path': resolve_model_path('prequal'),
      'data_yaml': PREQUAL_DATA_YAML,
      'class_names': config['names'],
      'nc': config['nc'],
  }


def load_front_model_config():
  """Front camera model weights path + class names from front_model_data.yaml."""
  config = load_data_yaml(DEFAULT_DATA_YAML)
  return {
      'model_path': DEFAULT_MODEL_PATH,
      'data_yaml': DEFAULT_DATA_YAML,
      'class_names': config['names'],
      'nc': config['nc'],
  }

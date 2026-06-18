"""Load YOLO dataset / model metadata (front_model_data.yaml)."""

from pathlib import Path

import yaml

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / 'weights'
DEFAULT_MODEL_PATH = WEIGHTS_DIR / 'front_model.pt'
DEFAULT_DATA_YAML = WEIGHTS_DIR / 'front_model_data.yaml'


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


def load_front_model_config():
    """Front camera model weights path + class names from front_model_data.yaml."""
    config = load_data_yaml(DEFAULT_DATA_YAML)
    return {
        'model_path': DEFAULT_MODEL_PATH,
        'data_yaml': DEFAULT_DATA_YAML,
        'class_names': config['names'],
        'nc': config['nc'],
    }

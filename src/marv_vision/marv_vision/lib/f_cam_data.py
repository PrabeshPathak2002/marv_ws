"""Front camera frame processing."""

from marv_vision.lib.model_config import load_front_model_config
from marv_vision.lib.yolo_inference import run_yolo_inference

_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_front_model_config()
    return _config


def process_f_cam(frame, model_path=None, conf=0.25):
    """Process front camera frame with YOLO. Returns list of detection dicts."""
    cfg = _get_config()
    path = model_path or cfg['model_path']
    return run_yolo_inference(frame, path, conf=conf)

"""Down camera frame processing."""

from pathlib import Path

from marv_vision.lib.yolo_inference import run_yolo_inference

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / 'weights'
DEFAULT_DOWN_MODEL = WEIGHTS_DIR / 'down_model.pt'


def process_d_cam(frame, model_path=None, conf=0.25):
    """Process down camera frame. Uses down_model.pt when weights exist."""
    path = Path(model_path) if model_path else DEFAULT_DOWN_MODEL
    if not path.is_file() or path.stat().st_size == 0:
        return []
    return run_yolo_inference(frame, path, conf=conf)

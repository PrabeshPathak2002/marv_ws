"""YOLO model inference utilities."""

from pathlib import Path

_model_cache = {}


def _get_model(model_path):
    path_key = str(Path(model_path).resolve())
    if path_key in _model_cache:
        return _model_cache[path_key]

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError(
            'ultralytics is required for YOLO inference. '
            'Install with: pip install ultralytics'
        ) from exc

    _model_cache[path_key] = YOLO(path_key)
    return _model_cache[path_key]


def run_yolo_inference(frame, model_path, conf=0.25):
    """Run YOLO inference on a BGR numpy frame. Returns list of detection dicts."""
    if frame is None:
        return []

    model = _get_model(model_path)
    results = model.predict(frame, conf=conf, verbose=False)
    detections = []

    names = model.names
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            cls_id = int(box.cls.item())
            detections.append({
                'class_id': cls_id,
                'class_name': names.get(cls_id, str(cls_id)),
                'confidence': float(box.conf.item()),
                'xyxy': box.xyxy.cpu().numpy().flatten().tolist(),
            })

    return detections

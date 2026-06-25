#!/usr/bin/env python3
"""Print YOLO detections on pool gate photos."""

from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL = Path(__file__).resolve().parents[1] / (
    'src/marv_vision/marv_vision/weights/front_model.pt')
SRC = Path('/home/eagleauv/Downloads/pictures')


def main():
    model = YOLO(str(MODEL))
    images = sorted(SRC.glob('*.JPG')) + sorted(SRC.glob('*.jpg'))
    hits = 0
    for path in images:
        results = model.predict(str(path), conf=0.20, imgsz=640, verbose=False)
        names = []
        for r in results:
            if r.boxes is None:
                continue
            names.extend(model.names[int(c)] for c in r.boxes.cls.tolist())
        has_gate = 'gate' in names
        has_obs = 'obstacle' in names
        if has_gate or has_obs:
            hits += 1
        print(f'{path.name}: {names}  gate={has_gate} obstacle={has_obs}')
    print(f'Detected gate/marker in {hits}/{len(images)} images')


if __name__ == '__main__':
    main()

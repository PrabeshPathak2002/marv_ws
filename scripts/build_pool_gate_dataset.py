#!/usr/bin/env python3
"""Build YOLO dataset from pool gate/marker photos and auto-label boxes."""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

CLASS_NAMES = ('gate', 'obstacle')


def _yolo_line(cls_id: int, box, w: int, h: int) -> str:
    x, y, bw, bh = box
    cx = (x + bw / 2.0) / w
    cy = (y + bh / 2.0) / h
    return f'{cls_id} {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}'


def _largest_gate_box(mask: np.ndarray, w: int, h: int):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_score = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        area_frac = area / float(w * h)
        if area_frac < 0.08 or area_frac > 0.78:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw < w * 0.28 or bh < h * 0.22:
            continue
        if x < 5 and y < 5 and bw > w * 0.95 and bh > h * 0.95:
            continue
        aspect = bw / max(bh, 1)
        if aspect < 0.55 or aspect > 2.8:
            continue
        score = area + bw * 0.25
        if score > best_score:
            best_score = score
            best = (x, y, bw, bh)
    return best


def _best_marker_box(img: np.ndarray, gate_box=None):
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    orange = cv2.inRange(hsv, (5, 90, 90), (28, 255, 255))
    white = cv2.inRange(hsv, (0, 0, 175), (180, 70, 255))
    tan = cv2.inRange(hsv, (8, 35, 80), (28, 180, 220))
    mask = cv2.bitwise_or(cv2.bitwise_or(orange, white), tan)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), 2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_score = 0.0
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bh < h * 0.10 or bw > w * 0.20:
            continue
        if bh < bw * 1.1:
            continue
        cx = x + bw / 2.0
        if gate_box is not None:
            gx, gy, gw, gh = gate_box
            if not (gx - 0.15 * w < cx < gx + gw + 0.15 * w):
                continue
            if y + bh < gy + gh * 0.05:
                continue
        score = bh * bh
        if score > best_score:
            best_score = score
            best = (x, y, bw, bh)
    return best


def auto_label_image(img: np.ndarray):
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    dark_hsv = cv2.inRange(hsv, (0, 0, 0), (180, 255, 88))
    dark_gray = cv2.inRange(gray, 0, 80)
    edges = cv2.Canny(gray, 40, 120)
    gate_mask = cv2.bitwise_or(dark_hsv, dark_gray)
    gate_mask = cv2.bitwise_or(gate_mask, edges)
    gate_mask = cv2.morphologyEx(
        gate_mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8), 2)
    gate_mask = cv2.dilate(gate_mask, np.ones((5, 5), np.uint8), 1)

    labels = []
    gate = _largest_gate_box(gate_mask, w, h)
    if gate is not None:
        labels.append(('gate', gate))
    marker = _best_marker_box(img, gate)
    if marker is not None:
        labels.append(('obstacle', marker))
    return labels


# Manual YOLO-normalized boxes (cx, cy, w, h) for images auto-label misses.
MANUAL_OVERRIDES = {
    'DJI_20260624190923_0199_D': [('gate', 0.50, 0.52, 0.72, 0.62), ('obstacle', 0.50, 0.58, 0.06, 0.28)],
    'DJI_20260624190833_0195_D': [('gate', 0.50, 0.50, 0.78, 0.55)],
    'DJI_20260624190641_0193_D': [('gate', 0.50, 0.48, 0.70, 0.50)],
    'DJI_20260624190849_0198_D': [('gate', 0.50, 0.50, 0.75, 0.55), ('obstacle', 0.50, 0.55, 0.05, 0.25)],
    'DJI_20260624190957_0203_D': [('gate', 0.50, 0.50, 0.72, 0.58), ('obstacle', 0.50, 0.56, 0.05, 0.22)],
    'DJI_20260624190646_0194_D': [('gate', 0.50, 0.50, 0.68, 0.52)],
    'DJI_20260624190948_0202_D': [('gate', 0.50, 0.50, 0.70, 0.55)],
    'DJI_20260624190938_0200_D': [('gate', 0.50, 0.50, 0.72, 0.55)],
    'DJI_20260624190843_0196_D': [('gate', 0.50, 0.50, 0.74, 0.55)],
    'DJI_20260624190639_0192_D': [('gate', 0.50, 0.48, 0.68, 0.50)],
    'DJI_20260624190513_0188_D': [('obstacle', 0.50, 0.55, 0.05, 0.35)],
    'DJI_20260624190534_0189_D': [('obstacle', 0.52, 0.50, 0.04, 0.28)],
    'DJI_20260624190536_0190_D': [('obstacle', 0.51, 0.52, 0.05, 0.30)],
    'DJI_20260624190942_0201_D': [('obstacle', 0.50, 0.54, 0.05, 0.26)],
    'DJI_20260624190552_0191_D': [('gate', 0.50, 0.50, 0.65, 0.50)],
    'DJI_20260624190847_0197_D': [('gate', 0.50, 0.50, 0.70, 0.52)],
}


def _manual_labels(stem: str, w: int, h: int):
    rows = MANUAL_OVERRIDES.get(stem)
    if not rows:
        return []
    out = []
    for name, cx, cy, bw, bh in rows:
        box_w = int(bw * w)
        box_h = int(bh * h)
        x = int(cx * w - box_w / 2)
        y = int(cy * h - box_h / 2)
        out.append((name, (x, y, box_w, box_h)))
    return out


def build_dataset(src_dir: Path, out_dir: Path, val_frac: float = 0.2, seed: int = 42):
    images = sorted(src_dir.glob('*.JPG')) + sorted(src_dir.glob('*.jpg'))
    if not images:
        raise SystemExit(f'No images in {src_dir}')

    random.Random(seed).shuffle(images)
    val_count = max(1, int(len(images) * val_frac))
    val_set = set(images[:val_count])

    for split in ('train', 'val'):
        (out_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (out_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    summary = []
    for src in images:
        split = 'val' if src in val_set else 'train'
        img = cv2.imread(str(src))
        if img is None:
            continue
        h, w = img.shape[:2]
        scale = 1280.0 / max(w, h)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
            h, w = img.shape[:2]

        stem = src.stem
        labels = _manual_labels(stem, w, h) or auto_label_image(img)
        out_img = out_dir / split / 'images' / f'{stem}.jpg'
        out_lbl = out_dir / split / 'labels' / f'{stem}.txt'
        cv2.imwrite(str(out_img), img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        lines = []
        for name, box in labels:
            cls_id = CLASS_NAMES.index(name)
            x, y, bw, bh = box
            if scale < 1.0:
                pass  # boxes computed on resized image
            lines.append(_yolo_line(cls_id, box, w, h))
        out_lbl.write_text('\n'.join(lines) + ('\n' if lines else ''))
        summary.append((src.name, split, [n for n, _ in labels]))

    yaml_path = out_dir / 'pool_gate_data.yaml'
    yaml_path.write_text(
        '\n'.join([
            f'path: {out_dir.resolve()}',
            'train: train/images',
            'val: val/images',
            'nc: 2',
            "names: ['gate', 'obstacle']",
            '',
        ]))
    print('Dataset:', out_dir)
    for row in summary:
        print(' ', row)
    return out_dir / 'pool_gate_data.yaml'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', default='/home/eagleauv/Downloads/pictures')
    parser.add_argument(
        '--out',
        default='/home/eagleauv/marv_ws/src/marv_vision/marv_vision/weights/pool_gate_dataset')
    args = parser.parse_args()
    build_dataset(Path(args.src), Path(args.out))


if __name__ == '__main__':
    main()

#!/usr/bin/env bash
# Train pre-qual YOLO model (black_gate + yellow_pole).
# Dataset paths must match prequal_model_data.yaml.
set -euo pipefail

WS="${HOME}/marv_ws"
WEIGHTS="${WS}/src/marv_vision/marv_vision/weights"
cd "${WEIGHTS}"

if ! python3 -c "from ultralytics import YOLO" 2>/dev/null; then
  echo "Install: pip3 install 'numpy<2' ultralytics"
  exit 1
fi

echo "Training from ${WEIGHTS}/prequal_model_data.yaml"
yolo detect train \
  data=prequal_model_data.yaml \
  model=yolov8n.pt \
  imgsz=640 \
  epochs="${1:-100}" \
  batch="${2:-8}" \
  patience=20 \
  project=prequal_runs \
  name=v1

cp -f prequal_runs/v1/weights/best.pt prequal_model.pt
echo "Installed: ${WEIGHTS}/prequal_model.pt"
echo "Rebuild: cd ${WS} && colcon build --packages-select marv_vision"

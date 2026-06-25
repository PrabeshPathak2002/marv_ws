#!/usr/bin/env bash
# Train pool gate + marker YOLO from ~/Downloads/pictures (or --src).
set -euo pipefail

WS="${HOME}/marv_ws"
WEIGHTS="${WS}/src/marv_vision/marv_vision/weights"
SRC="${1:-${HOME}/Downloads/pictures}"
EPOCHS="${2:-80}"
BATCH="${3:-4}"

python3 "${WS}/scripts/build_pool_gate_dataset.py" --src "${SRC}"

if ! python3 -c "from ultralytics import YOLO" 2>/dev/null; then
  echo "Install: pip3 install 'numpy<2' ultralytics"
  exit 1
fi

cd "${WEIGHTS}"
echo "Training pool gate model (${EPOCHS} epochs)..."
yolo detect train \
  data=pool_gate_dataset/pool_gate_data.yaml \
  model=yolov8n.pt \
  imgsz=640 \
  epochs="${EPOCHS}" \
  batch="${BATCH}" \
  patience=25 \
  augment=true \
  mosaic=1.0 \
  project=pool_gate_runs \
  name=v1

cp -f pool_gate_runs/v1/weights/best.pt front_model.pt
cp -f pool_gate_dataset/pool_gate_data.yaml front_model_data.yaml

# Sync into install tree for runtime without rebuild.
INSTALL_W="${WS}/install/marv_vision/lib/python3.10/site-packages/marv_vision/weights"
if [[ -d "${INSTALL_W}" ]]; then
  cp -f front_model.pt front_model_data.yaml "${INSTALL_W}/"
fi

echo "Installed: ${WEIGHTS}/front_model.pt (classes: gate, obstacle)"
echo "Validate: python3 ${WS}/scripts/validate_pool_gate_model.py"

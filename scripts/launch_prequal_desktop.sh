#!/usr/bin/env bash
# Desktop launcher: in-water pre-qual with Colab YOLO model + vision debug.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
cd "${MARV_WS}"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash" 2>/dev/null || true
set -u

echo "=============================================="
echo "  Marv Pre-Qual — pool (YOLO gate + marker)"
echo "=============================================="
echo ""

if [[ -x "${MARV_WS}/scripts/sync_install.sh" ]]; then
  "${MARV_WS}/scripts/sync_install.sh"
fi

if curl -sf --connect-timeout 1 http://127.0.0.1:6040/v1/mavlink >/dev/null 2>&1; then
  echo "[OK] BlueOS mavlink-router detected"
elif pgrep -x mavlink-routerd >/dev/null 2>&1; then
  echo "[OK] mavlink-router already running"
else
  echo "Starting mavlink-router on ARK FPV..."
  if fuser /dev/ttyACM0 >/dev/null 2>&1 || fuser /dev/ark_fpv >/dev/null 2>&1; then
    echo "ERROR: FCU serial port busy — close QGroundControl direct USB."
    fuser -v /dev/ttyACM0 /dev/ark_fpv 2>&1 || true
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
  fi
  nohup "${MARV_WS}/start_mavlink_router.sh" >/tmp/marv-mavlink-router.log 2>&1 &
  for _ in $(seq 1 12); do
    sleep 1
    pgrep -x mavlink-routerd >/dev/null && break
  done
  if ! pgrep -x mavlink-routerd >/dev/null; then
    echo "ERROR: mavlink-router failed. See /tmp/marv-mavlink-router.log"
    tail -15 /tmp/marv-mavlink-router.log 2>/dev/null || true
    read -r -p "Press Enter to exit..."
    exit 1
  fi
  echo "[OK] mavlink-router running"
fi

echo ""
echo "Launching in-water pre-qual (YOLO, vision debug, ALT_HOLD)..."
echo "Ctrl+C to stop, or use: Marv Stop Thrusters desktop icon"
echo ""

exec "${MARV_WS}/scripts/run_prequal_pool.sh"

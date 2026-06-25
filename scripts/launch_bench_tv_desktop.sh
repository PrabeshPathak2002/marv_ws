#!/usr/bin/env bash
# Desktop launcher: TV bench test (vision + simulated Ping + thruster control).
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
cd "${MARV_WS}"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash" 2>/dev/null || true
set -u

echo "=============================================="
echo "  Marv Bench TV — vision + simulated Ping"
echo "=============================================="
echo ""

if [[ -x "${MARV_WS}/scripts/sync_install.sh" ]]; then
  "${MARV_WS}/scripts/sync_install.sh"
fi

if ! pgrep -x mavlink-routerd >/dev/null 2>&1; then
  echo "Starting mavlink-router..."
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
else
  echo "[OK] mavlink-router already running"
fi

echo ""
echo "Launching bench TV stack (STABILIZE, f_cam debug, simulated range)..."
echo "Ctrl+C to stop, or run: ~/marv_ws/scripts/stop_marv_thrusters.sh"
echo ""

exec "${MARV_WS}/scripts/run_bench_tv.sh"

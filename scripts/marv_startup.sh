#!/usr/bin/env bash
# Marv AUV boot helpers — free Ping serial port and start ping_sonar_ros.
set -eo pipefail

MARV_WS="${HOME}/marv_ws"
LOG_DIR="${HOME}/.local/log"
LOG_FILE="${LOG_DIR}/marv_ping.log"

mkdir -p "${LOG_DIR}"

if [[ ! -f "${MARV_WS}/install/setup.bash" ]]; then
  echo "marv_startup: ${MARV_WS} not built — run: cd ~/marv_ws && colcon build"
  exit 1
fi

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

# Release /dev/ttyUSB0 from companion ping/bridge processes if present.
"${MARV_WS}/scripts/free_ping_port.sh" || true

if pgrep -f '[p]ing1d_node' >/dev/null 2>&1; then
  echo "marv_startup: ping1d_node already running"
  exit 0
fi

echo "marv_startup: launching Ping1D driver..."
nohup ros2 launch marv_bringup ping.launch.py >>"${LOG_FILE}" 2>&1 &
disown
echo "marv_startup: log → ${LOG_FILE}"

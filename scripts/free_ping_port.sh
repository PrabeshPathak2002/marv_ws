#!/usr/bin/env bash
# Stop companion ping/bridge processes that hold /dev/ttyUSB0 (Ping1D).
# Safe to run if you use marv_ws ping_sonar_ros directly over USB serial.
set -eo pipefail

PING_DEV="$(ls /dev/serial/by-id/usb-FTDI_*-if00-port0 2>/dev/null | head -1 || echo /dev/ttyUSB0)"

echo "Ping device: ${PING_DEV}"

if python3 -c "import os; os.open('${PING_DEV}', os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)" 2>/dev/null; then
  echo "Port is already free — nothing to stop."
  exit 0
fi

echo ""
echo "Port is busy. Stopping known Ping port holders..."

stop_pattern() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "${pattern}" 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "  stopping: ${pattern}"
    # shellcheck disable=SC2086
    kill ${pids} 2>/dev/null || true
  fi
}

stop_pattern '/home/pi/services/ping/main.py'
stop_pattern 'bridges.*9090'
stop_pattern 'run-service ping'

sleep 1

if python3 -c "import os; os.open('${PING_DEV}', os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)" 2>/dev/null; then
  echo ""
  echo "OK: ${PING_DEV} is now available for ping_sonar_ros."
  exit 0
fi

echo ""
echo "WARN: port still busy. Remaining holders:"
fuser -v "${PING_DEV}" 2>&1 || true
lsof "${PING_DEV}" 2>/dev/null || true
echo ""
echo "Stop the process above manually, then run:"
echo "  ros2 launch marv_bringup ping.launch.py"
exit 1

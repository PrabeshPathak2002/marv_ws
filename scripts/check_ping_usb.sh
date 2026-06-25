#!/usr/bin/env bash
# Quick check for Blue Robotics Ping1D on Jetson USB.
set -eo pipefail

echo "=== USB serial by-id (stable paths) ==="
if [[ -d /dev/serial/by-id ]]; then
  ls -la /dev/serial/by-id/
else
  echo "(no /dev/serial/by-id — is Ping plugged in?)"
fi

echo ""
echo "=== Legacy tty nodes ==="
ls -l /dev/ttyUSB* 2>/dev/null || echo "(no /dev/ttyUSB*)"
ls -l /dev/ttyACM* 2>/dev/null || echo "(no /dev/ttyACM*)"
echo "FTDI ttyUSB* = Ping1D | ArduPilot ttyACM* = ARK FPV"

echo ""
echo "=== Resolved paths ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/resolve_serial_devices.sh" | sed -n '/=== Resolved device paths ===/,$p' | head -n 8

echo ""
echo "=== dialout group ==="
groups | grep -q dialout && echo "OK: in dialout" || echo "WARN: add user to dialout"

echo ""
PING_DEV="/dev/ping_sonar"
if [[ ! -e "${PING_DEV}" ]]; then
  PING_DEV="$(ls /dev/serial/by-id/usb-FTDI_*-if00-port0 2>/dev/null | head -1 || echo /dev/ttyUSB0)"
fi
echo "=== Ping serial port (${PING_DEV}) ==="
if python3 -c "import os; os.open('${PING_DEV}', os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)" 2>/dev/null; then
  echo "Available — ready for: ros2 launch marv_bringup ping.launch.py"
else
  echo "BUSY — another process holds the Ping port."
  pgrep -af 'services/ping/main.py|bridges.*9090' 2>/dev/null || true
  echo "Free it with: ~/marv_ws/scripts/free_ping_port.sh"
fi

if [[ -f "${HOME}/marv_ws/install/setup.bash" ]]; then
  set +u
  source /opt/ros/humble/setup.bash
  source "${HOME}/marv_ws/install/setup.bash"
  set -u
  echo ""
  echo "=== ROS topics (if driver running) ==="
  timeout 2 ros2 topic list 2>/dev/null | grep -E "ping|range" || echo "(start: ros2 launch marv_bringup ping.launch.py)"
fi

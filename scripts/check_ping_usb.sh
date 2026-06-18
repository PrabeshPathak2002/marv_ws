#!/usr/bin/env bash
# Quick check for Blue Robotics Ping1D on Jetson USB.
set -euo pipefail

echo "=== USB serial devices ==="
ls -l /dev/ttyUSB* 2>/dev/null || echo "(no /dev/ttyUSB* — is Ping plugged in?)"
ls -l /dev/ttyACM* 2>/dev/null || true
echo "(ttyACM* = ARK FPV, ttyUSB* = Ping1D typically)"

echo ""
echo "=== dialout group ==="
groups | grep -q dialout && echo "OK: in dialout" || echo "WARN: add user to dialout"

if [[ -f "${HOME}/marv_ws/install/setup.bash" ]]; then
  source /opt/ros/humble/setup.bash
  source "${HOME}/marv_ws/install/setup.bash"
  echo ""
  echo "=== ROS topics (if driver running) ==="
  timeout 2 ros2 topic list 2>/dev/null | grep -E "ping|range" || echo "(start: ros2 launch marv_bringup ping.launch.py)"
fi

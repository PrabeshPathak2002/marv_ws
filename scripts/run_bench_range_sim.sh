#!/usr/bin/env bash
# Simulated forward Ping for TV / bench pre-qual testing.
# Maps gate vision bbox area -> range; auto-clears pass_gate after a few seconds.
set -eo pipefail

MARV_WS="${HOME}/marv_ws"
MODE="${1:-vision}"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

if pgrep -f mavlink_ping_bridge >/dev/null 2>&1; then
  echo "Stopping mavlink_ping_bridge (real FCU Ping) — bench sim replaces it."
  pkill -f mavlink_ping_bridge || true
  sleep 1
fi

echo "=== Bench range simulator ==="
echo "  mode=${MODE}"
echo "  topic=/mavros/distance_sensor/lidar -> /sensors/range_forward"
echo "  vision: larger gate on TV = closer range"
echo "  pass_gate: auto ramps to 3.5 m after 2.5 s to complete gate pass"
echo ""
echo "Monitor: ros2 topic echo /sensors/range_forward"
echo ""

exec ros2 run marv_bringup bench_range_sim --ros-args -p "mode:=${MODE}"

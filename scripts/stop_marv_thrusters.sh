#!/usr/bin/env bash
# Stop Marv bench/pre-qual stack and disarm thrusters.
set -eo pipefail

MARV_WS="${HOME}/marv_ws"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash" 2>/dev/null || true
set -u

echo "=== Stopping Marv thrusters ==="

if ros2 topic list 2>/dev/null | grep -q '/mavros/state'; then
  echo "Disarming FCU..."
  "${MARV_WS}/scripts/arm_vehicle.sh" false disarm 2>/dev/null || true
fi

echo "Stopping ROS control stack..."
for pat in prequal_bringup.launch.py bench_range_sim run_bench_range_sim \
           f_cam_node mission_planner_node master_control_node ardusub_node \
           mavros_node fcu_setup_node mapping_node mavlink_ping_bridge; do
  pkill -f "${pat}" 2>/dev/null || true
done
sleep 2

if pgrep -f prequal_bringup.launch.py >/dev/null 2>&1; then
  pkill -9 -f prequal_bringup.launch.py 2>/dev/null || true
  sleep 1
fi

echo "Done. mavlink-router left running (QGC link); stop with: pkill mavlink-routerd"
pgrep -af 'prequal_bringup|bench_range_sim|ardusub_node' || echo "[OK] control stack stopped"

#!/usr/bin/env bash
# TV bench: gate video on a screen + simulated Ping + MANUAL mode for horizontal thrusters.
set -eo pipefail

MARV_WS="${HOME}/marv_ws"

echo "Stopping stale Marv / ROS nodes..."
for pat in prequal_bringup.launch.py bench_range_sim f_cam_node mission_planner_node \
           master_control_node ardusub_node mavros_node fcu_setup_node mapping_node \
           mavlink_ping_bridge; do
  pkill -f "${pat}" 2>/dev/null || true
done
sleep 3

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

if ! pgrep -x mavlink-routerd >/dev/null 2>&1; then
  echo "Starting mavlink-router..."
  nohup "${MARV_WS}/start_mavlink_router.sh" >/tmp/marv-mavlink-router.log 2>&1 &
  sleep 3
fi

echo "Starting bench range simulator..."
nohup "${MARV_WS}/scripts/run_bench_range_sim.sh" vision >/tmp/bench_range_sim.log 2>&1 &
sleep 2

echo "=== Bench TV pre-qual ==="
echo "  STABILIZE mode + hold_depth_with_autopilot (FCU vertical, ROS surge/sway/yaw)"
echo "  plan=bench_tv_plan (find_gate -> traverse -> pass, loop)"
echo "  camera=/dev/video0  simulated Ping from gate bbox size"
echo ""

exec ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:=true \
  command_backend:=mavros_rc \
  auto_arm:=true \
  fcu_mode:=STABILIZE \
  hold_depth_with_autopilot:=true \
  use_ping_driver:=false \
  use_mapping:=false \
  camera_device:=/dev/video0 \
  plan_file:="${MARV_WS}/install/marv_bringup/share/marv_bringup/config/plans/bench_tv_plan.yaml" \
  publish_debug_image:=true \
  show_debug_window:=true \
  depth_hold_enabled:=false \
  target_depth_m:=1.0 \
  ping_range_topic:=/mavros/distance_sensor/lidar \
  ping_topic:=/sensors/range_forward

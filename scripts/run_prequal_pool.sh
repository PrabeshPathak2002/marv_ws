#!/usr/bin/env bash
# In-water RoboSub pre-qual: Colab YOLO (gate + obstacle), real Ping, mapping.
set -eo pipefail

MARV_WS="${HOME}/marv_ws"
MODEL="${MARV_WS}/install/marv_vision/lib/python3.10/site-packages/marv_vision/weights/front_model.pt"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

if [[ -x "${MARV_WS}/scripts/sync_install.sh" ]]; then
  "${MARV_WS}/scripts/sync_install.sh" >/dev/null 2>&1 || true
fi

if ! pgrep -x mavlink-routerd >/dev/null 2>&1; then
  echo "Starting mavlink-router..."
  nohup "${MARV_WS}/start_mavlink_router.sh" >/tmp/marv-mavlink-router.log 2>&1 &
  sleep 4
fi

echo "=== Marv pre-qual (in water) ==="
echo "  YOLO: ${MODEL}"
echo "  classes: gate, obstacle"
echo "  mode: ALT_HOLD  control: mavros_rc  auto_arm: true"
echo "  camera: /dev/explore_hd  ping: FCU MAVROS"
echo ""
echo "Monitor: ros2 topic echo /mission_planner/status"
echo "Vision:  ros2 topic echo /f_cam/detections"
echo "Stop:    ~/marv_ws/scripts/stop_marv_thrusters.sh"
echo ""

export DISPLAY="${DISPLAY:-:0}"
exec ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:=true \
  command_backend:=mavros_rc \
  auto_arm:=true \
  fcu_mode:=ALT_HOLD \
  hold_depth_with_autopilot:=true \
  use_ping_driver:=false \
  use_mapping:=true \
  camera_device:=/dev/explore_hd \
  vision_profile:=default \
  model_path:="${MODEL}" \
  publish_debug_image:=true \
  show_debug_window:=true \
  depth_hold_enabled:=true \
  target_depth_m:=1.0 \
  ping_range_topic:=/mavros/distance_sensor/lidar \
  ping_topic:=/sensors/range_forward

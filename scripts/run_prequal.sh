#!/usr/bin/env bash
# Launch full Marv pre-qual stack (MAVROS + vision + mission planner + Ping).
set -eo pipefail

ENABLE_CONTROL="${1:-false}"
COMMAND_BACKEND="${2:-log_only}"

if [[ "${ENABLE_CONTROL}" == "true" ]]; then
  COMMAND_BACKEND="${COMMAND_BACKEND:-mavros_rc}"
fi

MARV_WS="${HOME}/marv_ws"
set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

# Ping driver is started by marv_startup.sh; skip second instance unless not running.
USE_PING_DRIVER="false"
if ! pgrep -f '[p]ing1d_node' >/dev/null 2>&1; then
  USE_PING_DRIVER="true"
  "${MARV_WS}/scripts/free_ping_port.sh" || true
fi

echo "=== Marv pre-qual ==="
echo "  enable_control=${ENABLE_CONTROL}"
echo "  command_backend=${COMMAND_BACKEND}"
echo "  camera_device=/dev/video2 (exploreHD)"
echo "  use_ping_driver=${USE_PING_DRIVER}"
echo "  use_mapping=true (map_pose for transit)"
echo ""
echo "Monitor: ros2 topic echo /mission_planner/status"
echo "Vision:  ros2 topic echo /f_cam/detections"
echo "Ping:    ros2 topic echo /ping1d/range --once"
echo ""

exec ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:="${ENABLE_CONTROL}" \
  command_backend:="${COMMAND_BACKEND}" \
  use_ping_driver:="${USE_PING_DRIVER}" \
  use_mapping:=true \
  camera_device:=/dev/video2 \
  target_depth_m:=1.0

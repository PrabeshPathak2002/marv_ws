#!/usr/bin/env bash
# Launch full Marv pre-qual stack (MAVROS + vision + mission planner + FCU Ping).
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

# System MAVROS (apt) takes precedence over legacy .ros_apt_overlay.
_strip_path() {
  local var="$1"
  local val="${!var:-}"
  [[ -z "${val}" ]] && return
  export "${var}=$(echo "${val}" | tr ':' '\n' | grep -v "${MARV_WS}/.ros_apt_overlay" | paste -sd: -)"
}
for _v in AMENT_PREFIX_PATH CMAKE_PREFIX_PATH LD_LIBRARY_PATH PYTHONPATH; do
  _strip_path "${_v}"
done

if ! pgrep -x mavlink-routerd >/dev/null 2>&1; then
  echo "Starting mavlink-router (ARK FPV USB -> udp://@127.0.0.1:14555)..."
  nohup "${MARV_WS}/start_mavlink_router.sh" >/tmp/marv-mavlink-router.log 2>&1 &
  for _ in $(seq 1 15); do
    sleep 1
    pgrep -x mavlink-routerd >/dev/null && break
  done
  if ! pgrep -x mavlink-routerd >/dev/null; then
    echo "ERROR: mavlink-router failed. See /tmp/marv-mavlink-router.log"
    tail -15 /tmp/marv-mavlink-router.log 2>/dev/null || true
    exit 1
  fi
fi

echo "=== Marv pre-qual ==="
echo "  enable_control=${ENABLE_CONTROL}"
echo "  command_backend=${COMMAND_BACKEND}"
echo "  camera_device=/dev/explore_hd (exploreHD MJPEG)"
echo "  ping=FCU MAVROS (/mavros/distance_sensor/lidar -> /sensors/range_forward)"
echo "  use_mapping=true (map_pose for transit)"
echo ""
echo "Monitor: ros2 topic echo /mission_planner/status"
echo "Vision:  ros2 topic echo /f_cam/detections"
echo "Ping:    ros2 topic echo /sensors/range_forward --once"
echo ""

exec ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:="${ENABLE_CONTROL}" \
  command_backend:="${COMMAND_BACKEND}" \
  auto_arm:="${ENABLE_CONTROL}" \
  use_ping_driver:=false \
  use_mapping:=true \
  camera_device:=/dev/explore_hd \
  target_depth_m:=1.0 \
  ping_range_topic:=/mavros/distance_sensor/lidar \
  ping_topic:=/sensors/range_forward

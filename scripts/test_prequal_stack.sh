#!/usr/bin/env bash
# Quick pre-qual hardware + ROS topic health check (stack must be running).
set -eo pipefail

MARV_WS="${HOME}/marv_ws"
set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u
for _v in AMENT_PREFIX_PATH CMAKE_PREFIX_PATH LD_LIBRARY_PATH PYTHONPATH; do
  val="${!_v:-}"
  [[ -n "${val}" ]] && export "${_v}=$(echo "${val}" | tr ':' '\n' | grep -v "${MARV_WS}/.ros_apt_overlay" | paste -sd: -)"
done

PASS=0
FAIL=0
WARN=0

ok() { echo "  [PASS] $*"; PASS=$((PASS + 1)); }
bad() { echo "  [FAIL] $*"; FAIL=$((FAIL + 1)); }
warn() { echo "  [WARN] $*"; WARN=$((WARN + 1)); }

echo "=== Marv pre-qual stack test ==="
echo ""

echo "--- Hardware ---"
if ls /dev/serial/by-id/usb-ArduPilot_ARK_FPV* >/dev/null 2>&1; then ok "ARK FPV USB present"; else bad "ARK FPV USB missing"; fi
if [[ -e /dev/video0 ]] || [[ -e /dev/explore_hd ]]; then ok "exploreHD V4L2 present"; else bad "No camera device"; fi
if pgrep -x mavlink-routerd >/dev/null; then ok "mavlink-router running"; else bad "mavlink-router not running"; fi
if ls /dev/serial/by-id/usb-FTDI_* >/dev/null 2>&1; then
  warn "Ping USB present (optional — FCU MAVLink path is default)"
else
  ok "Ping via FCU MAVLink (no USB Ping expected)"
fi

echo ""
echo "--- ROS nodes ---"
for n in mavros mavlink_ping_bridge ardusub_node f_cam_node mapping_node master_control_node mission_planner_node; do
  if ros2 node list 2>/dev/null | grep -q "/${n}"; then ok "node /${n}"; else bad "node /${n} not running"; fi
done
if ros2 node list 2>/dev/null | grep -q ping1d_node; then
  warn "ping1d_node running (USB driver — FCU path usually uses use_ping_driver:=false)"
fi

echo ""
echo "--- Topics (5s sample) ---"
sample() {
  local topic="$1" label="$2"
  if timeout 5 ros2 topic echo "${topic}" --once >/tmp/marv_test_msg 2>/dev/null; then
    ok "${label} (${topic})"
    return 0
  fi
  if ros2 topic info "${topic}" 2>/dev/null | grep -q 'Publisher count: [1-9]'; then
    warn "${label} has publisher but no message in 5s (${topic})"
  else
    bad "${label} no data (${topic})"
  fi
}

sample /mavros/distance_sensor/lidar "FCU Ping (MAVLink bridge)"
sample /sensors/range_forward "Forward range (ardusub)"
sample /mavros/mavros/data "MAVROS IMU"
sample /sensors/pose "FCU pose"
sample /sensors/map_pose "Map pose"
sample /f_cam/detections "Vision detections"
sample /mission_planner/status "Mission planner"

echo ""
echo "--- Summary: ${PASS} pass, ${WARN} warn, ${FAIL} fail ---"
if [[ "${FAIL}" -gt 0 ]]; then exit 1; fi

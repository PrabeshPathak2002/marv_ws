#!/usr/bin/env bash
# Verify full Gazebo prequal sim stack (run while launch is up).
set -eo pipefail
set +u
source /opt/ros/humble/setup.bash
source /home/eagleauv/marv_ws/install/setup.bash
source /home/eagleauv/marv_ws/scripts/ensure_mavros.sh 2>/dev/null || true
set -u

PASS=0
FAIL=0
check() {
  local name="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    FAIL=$((FAIL + 1))
  fi
}

check "gz sim running" "pgrep -f 'gz sim.*marv_prequal_full'"
check "marv_auv in gz" "gz topic -l | grep -q /model/marv_auv/"
check "explore_hd camera" "gz topic -l | grep -q /explore_hd"
check "gz_image_bridge" "ros2 node list | grep -qE 'gz_image_bridge|gazebo_front_camera_bridge'"
check "ROS camera topic" "timeout 4 ros2 topic echo /gazebo/f_cam/image_raw --once"
check "mavros node" "ros2 node list | grep -q mavros"
check "ardusub_node" "ros2 node list | grep -q ardusub_node"
check "f_cam_node" "ros2 node list | grep -q f_cam_node"

echo "---"
echo "Results: ${PASS} passed, ${FAIL} failed"
exit $(( FAIL > 0 ? 1 : 0 ))

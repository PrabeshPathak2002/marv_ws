#!/usr/bin/env bash
# Quick check for Blue Robotics / DWE exploreHD USB camera on Jetson.
set -euo pipefail

echo "=== V4L2 devices ==="
if command -v v4l2-ctl >/dev/null 2>&1; then
  v4l2-ctl --list-devices || true
else
  echo "Install v4l-utils: sudo apt install v4l-utils"
  ls -l /dev/video* 2>/dev/null || echo "(no /dev/video* — is exploreHD plugged in?)"
fi

echo ""
echo "=== exploreHD notes ==="
echo "Each exploreHD creates ~4 /dev/video* nodes."
echo "  MJPEG (OpenCV): usually first in group, e.g. /dev/video0"
echo "  H.264 stream:   usually third, e.g. /dev/video2"
echo "Marv f_cam_node defaults to /dev/video0 @ 1280x720 MJPG."

DEVICE="${1:-/dev/explore_hd}"
echo ""
echo "=== Test capture on ${DEVICE} ==="
if command -v gst-launch-1.0 >/dev/null 2>&1 && [[ -e "${DEVICE}" ]]; then
  timeout 5 gst-launch-1.0 -q v4l2src device="${DEVICE}" num-buffers=30 \
    ! "image/jpeg,width=1280,height=720,framerate=30/1" ! jpegdec ! fakesink \
    && echo "OK: MJPEG frames received on ${DEVICE}" \
    || echo "WARN: no MJPEG on ${DEVICE} — try another node from v4l2-ctl --list-devices"
elif [[ -e "${DEVICE}" ]]; then
  echo "Device exists. Install gstreamer1.0-tools for live test, or run f_cam_node."
else
  echo "Device ${DEVICE} not found."
fi

if [[ -f "${HOME}/marv_ws/install/setup.bash" ]]; then
  source /opt/ros/humble/setup.bash
  source "${HOME}/marv_ws/install/setup.bash"
  echo ""
  echo "=== ROS (if f_cam_node running) ==="
  timeout 2 ros2 topic list 2>/dev/null | grep f_cam || \
    echo "(start: ros2 run marv_vision f_cam_node --ros-args -p vision_profile:=prequal_cv)"
fi

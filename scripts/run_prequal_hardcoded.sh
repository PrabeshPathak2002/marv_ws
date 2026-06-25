#!/usr/bin/env bash
# Pre-qual with hardcoded paths — no camera, no ping (bench/minimal hardware).
set -eo pipefail

ENABLE_CONTROL="${1:-true}"
COMMAND_BACKEND="${2:-mavros_rc}"

MARV_WS="${HOME}/marv_ws"
set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash"
set -u

"${MARV_WS}/scripts/install_python_packages.sh" >/dev/null 2>&1 || true
"${MARV_WS}/scripts/sync_install.sh" >/dev/null 2>&1 || true

# Bench (mavlink-router): udp://@127.0.0.1:14555
# BlueOS companion:           udp://@127.0.0.1:14001
if curl -sf --connect-timeout 1 http://127.0.0.1:6040/v1/mavlink >/dev/null 2>&1; then
  FCU_URL="${FCU_URL:-udp://@127.0.0.1:14001}"
  BRIDGE_NOTE="BlueOS mavlink-router on /dev/ttyACM0"
else
  FCU_URL="${FCU_URL:-udp://@127.0.0.1:14555}"
  BRIDGE_NOTE="Run ~/marv_ws/start_mavlink_router.sh first (close QGC direct USB)"
fi

echo "=== Marv pre-qual (hardcoded, no camera/ping) ==="
echo "  enable_control=${ENABLE_CONTROL}"
echo "  command_backend=${COMMAND_BACKEND}"
echo "  fcu_url=${FCU_URL}"
echo "  use_vision=false  use_ping_driver=false  use_mapping=false"
echo ""
echo "  fcu_mode=${FCU_MODE:-ALT_HOLD}  auto_arm=${AUTO_ARM:-true}"
echo "  hold_depth_with_autopilot=true (FCU holds depth)"
echo ""
echo "  ${BRIDGE_NOTE}"
echo "  Monitor: ros2 topic echo /mission_planner/status"
echo ""

exec ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:="${ENABLE_CONTROL}" \
  command_backend:="${COMMAND_BACKEND}" \
  use_vision:=false \
  use_ping_driver:=false \
  use_mapping:=false \
  fcu_url:="${FCU_URL}" \
  fcu_mode:="${FCU_MODE:-ALT_HOLD}" \
  auto_arm:="${AUTO_ARM:-true}" \
  hold_depth_with_autopilot:=true \
  target_depth_m:=1.0

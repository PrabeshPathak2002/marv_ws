#!/usr/bin/env bash
# Bench stack: Jetson + ARK FPV only (no camera, ping, BlueOS).
#
# Usage:
#   1) Close QGroundControl if it has a direct USB link to the FCU.
#   2) ~/marv_ws/scripts/bench_fcu_stack.sh          # telemetry + ROS
#   3) ~/marv_ws/scripts/bench_fcu_stack.sh test     # health check only
#
# QGC on laptop: UDP to <jetson-ip>:14550 (do NOT use direct USB on Jetson).
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
MODE="${1:-run}"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/setup.bash" 2>/dev/null || true
set -u

# Resolve FCU serial: udev symlink, by-id if00, or ttyACM0.
resolve_fcu_device() {
  if [[ -e /dev/ark_fpv ]]; then
    readlink -f /dev/ark_fpv
    return
  fi
  local by_id
  by_id=$(ls -1 /dev/serial/by-id/usb-ArduPilot_ARK_FPV*-if00 2>/dev/null | head -1 || true)
  if [[ -n "${by_id}" ]]; then
    readlink -f "${by_id}"
    return
  fi
  echo "/dev/ttyACM0"
}

FCU_DEV="$(resolve_fcu_device)"
FCU_URL="${FCU_URL:-udp://@127.0.0.1:14555}"

check_serial_free() {
  if fuser "${FCU_DEV}" >/dev/null 2>&1; then
    echo "ERROR: ${FCU_DEV} is in use (QGroundControl direct USB?)."
    echo "  Close QGC on the Jetson or disconnect its Comm Link to the FCU."
    fuser -v "${FCU_DEV}" 2>&1 || true
    echo ""
    echo "Use QGC over UDP to <jetson-ip>:14550 after this script starts the bridge."
    exit 1
  fi
}

check_bridge() {
  pgrep -x mavlink-routerd >/dev/null 2>&1
}

wait_imu_sample() {
  local timeout_s="${1:-10}"
  python3 <<PY
import sys, time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu

timeout = float("${timeout_s}")
rclpy.init()
node = Node('bench_imu_probe')
msgs = []

def cb(msg):
    msgs.append(msg)

sub = node.create_subscription(
    Imu, '/mavros/mavros/data', cb, qos_profile_sensor_data)
deadline = time.time() + timeout
while time.time() < deadline and not msgs:
    rclpy.spin_once(node, timeout_sec=0.2)
if msgs:
    m = msgs[0]
    print(f"orientation: x={m.orientation.x:.4f} y={m.orientation.y:.4f} "
          f"z={m.orientation.z:.4f} w={m.orientation.w:.4f}")
    print(f"angular_velocity: x={m.angular_velocity.x:.4f} "
          f"y={m.angular_velocity.y:.4f} z={m.angular_velocity.z:.4f}")
    sys.exit(0)
sys.exit(1)
PY
}

request_mavlink_streams() {
  if ros2 service list 2>/dev/null | grep -q '/mavros/set_stream_rate'; then
    ros2 service call /mavros/set_stream_rate mavros_msgs/srv/StreamRate \
      "{stream_id: 0, message_rate: 10, on_off: true}" >/dev/null 2>&1 || true
  fi
}

start_bridge() {
  check_serial_free
  if pgrep -x mavlink-routerd >/dev/null 2>&1; then
    echo "mavlink-router already running"
    return 0
  fi
  export FCU_DEVICE="${FCU_DEV}"
  echo "Starting mavlink-router on ${FCU_DEV} -> MAVROS ${FCU_URL}"
  nohup "${MARV_WS}/start_mavlink_router.sh" > /tmp/marv-mavlink-router.log 2>&1 &
  for _ in $(seq 1 15); do
    sleep 1
    if check_bridge; then
      echo "mavlink-router up (log: /tmp/marv-mavlink-router.log)"
      return 0
    fi
  done
  echo "ERROR: mavlink-router failed to start. Log:"
  tail -20 /tmp/marv-mavlink-router.log 2>/dev/null || true
  exit 1
}

wait_mavros() {
  for _ in $(seq 1 25); do
    if timeout 3 ros2 topic echo /mavros/state --once 2>/dev/null | grep -q 'connected: true'; then
      sleep 1
      if timeout 3 ros2 topic echo /mavros/state --once 2>/dev/null | grep -q 'connected: true'; then
        return 0
      fi
    fi
    sleep 1
  done
  return 1
}

run_test() {
  echo "=== Bench FCU test (Jetson + ARK FPV) ==="
  echo "FCU device: ${FCU_DEV}"
  echo ""

  if pgrep -x mavlink-routerd >/dev/null 2>&1; then
    echo "[PASS] mavlink-router running (${FCU_DEV})"
  elif fuser "${FCU_DEV}" >/dev/null 2>&1; then
    echo "[FAIL] Serial port busy (close QGC direct USB)"
    fuser -v "${FCU_DEV}" 2>&1 || true
    exit 1
  else
    echo "[WARN] Serial port free — start bridge: $0 bridge"
  fi

  if check_bridge; then
    echo "[PASS] mavlink-router running"
  else
    echo "[FAIL] mavlink-router not running — run: $0 bridge"
    exit 1
  fi

  if wait_mavros; then
    echo "[PASS] MAVROS connected"
    timeout 3 ros2 topic echo /mavros/state --once 2>/dev/null || true
  else
    echo "[FAIL] MAVROS not connected — restart bridge + stack:"
    echo "  pkill mavlink-routerd; pkill -f mavros_node"
    echo "  ~/marv_ws/scripts/bench_fcu_stack.sh"
    exit 1
  fi

  request_mavlink_streams
  sleep 1

  if wait_imu_sample 12; then
    echo "[PASS] IMU data (/mavros/mavros/data, sensor_data QoS)"
  else
    echo "[FAIL] No IMU on /mavros/mavros/data"
    echo "  Hint: MAVROS IMU uses best_effort QoS; link may be stale."
    echo "  Restart: pkill mavlink-routerd; pkill -f mavros_node; $0"
    exit 1
  fi

  echo ""
  echo "RC override test (2s forward) — props OFF / sub out of water:"
  timeout 8 ros2 topic pub -r 10 /mavros/rc/override mavros_msgs/msg/OverrideRCIn \
    "{channels: [65535, 65535, 1500, 1500, 1600, 1500, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535]}" &
  PUB_PID=$!
  sleep 2
  kill "${PUB_PID}" 2>/dev/null || true
  echo "[INFO] Published RC override chan5=1600 (forward). Check SERVO in QGC or mavproxy."
  echo ""
  echo "All bench checks passed."
}

case "${MODE}" in
  test)
    run_test
    ;;
  bridge)
    start_bridge
    ;;
  run)
    # Ensure Python package importable
    if ! python3 -c "from marv_bringup.serial_devices import DEFAULT_MAVROS_FCU_URL" 2>/dev/null; then
      echo "Installing marv_bringup Python package..."
      pip3 install "${MARV_WS}/src/marv_bringup" \
        --target "${MARV_WS}/install/marv_bringup/lib/python3.10/site-packages" -q
      source "${MARV_WS}/install/setup.bash"
    fi
    start_bridge
    echo ""
    echo "Launching ROS (ardusub + mavros, no vision/ping)..."
    exec ros2 launch marv_bringup prequal_bringup.launch.py \
      enable_control:=true \
      command_backend:=mavros_rc \
      use_vision:=false \
      use_ping_driver:=false \
      use_mapping:=false \
      fcu_url:="${FCU_URL}" \
      fcu_mode:="${FCU_MODE:-MANUAL}" \
      auto_arm:="${AUTO_ARM:-false}" \
      hold_depth_with_autopilot:=false
    ;;
  *)
    echo "Usage: $0 [run|test|bridge]"
    exit 1
    ;;
esac

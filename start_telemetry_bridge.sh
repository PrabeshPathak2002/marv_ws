#!/usr/bin/env bash
# MAVProxy telemetry splitter: one FCU serial link -> MAVROS (Jetson) + QGC (laptop).
#
# Start this BEFORE ros2 launch / run_prequal.sh. MAVROS uses udp://@127.0.0.1:14555
# and must NOT open the FCU serial port directly.
#
# Alternative (lighter, recommended for param-sync issues): start_mavlink_router.sh
#
# Ping (/dev/ping_sonar) and exploreHD (/dev/explore_hd) are separate USB devices —
# install udev rules once: sudo ~/marv_ws/setup_hardware_rules.sh
set -euo pipefail

# ---------------------------------------------------------------------------
# FCU serial port — EDIT to match your Jetson (run: ls -l /dev/ark_fpv)
# ---------------------------------------------------------------------------
# Recommended after udev setup:
FCU_DEVICE="${FCU_DEVICE:-/dev/ark_fpv}"
# Or a raw tty node if udev is not installed yet:
# FCU_DEVICE="/dev/ttyACM0"

BAUDRATE="${BAUDRATE:-115200}"

# ---------------------------------------------------------------------------
# QGC UDP broadcast — EDIT subnet to match your Wi-Fi / tether network
# ---------------------------------------------------------------------------
# Examples:
#   Wi-Fi bench:     192.168.1.255
#   USB tether:      192.168.137.255
# Find yours: ip -4 addr show | grep inet   (use x.y.z.255 for subnet x.y.z.0/24)
QGC_UDP_BCAST="${QGC_UDP_BCAST:-192.168.1.255}"
QGC_UDP_PORT="${QGC_UDP_PORT:-14550}"

# Local MAVROS input (must match marv_bringup mavros.launch.py default)
MAVROS_UDP_HOST="${MAVROS_UDP_HOST:-127.0.0.1}"
MAVROS_UDP_PORT="${MAVROS_UDP_PORT:-14555}"

# ---------------------------------------------------------------------------

if ! command -v mavproxy.py >/dev/null 2>&1; then
  echo "ERROR: MAVProxy is not installed."
  echo ""
  echo "Install one of:"
  echo "  pip3 install MAVProxy"
  echo "  sudo apt install python3-pip && pip3 install MAVProxy"
  echo ""
  echo "Then re-run: $0"
  exit 1
fi

if [[ ! -e "${FCU_DEVICE}" ]]; then
  echo "ERROR: FCU device not found: ${FCU_DEVICE}"
  echo "  ls -l /dev/ark_fpv /dev/ttyACM*"
  echo "  Or run: sudo ~/marv_ws/setup_hardware_rules.sh"
  exit 1
fi

if fuser "${FCU_DEVICE}" >/dev/null 2>&1; then
  echo "WARN: ${FCU_DEVICE} is already in use (QGC direct USB or another MAVProxy?)."
  fuser -v "${FCU_DEVICE}" 2>&1 || true
fi

echo "=== Marv MAVProxy telemetry bridge ==="
echo "  Master:   ${FCU_DEVICE} @ ${BAUDRATE}"
echo "  MAVROS:   udp:${MAVROS_UDP_HOST}:${MAVROS_UDP_PORT}"
echo "  QGC:      udpbcast:${QGC_UDP_BCAST}:${QGC_UDP_PORT}"
echo ""
echo "In QGC: Application Settings -> Comm Links -> Add UDP, port ${QGC_UDP_PORT}"
echo ""
echo "STARTUP ORDER (important for QGC parameters):"
echo "  1) Start this script (MAVProxy) — keep this terminal open"
echo "  2) Connect QGC on laptop — wait until parameters finish loading"
echo "  3) Then launch ROS: ~/marv_ws/scripts/run_prequal.sh"
echo ""
echo "If QGC is stuck on 'Waiting for parameters', stop the ROS stack first:"
echo "  pkill -f prequal_bringup.launch.py"
echo ""
echo "Press Ctrl+C to stop."
echo ""
echo "========================================================================"
echo "WARNING: If QGroundControl gets stuck waiting for parameters, type"
echo "         'param fetch' into this terminal and hit Enter!"
echo "========================================================================"
echo ""

exec mavproxy.py \
  --master="${FCU_DEVICE}" \
  --baudrate="${BAUDRATE}" \
  --streamrate=10 \
  --mav20 \
  --out="udp:${MAVROS_UDP_HOST}:${MAVROS_UDP_PORT}" \
  --out="udpbcast:${QGC_UDP_BCAST}:${QGC_UDP_PORT}"

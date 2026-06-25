#!/usr/bin/env bash
# Arm/disarm ArduSub — mavlink2rest (BlueOS) or MAVROS (bench).
set -euo pipefail

FORCE="${1:-false}"
ACTION="${2:-arm}"   # arm | disarm

MAVLINK2REST_URL="${MAVLINK2REST_URL:-http://127.0.0.1:6040/v1/mavlink}"

if [[ "${FORCE}" == "force" || "${FORCE}" == "true" ]]; then
  PARAM2=2989.0
else
  PARAM2=0.0
fi

if [[ "${ACTION}" == "disarm" ]]; then
  PARAM1=0.0
  PARAM2=0.0
  echo "Disarming..."
else
  PARAM1=1.0
  if [[ "${FORCE}" == "force" || "${FORCE}" == "true" ]]; then
    echo "Force arming (bypasses prearm checks — use only when safe)..."
  else
    echo "Arming..."
  fi
fi

# --- BlueOS mavlink2rest ---
if curl -sf --connect-timeout 1 "${MAVLINK2REST_URL%/v1/mavlink}/v1/mavlink" >/dev/null 2>&1; then
  curl -sf -X POST "${MAVLINK2REST_URL}" \
    -H 'Content-Type: application/json' \
    -d "{\"header\":{\"system_id\":255,\"component_id\":240,\"sequence\":0},\"message\":{\"type\":\"COMMAND_LONG\",\"param1\":${PARAM1},\"param2\":${PARAM2},\"param3\":0.0,\"param4\":0.0,\"param5\":0.0,\"param6\":0.0,\"param7\":0.0,\"command\":{\"type\":\"MAV_CMD_COMPONENT_ARM_DISARM\"},\"target_system\":1,\"target_component\":1,\"confirmation\":1}}" \
    >/dev/null
  sleep 1
  ARMED=$(curl -sf "${MAVLINK2REST_URL%/v1/mavlink}/v1/mavlink/vehicles/1/components/1/messages/HEARTBEAT" \
    | python3 -c "import sys,json; b=json.load(sys.stdin)['message']['base_mode']['bits']; print('true' if b&128 else 'false')")
  if [[ "${ACTION}" == "arm" && "${ARMED}" == "true" ]]; then
    echo "Armed successfully (mavlink2rest)."
    exit 0
  elif [[ "${ACTION}" == "disarm" && "${ARMED}" == "false" ]]; then
    echo "Disarmed successfully (mavlink2rest)."
    exit 0
  fi
fi

# --- MAVROS (bench: start mavlink-router + ros launch first) ---
set +u
source /opt/ros/humble/setup.bash 2>/dev/null
source "${HOME}/marv_ws/install/setup.bash" 2>/dev/null
set -u

if ! ros2 service list 2>/dev/null | grep -qE '/mavros/(cmd/arming|mavros/arming)'; then
  echo "ERROR: /mavros/cmd/arming not available." >&2
  echo "  Start: ~/marv_ws/scripts/bench_fcu_stack.sh bridge" >&2
  echo "  Then launch mavros / prequal stack." >&2
  exit 1
fi

VALUE=$([[ "${ACTION}" == "arm" ]] && echo true || echo false)
ARM_SVC=$(ros2 service list 2>/dev/null | grep -E '/mavros/(cmd/arming|mavros/arming)' | head -1)
if [[ -n "${ARM_SVC}" ]] && ros2 service call "${ARM_SVC}" mavros_msgs/srv/CommandBool "{value: ${VALUE}}" --timeout 10 2>/dev/null \
   | grep -q 'success: True'; then
  echo "${ACTION^} command accepted (MAVROS)."
  exit 0
fi

# Force arm fallback via MAVROS param2 not available in CommandBool — use pymavlink
if [[ "${ACTION}" == "arm" && "${FORCE}" == "force" ]]; then
  python3 - <<'PY'
import sys
try:
    from pymavlink import mavutil
except ImportError:
    sys.exit(1)
m = mavutil.mavlink_connection('udp:127.0.0.1:14555')
m.wait_heartbeat(timeout=5)
m.mav.command_long_send(1, 1, 400, 0, 1, 2989, 0, 0, 0, 0, 0)
print("Force arm sent (pymavlink)")
PY
  exit $?
fi

echo "Arm/disarm failed." >&2
exit 1

#!/usr/bin/env bash
# Wait for marv_auv + ArduPilot plugin in Gazebo, then start ArduSub SITL.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
ARDUPILOT="${HOME}/ardupilot"
MODEL="${GZ_AUV_MODEL:-marv_auv}"
WAIT_SEC="${WAIT_SEC:-180}"
FRAME="${FRAME:-vectored_6dof}"
MAVPROXY_OUT="${MAVPROXY_OUT:-udp:127.0.0.1:14555}"

"${MARV_WS}/scripts/ensure_numpy1.sh"

# shellcheck source=/dev/null
source "${MARV_WS}/scripts/ensure_gazebo.sh"

export GZ_SIM_SYSTEM_PLUGIN_PATH="${HOME}/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
export GZ_SIM_RESOURCE_PATH="${HOME}/bluerov2_gz/models:${MARV_WS}/install/marv_worlds/share/marv_worlds/models:${GZ_SIM_RESOURCE_PATH:-}"

if [[ ! -x "${ARDUPILOT}/Tools/autotest/sim_vehicle.py" ]]; then
  echo "ArduPilot not found at ${ARDUPILOT}"
  exit 1
fi

echo "Waiting for Gazebo model ${MODEL} (up to ${WAIT_SEC}s)..."
deadline=$((SECONDS + WAIT_SEC))
while (( SECONDS < deadline )); do
  topics="$(gz topic -l 2>/dev/null || true)"
  if grep -q "/model/${MODEL}/" <<<"${topics}"; then
    echo "Found ${MODEL} in Gazebo — starting ArduSub SITL in 5s (plugin bind :9002)..."
    sleep 5
    break
  fi
  sleep 2
done

if ! gz topic -l 2>/dev/null | grep -q "/model/${MODEL}/"; then
  echo "ERROR: ${MODEL} not in Gazebo — start Gazebo first:" >&2
  echo "  ~/marv_ws/scripts/run_gazebo_prequal.sh full" >&2
  exit 1
fi

# World may load paused; ArduPilot JSON lockstep needs sim time advancing.
WORLD="$(gz topic -l 2>/dev/null | sed -n 's#^/world/\([^/]*\)/clock$#\1#p' | head -1)"
if [[ -n "${WORLD}" ]]; then
  "${MARV_WS}/scripts/gz_unpause_world.sh" "${WORLD}" 30 || true
fi

cd "${ARDUPILOT}"
exec ./Tools/autotest/sim_vehicle.py \
  -v ArduSub \
  -f "${FRAME}" \
  --model JSON \
  --out="${MAVPROXY_OUT}"

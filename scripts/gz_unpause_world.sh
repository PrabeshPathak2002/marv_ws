#!/usr/bin/env bash
# Unpause Gazebo world (sim may start paused; ArduPilot lockstep needs stepping).
set -euo pipefail
MARV_WS="${HOME}/marv_ws"
# shellcheck source=/dev/null
source "${MARV_WS}/scripts/ensure_gazebo.sh"
WORLD="${1:?world name}"
TRIES="${2:-60}"
for ((i = 1; i <= TRIES; i++)); do
  if gz service -s "/world/${WORLD}/control" \
      --reqtype gz.msgs.WorldControl \
      --reptype gz.msgs.Boolean \
      --timeout 3000 \
      --req 'pause: false' 2>/dev/null | grep -q 'data: true'; then
    echo "[gz_unpause_world] ${WORLD} running"
    exit 0
  fi
  sleep 2
done
echo "[gz_unpause_world] failed to unpause ${WORLD}" >&2
exit 1

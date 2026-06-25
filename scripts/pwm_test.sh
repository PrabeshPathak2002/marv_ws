#!/usr/bin/env bash
# Direct PWM test via mavlink2rest — streams RC override at 10Hz.
# RCMAP: throttle=3, yaw=4, forward=5, lateral=6 (ArduSub)
set -euo pipefail

MAVLINK2REST="${MAVLINK2REST:-http://127.0.0.1:6040/v1/mavlink}"
DURATION="${1:-5}"
# chan3=throttle, chan4=yaw, chan5=forward, chan6=lateral
THR="${2:-1500}"
YAW="${3:-1500}"
FWD="${4:-1600}"
LAT="${5:-1500}"

echo "PWM test ${DURATION}s: thr=${THR} yaw=${YAW} fwd=${FWD} lat=${LAT}"

# Ensure armed
"${HOME}/marv_ws/scripts/arm_vehicle.sh" force 2>/dev/null || true

# MANUAL mode (custom_mode 19)
curl -sf -X POST "${MAVLINK2REST}" -H 'Content-Type: application/json' -d \
  '{"header":{"system_id":255,"component_id":240,"sequence":0},"message":{"type":"SET_MODE","custom_mode":19,"target_system":1,"base_mode":{"bits":209}}}' >/dev/null || true

END=$((SECONDS + DURATION))
while (( SECONDS < END )); do
  curl -sf -X POST "${MAVLINK2REST}" -H 'Content-Type: application/json' -d \
    "{\"header\":{\"system_id\":255,\"component_id\":240,\"sequence\":0},\"message\":{\"type\":\"RC_CHANNELS_OVERRIDE\",\"chan1_raw\":65535,\"chan2_raw\":65535,\"chan3_raw\":${THR},\"chan4_raw\":${YAW},\"chan5_raw\":${FWD},\"chan6_raw\":${LAT},\"chan7_raw\":65535,\"chan8_raw\":65535,\"target_system\":1,\"target_component\":1}}" >/dev/null
  sleep 0.1
done

curl -s "${MAVLINK2REST%/v1/mavlink}/v1/mavlink/vehicles/1/components/1/messages/SERVO_OUTPUT_RAW" \
  | python3 -c "import sys,json; s=json.load(sys.stdin)['message']; print('SERVO after:', [s.get(f'servo{i}_raw') for i in range(1,9)])"

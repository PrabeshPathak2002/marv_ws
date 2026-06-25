#!/usr/bin/env bash
set -euo pipefail
export GZ_SIM_RESOURCE_PATH="${HOME}/bluerov2_gz/models:${HOME}/marv_ws/install/marv_worlds/share/marv_worlds/models"
export GZ_SIM_SYSTEM_PLUGIN_PATH="${HOME}/ardupilot_gazebo/build"
WORLD="${HOME}/marv_ws/install/marv_worlds/share/marv_worlds/worlds/marv_sitl_test.world"
GZLOG=/tmp/marv_gz_link.log
APLOG=/tmp/marv_ardu_link.log

cleanup() {
  kill "$APID" 2>/dev/null || true
  kill "$GZPID" 2>/dev/null || true
  wait "$APID" 2>/dev/null || true
  wait "$GZPID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting Gazebo..."
gz sim -r -s "$WORLD" >"$GZLOG" 2>&1 &
GZPID=$!
sleep 12
"${HOME}/marv_ws/scripts/gz_unpause_world.sh" marv_sitl_test 30

gz topic -l 2>/dev/null | grep -q '/model/marv_auv/' || { echo FAIL; exit 1; }
echo "marv_auv present"

cd "${HOME}/ardupilot"
./build/sitl/bin/ardusub --model JSON --speedup 1 \
  --defaults Tools/autotest/default_params/sub-6dof.parm \
  --sim-address=127.0.0.1 -I0 >"$APLOG" 2>&1 &
APID=$!
sleep 2
timeout 20 mavproxy.py --master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14555 >/dev/null 2>&1 || true

for _ in $(seq 1 15); do
  if grep -q 'JSON received' "$APLOG"; then
    echo "PASS: ArduSub received JSON from Gazebo (IMU plugin fix works)"
    exit 0
  fi
  sleep 1
done

grep 'No JSON sensor' "$APLOG" | tail -2 || true
echo "FAIL: no JSON received"
exit 1

#!/usr/bin/env bash
# ArduSub SITL for Gazebo marv_auv (waits for model in Gazebo first).
set -euo pipefail
exec "${HOME}/marv_ws/scripts/wait_for_gz_auv_and_start_sitl.sh"

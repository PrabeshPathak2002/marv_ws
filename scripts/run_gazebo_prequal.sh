#!/usr/bin/env bash
# Gazebo pre-qual practice: exploreHD camera in sim + prequal_cv vision + mission planner.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"

set +u
source /opt/ros/humble/setup.bash
source "${MARV_WS}/install/bb_worlds/share/bb_worlds/local_setup.bash" 2>/dev/null || true
source "${MARV_WS}/install/marv_worlds/share/marv_worlds/local_setup.bash" 2>/dev/null || true
source "${MARV_WS}/install/setup.bash" 2>/dev/null || true
set -u

export GZ_SIM_SYSTEM_PLUGIN_PATH="${HOME}/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
export GZ_SIM_RESOURCE_PATH="${HOME}/marv_ws/install/marv_worlds/share/marv_worlds/models:${HOME}/marv_ws/install/marv_worlds/share/marv_worlds:${HOME}/marv_ws/install/bb_worlds/share/bb_worlds/models:${HOME}/marv_ws/install/bb_worlds/share/bb_worlds:${HOME}/bluerov2_gz/models:${HOME}/bluerov2_gz/worlds:${GZ_SIM_RESOURCE_PATH:-}"

# shellcheck source=/dev/null
source "${MARV_WS}/scripts/ensure_gazebo.sh"

"${MARV_WS}/scripts/ensure_numpy1.sh"

# Regenerate worlds + marv_auv, reinstall marv_worlds
python3 "${MARV_WS}/src/marv_worlds/scripts/generate_worlds.py"
python3 "${MARV_WS}/src/marv_worlds/scripts/build_marv_auv_model.py" 2>/dev/null || true
cmake --install "${MARV_WS}/src/marv_worlds/build" >/dev/null 2>&1 || \
  "${MARV_WS}/scripts/install_sim_worlds.sh"

MODE="${1:-vision}"
shift || true

case "${MODE}" in
  vision)
    echo "=== Gazebo pre-qual (vision + planner, no FCU) ==="
    echo "  World: marv_prequal_sim (pass world:=marv_prequal for bb pool visuals)"
    exec ros2 launch marv_worlds gazebo_prequal_sim.launch.py \
      vision_only:=true \
      publish_debug_image:=true \
      "$@"
    ;;
  full)
    echo "=== Gazebo pre-qual (BlueROV2 heavy + ArduSub + mission control) ==="
    echo "  World: marv_prequal_full (bb pool + embedded marv_auv)."
    echo "  Order: Gazebo loads AUV -> SITL (~40s) -> MAVROS (~55s)."
    echo "  Do NOT run start_ardusub_sitl.sh separately."
    echo ""
    # shellcheck source=/dev/null
    source "${MARV_WS}/scripts/ensure_mavros.sh"
    HEADLESS_ARGS=()
    if [[ -z "${MARV_GZ_GUI:-}" ]] && { [[ -f /etc/nv_tegra_release ]] || [[ "${MARV_FORCE_HEADLESS:-}" == 1 ]]; }; then
      echo "  Jetson detected — running Gazebo headless (no GUI). Set MARV_GZ_GUI=1 to force GUI."
      HEADLESS_ARGS=(headless:=true)
    fi
    exec ros2 launch marv_worlds gazebo_prequal_sim.launch.py \
      vision_only:=false \
      world:=marv_prequal_full \
      start_sitl:=true \
      enable_control:=true \
      auto_arm:=true \
      publish_debug_image:=true \
      "${HEADLESS_ARGS[@]}" \
      "$@"
    ;;
  pool)
    echo "=== Real pool pre-qual (exploreHD USB + ARK FPV) ==="
    exec "${MARV_WS}/scripts/run_prequal_hardcoded.sh" true mavros_rc "$@"
    ;;
  *)
    echo "Usage: $0 {vision|full|pool} [extra launch args...]"
    exit 1
    ;;
esac

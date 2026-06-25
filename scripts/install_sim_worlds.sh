#!/usr/bin/env bash
# Install bb_worlds + marv_worlds for Gazebo simulation.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
BB_SRC="${MARV_WS}/src/bb_worlds"
BB_INSTALL="${MARV_WS}/install/bb_worlds"
MARV_PKG="${MARV_WS}/src/marv_worlds"
MARV_INSTALL="${MARV_WS}/install/marv_worlds"

echo "=============================================="
echo "  Marv simulation worlds install"
echo "=============================================="

# --- bb_worlds submodule ---
if [[ ! -d "${BB_SRC}/.git" ]]; then
  echo "Initializing bb_worlds submodule..."
  cd "${MARV_WS}"
  git submodule update --init --recursive src/bb_worlds
fi

if command -v git-lfs >/dev/null 2>&1; then
  echo "Pulling bb_worlds mesh assets (git lfs)..."
  cd "${BB_SRC}"
  git lfs install --local 2>/dev/null || true
  git lfs pull
else
  echo "WARNING: git-lfs not installed — bb_worlds meshes may be missing."
  echo "  Install: sudo apt install git-lfs && git lfs install"
  echo "  Then re-run this script, or use use_simple:=true in launch."
fi

# --- build / install bb_worlds ---
echo "Installing bb_worlds..."
mkdir -p "${BB_SRC}/build"
cmake -S "${BB_SRC}" -B "${BB_SRC}/build" -DCMAKE_INSTALL_PREFIX="${BB_INSTALL}"
cmake --build "${BB_SRC}/build"
cmake --install "${BB_SRC}/build"

# --- regenerate marv worlds (bb assets by default) ---
echo "Generating marv_worlds SDF files..."
python3 "${MARV_PKG}/scripts/generate_worlds.py"

# --- build / install marv_worlds ---
echo "Installing marv_worlds..."
mkdir -p "${MARV_PKG}/build"
cmake -S "${MARV_PKG}" -B "${MARV_PKG}/build" -DCMAKE_INSTALL_PREFIX="${MARV_INSTALL}"
cmake --build "${MARV_PKG}/build"
cmake --install "${MARV_PKG}/build"

echo ""
echo "[OK] Simulation worlds ready."
echo ""
echo "  source ${BB_INSTALL}/share/bb_worlds/local_setup.bash"
echo "  source ${MARV_INSTALL}/share/marv_worlds/local_setup.bash"
echo ""
echo "  ros2 launch marv_worlds gazebo_world.launch.py mission:=prequal"
echo "  ros2 launch marv_worlds gazebo_world.launch.py mission:=traverse_gate"
echo ""
echo "  Procedural fallback (no meshes):  use_simple:=true"

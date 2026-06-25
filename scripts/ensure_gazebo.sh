#!/usr/bin/env bash
# Ensure Gazebo Harmonic CLI and runtime plugins are available before sim launch.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
_GZ_APT_PACKAGES=(
  gz-tools2
  gz-sim8-cli
  libgz-sim8-plugins
  libgz-physics8-dartsim
  libgz-rendering8-ogre2
  libgz-rendering8-ogre2-dev
  python3-gz-transport13
  python3-gz-msgs10
)
_GZ_INSTALL_HINT="sudo apt install ${_GZ_APT_PACKAGES[*]}"

if ! command -v gz >/dev/null 2>&1; then
  for setup in \
    /usr/share/gz/gz2.setup.sh \
    /opt/ros/humble/share/gz/setup.sh; do
    if [[ -f "${setup}" ]]; then
      # shellcheck disable=SC1090
      set +u
      source "${setup}"
      set -u
      break
    fi
  done
fi

if ! command -v gz >/dev/null 2>&1; then
  echo "ERROR: Gazebo Sim not found ('gz' not in PATH)." >&2
  echo "  Install: ${_GZ_INSTALL_HINT}" >&2
  return 1 2>/dev/null || exit 1
fi

ARCH="$(dpkg-architecture -qDEB_HOST_MULTIARCH 2>/dev/null || echo 'aarch64-linux-gnu')"
PHYS8="/usr/lib/${ARCH}/gz-physics-8/engine-plugins/libgz-physics8-dartsim-plugin.so.8"
RENDER8="/usr/lib/${ARCH}/gz-rendering-8/engine-plugins/libgz-rendering8-ogre2.so.8"
OGRE_MEDIA="/usr/share/gz/gz-rendering8/ogre2/media/Hlms/Unlit/GLSL"
OGRE_MEDIA_LOCAL="${MARV_WS}/.gz_local/usr/share/gz/gz-rendering8/ogre2/media/Hlms/Unlit/GLSL"
missing=()
[[ -f "${PHYS8}" ]] || missing+=('libgz-physics8-dartsim')
[[ -f "${RENDER8}" ]] || missing+=('libgz-rendering8-ogre2')
if [[ ! -d "${OGRE_MEDIA}" ]] && [[ ! -d "${OGRE_MEDIA_LOCAL}" ]]; then
  missing+=('libgz-rendering8-ogre2-dev')
fi

if ((${#missing[@]} > 0)); then
  echo "ERROR: Missing Gazebo packages: ${missing[*]}" >&2
  echo "  Install: ${_GZ_INSTALL_HINT}" >&2
  return 1 2>/dev/null || exit 1
fi

# shellcheck source=/dev/null
source "${MARV_WS}/scripts/gz_plugin_path_setup.sh"

return 0 2>/dev/null || exit 0

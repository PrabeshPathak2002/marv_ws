#!/usr/bin/env bash
# Symlink versioned Gazebo engine plugins + OGRE media paths gz-sim 8.14 expects.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
ARCH="$(dpkg-architecture -qDEB_HOST_MULTIARCH 2>/dev/null || echo 'aarch64-linux-gnu')"
CACHE="${MARV_WS}/.gz_plugin_cache"
PHYS_SRC="/usr/lib/${ARCH}/gz-physics-8/engine-plugins/libgz-physics8-dartsim-plugin.so.8"
RENDER_SRC="/usr/lib/${ARCH}/gz-rendering-8/engine-plugins/libgz-rendering8-ogre2.so.8"
OGRE_MEDIA="/usr/share/gz/gz-rendering8/ogre2/media"
OGRE_MEDIA_LOCAL="${MARV_WS}/.gz_local/usr/share/gz/gz-rendering8/ogre2/media"
if [[ ! -d "${OGRE_MEDIA}/Hlms/Unlit/GLSL" ]] && [[ -d "${OGRE_MEDIA_LOCAL}/Hlms/Unlit/GLSL" ]]; then
  OGRE_MEDIA="${OGRE_MEDIA_LOCAL}"
fi

mkdir -p "${CACHE}/physics" "${CACHE}/rendering"

if [[ -f "${PHYS_SRC}" ]]; then
  ln -sfn "${PHYS_SRC}" "${CACHE}/physics/libgz-physics-dartsim-plugin.so"
else
  PHYS7="/usr/lib/${ARCH}/gz-physics-7/engine-plugins/libgz-physics7-dartsim-plugin.so.7"
  if [[ -f "${PHYS7}" ]]; then
    ln -sfn "${PHYS7}" "${CACHE}/physics/libgz-physics-dartsim-plugin.so"
  fi
fi

if [[ -f "${RENDER_SRC}" ]]; then
  ln -sfn "${RENDER_SRC}" "${CACHE}/rendering/libgz-rendering-ogre2.so"
fi

# gz-sim looks under <resource>/gz-rendering8/ogre2/src/media; apt ships ogre2/media (-dev pkg).
if [[ ! -d "${OGRE_MEDIA}/Hlms/Unlit/GLSL" ]]; then
  if [[ ! -d "${OGRE_MEDIA_LOCAL}/Hlms/Unlit/GLSL" ]]; then
    echo "[gz_plugin_path_setup] Fetching OGRE media (libgz-rendering8-ogre2-dev)..." >&2
    curl -fsSL \
      http://packages.osrfoundation.org/gazebo/ubuntu-stable/pool/main/g/gz-rendering8/libgz-rendering8-ogre2-dev_8.2.3-1~jammy_arm64.deb \
      -o /tmp/libgz-rendering8-ogre2-dev.deb
    mkdir -p "${MARV_WS}/.gz_local"
    dpkg-deb -x /tmp/libgz-rendering8-ogre2-dev.deb "${MARV_WS}/.gz_local"
  fi
  OGRE_MEDIA="${OGRE_MEDIA_LOCAL}"
fi
if [[ ! -d "${OGRE_MEDIA}/Hlms/Unlit/GLSL" ]]; then
  echo "ERROR: OGRE shader media missing (need libgz-rendering8-ogre2-dev)." >&2
  echo "  Install: sudo apt install libgz-rendering8-ogre2-dev" >&2
  return 1 2>/dev/null || exit 1
fi
mkdir -p "${CACHE}/resource/ogre2/src"
ln -sfn "${OGRE_MEDIA}" "${CACHE}/resource/ogre2/src/media"

export GZ_SIM_PHYSICS_ENGINE_PATH="${CACHE}/physics"
export GZ_SIM_RENDER_ENGINE_PATH="${CACHE}/rendering"
export GZ_RENDERING_RESOURCE_PATH="${CACHE}/resource"

# Headless Jetson: avoid LIBGL_ALWAYS_SOFTWARE — conflicts with OGRE EGL device selection.

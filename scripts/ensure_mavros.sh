#!/usr/bin/env bash
# Use system mavros or a local apt overlay (no sudo) when missing.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
OVERLAY="${MARV_WS}/.ros_apt_overlay"
ROS_PREFIX="${OVERLAY}/opt/ros/humble"
SYS_OVERLAY="${OVERLAY}/usr"

_mavros_env() {
  export AMENT_PREFIX_PATH="${ROS_PREFIX}:${AMENT_PREFIX_PATH:-}"
  export CMAKE_PREFIX_PATH="${ROS_PREFIX}:${CMAKE_PREFIX_PATH:-}"
  export PATH="${ROS_PREFIX}/bin:${PATH}"
  export LD_LIBRARY_PATH="${SYS_OVERLAY}/lib/aarch64-linux-gnu:${ROS_PREFIX}/lib:${LD_LIBRARY_PATH:-}"
  export PYTHONPATH="${ROS_PREFIX}/local/lib/python3.10/dist-packages:${PYTHONPATH:-}"
}

_fetch_deb() {
  local pkg="$1" dest="$2"
  if [[ -f "${dest}" ]]; then
    return 0
  fi
  apt-get download -o Dir::Cache=/tmp "${pkg}" 2>/dev/null
  local deb
  deb="$(ls -t /tmp/${pkg}_*.deb 2>/dev/null | head -1)"
  if [[ -n "${deb}" ]]; then
    cp -f "${deb}" "${dest}"
  fi
}

if [[ -x /opt/ros/humble/lib/mavros/mavros_node ]]; then
  return 0 2>/dev/null || exit 0
fi

if ros2 pkg prefix mavros >/dev/null 2>&1; then
  return 0 2>/dev/null || exit 0
fi

if [[ -x "${ROS_PREFIX}/lib/mavros/mavros_node" ]]; then
  _mavros_env
  echo "[ensure_mavros] using local overlay: ${ROS_PREFIX}" >&2
  return 0 2>/dev/null || exit 0
fi

mkdir -p "${OVERLAY}"
for pkg in libgeographic19 ros-humble-geographic-msgs ros-humble-libmavconn ros-humble-mavros-msgs ros-humble-mavros ros-humble-mavros-extras; do
  deb="${OVERLAY}/${pkg}.deb"
  if [[ ! -f "${deb}" ]]; then
    echo "[ensure_mavros] downloading ${pkg}..." >&2
    _fetch_deb "${pkg}" "${deb}" || true
  fi
  if [[ -f "${deb}" ]]; then
    dpkg-deb -x "${deb}" "${OVERLAY}"
  fi
done

if [[ ! -x "${ROS_PREFIX}/lib/mavros/mavros_node" ]]; then
  echo "ERROR: mavros not installed." >&2
  echo "  Install: sudo apt install ros-humble-mavros ros-humble-mavros-extras libgeographic19" >&2
  return 1 2>/dev/null || exit 1
fi

_mavros_env

if ! ros2 pkg prefix mavros >/dev/null 2>&1; then
  echo "ERROR: mavros overlay failed." >&2
  return 1 2>/dev/null || exit 1
fi

echo "[ensure_mavros] using local overlay: ${ROS_PREFIX}" >&2
return 0 2>/dev/null || exit 0

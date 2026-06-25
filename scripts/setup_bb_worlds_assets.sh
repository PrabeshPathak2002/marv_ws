#!/usr/bin/env bash
# Pull bb_worlds git-lfs meshes (required for default worlds).
set -euo pipefail

BB_WORLDS="${HOME}/marv_ws/src/bb_worlds"

if [[ ! -d "${BB_WORLDS}/.git" ]]; then
  echo "bb_worlds submodule missing. From marv_ws:"
  echo "  git submodule update --init --recursive src/bb_worlds"
  exit 1
fi

cd "${BB_WORLDS}"
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install --local 2>/dev/null || true
  git lfs pull
  echo "[OK] bb_worlds LFS assets pulled."
else
  echo "WARNING: git-lfs not installed."
  echo "  sudo apt install git-lfs && git lfs install"
  echo "  Or launch with use_simple:=true for procedural fallback worlds."
  exit 1
fi

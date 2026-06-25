#!/usr/bin/env bash
# ROS Humble cv_bridge and MAVProxy/matplotlib need NumPy 1.x.
# colcon may install NumPy 2 into marv_bringup site-packages — fix it here.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
TARGET="${MARV_WS}/install/marv_bringup/lib/python3.10/site-packages"

_numpy_ok() {
  python3 - "$TARGET" <<'PY'
import sys
target = sys.argv[1]
sys.path.insert(0, target)
try:
    import numpy
except ImportError:
    raise SystemExit(1)
raise SystemExit(0 if numpy.__version__.startswith("1.") else 1)
PY
}

if _numpy_ok; then
  exit 0
fi

echo "Fixing NumPy (workspace has 2.x; need 1.x for cv_bridge / MAVProxy)..."
pip3 install --target "${TARGET}" --force-reinstall --upgrade 'numpy<2' -q
pip3 install --user --force-reinstall 'numpy<2' -q 2>/dev/null || true

if _numpy_ok; then
  python3 -c "import sys; sys.path.insert(0,'${TARGET}'); import numpy; print('NumPy', numpy.__version__, 'OK')"
else
  echo "WARNING: NumPy still not 1.x — try: pip3 install --user --force-reinstall 'numpy<2'" >&2
  exit 1
fi

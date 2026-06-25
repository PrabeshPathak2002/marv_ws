#!/usr/bin/env bash
# Copy src launch/config into install/ when colcon build is broken.
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
SRC="${MARV_WS}/src/marv_bringup"
DST="${MARV_WS}/install/marv_bringup/share/marv_bringup"

mkdir -p "${DST}/launch" "${DST}/config"
cp -a "${SRC}/launch/"*.launch.py "${DST}/launch/"
cp -a "${SRC}/config/"*.yaml "${DST}/config/" 2>/dev/null || true
cp -a "${SRC}/config/plans/"*.yaml "${DST}/config/plans/" 2>/dev/null || true

PY_SITE="${MARV_WS}/install/marv_bringup/lib/python3.10/site-packages/marv_bringup"
mkdir -p "${PY_SITE}"
cp -a "${SRC}/marv_bringup/"*.py "${PY_SITE}/"

LIB_BIN="${MARV_WS}/install/marv_bringup/lib/marv_bringup"
mkdir -p "${LIB_BIN}"
cat > "${LIB_BIN}/fcu_setup_node" <<'PY'
#!/usr/bin/env python3
import sys
from pathlib import Path
site = Path(__file__).resolve().parents[1] / 'python3.10' / 'site-packages'
sys.path.insert(0, str(site))
from marv_bringup.fcu_setup_node import main
raise SystemExit(main())
PY
chmod +x "${LIB_BIN}/fcu_setup_node"

PY_SITE_ARDU="${MARV_WS}/install/marv_ardusub/lib/python3.10/site-packages"
mkdir -p "${PY_SITE_ARDU}/marv_ardusub/lib"
if [[ -d "${MARV_WS}/src/marv_ardusub/marv_ardusub" ]]; then
  cp -a "${MARV_WS}/src/marv_ardusub/marv_ardusub/"*.py "${PY_SITE_ARDU}/marv_ardusub/" 2>/dev/null || true
  cp -a "${MARV_WS}/src/marv_ardusub/marv_ardusub/lib/"*.py "${PY_SITE_ARDU}/marv_ardusub/lib/" 2>/dev/null || true
fi

echo "Synced marv_bringup + ardusub to install/"

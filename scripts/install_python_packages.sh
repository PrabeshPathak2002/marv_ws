#!/usr/bin/env bash
# Install Python packages when colcon build fails (setuptools 82+ vs colcon).
set -euo pipefail

MARV_WS="${HOME}/marv_ws"
PY_SITE="${MARV_WS}/install/marv_bringup/lib/python3.10/site-packages"
mkdir -p "${PY_SITE}"

PKGS=(
  marv_ardusub
  marv_control
  marv_mapping
  marv_vision
  marv_prequal
  marv_bringup
)

for pkg in "${PKGS[@]}"; do
  if [[ -d "${MARV_WS}/src/${pkg}" ]]; then
    echo "pip install ${pkg}..."
    pip3 install "${MARV_WS}/src/${pkg}" --target "${PY_SITE}" -q --force-reinstall \
      || pip3 install "${MARV_WS}/src/${pkg}" --target "${PY_SITE}" -q
  fi
done

# ROS 2 launch looks for executables under lib/<package_name>/.
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

echo "Done. Source: source ${MARV_WS}/install/setup.bash"
python3 -c "import sys; sys.path.insert(0,'${PY_SITE}'); from marv_bringup.serial_devices import DEFAULT_MAVROS_FCU_URL; print('marv_bringup OK:', DEFAULT_MAVROS_FCU_URL)"

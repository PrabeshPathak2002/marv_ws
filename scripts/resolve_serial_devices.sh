#!/usr/bin/env bash
# Print stable /dev/serial/by-id paths for Ping1D and ARK FPV.
set -euo pipefail

echo "=== /dev/serial/by-id ==="
if [[ -d /dev/serial/by-id ]]; then
  ls -la /dev/serial/by-id/
else
  echo "(directory missing — are USB devices plugged in?)"
fi

echo ""
echo "=== Resolved device paths ==="
python3 - <<'PY'
import sys
sys.path.insert(0, 'src/marv_bringup')
try:
    from marv_bringup.serial_devices import describe_serial_devices
    print(describe_serial_devices())
except ImportError:
    # Workspace not on PYTHONPATH — use glob directly.
    from pathlib import Path
    by_id = Path('/dev/serial/by-id')
    ping = sorted(by_id.glob('usb-FTDI_FT231X_USB_UART_*-if00-port0'))
    ark = sorted(by_id.glob('usb-ArduPilot_ARK_FPV*-if00'))
    print('Ping1D:', ping[0] if ping else '/dev/ttyUSB0 (fallback)')
    print('ARK FPV:', ark[0] if ark else '/dev/ttyACM0 (fallback)')
PY

echo ""
echo "=== Port holders (if busy) ==="
for dev in /dev/ttyUSB0 /dev/ttyACM0; do
  if [[ -e "$dev" ]]; then
    echo -n "$dev: "
    fuser -v "$dev" 2>&1 | tail -n +1 || echo "(free)"
  fi
done

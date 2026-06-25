#!/usr/bin/env bash
# Free Jetson 40-pin UART pins and grant serial port access for the FCU.
# Run once after wiring the flight controller to the Orin NX header (TX/RX).
set -euo pipefail

echo "=== Jetson UART setup ==="
echo "Stopping nvgetty (frees /dev/ttyTHS* for user applications)..."
sudo systemctl stop nvgetty

echo "Disabling nvgetty at boot..."
sudo systemctl disable nvgetty

echo "Adding ${USER} to dialout group (serial port access)..."
sudo usermod -aG dialout "${USER}"

echo ""
echo "========================================================================"
echo "  REBOOT REQUIRED"
echo ""
echo "  You MUST reboot the Jetson for these changes to take effect."
echo "  After reboot, verify with:  groups   (should include dialout)"
echo "  Then test FCU UART:         ls -l /dev/ttyTHS0 /dev/ttyTHS1"
echo "========================================================================"

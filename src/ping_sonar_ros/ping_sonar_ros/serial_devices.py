"""Resolve Ping1D serial path from /dev/serial/by-id."""

import os
from pathlib import Path

BY_ID_DIR = Path('/dev/serial/by-id')

PING_GLOB_PATTERNS = (
    'usb-FTDI_FT231X_USB_UART_*-if00-port0',
    'usb-FTDI_*_UART_*-if00-port0',
    'usb-FTDI_*-if00-port0',
)


def resolve_ping_device(fallback='/dev/ping_sonar'):
    udev = Path('/dev/ping_sonar')
    if udev.exists():
        return str(udev)
    if not BY_ID_DIR.is_dir():
        return fallback
    for pattern in PING_GLOB_PATTERNS:
        matches = sorted(BY_ID_DIR.glob(pattern))
        if matches:
            return str(matches[0])
    return fallback


def is_serial_port_available(port_path):
    try:
        fd = os.open(port_path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        os.close(fd)
        return True
    except OSError:
        return False

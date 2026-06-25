"""Resolve stable /dev/serial/by-id paths for Marv USB peripherals."""

from __future__ import annotations

from pathlib import Path

BY_ID_DIR = Path('/dev/serial/by-id')

# MAVROS connects via mavlink-router / MAVProxy UDP fan-out (see start_mavlink_router.sh).
DEFAULT_MAVROS_FCU_URL = 'udp://@127.0.0.1:14555'

# Blue Robotics Ping1D typically enumerates as FTDI FT231X USB UART.
PING_GLOB_PATTERNS = (
    'usb-FTDI_FT231X_USB_UART_*-if00-port0',
    'usb-FTDI_*_UART_*-if00-port0',
    'usb-FTDI_*-if00-port0',
)

# ARK FPV flight controller (ArduPilot USB CDC, primary MAVLink interface).
ARK_FPV_GLOB_PATTERNS = (
    'usb-ArduPilot_ARK_FPV*-if00',
    'usb-ARK*FPV*-if00',
)


def _first_match(patterns):
    if not BY_ID_DIR.is_dir():
        return None
    for pattern in patterns:
        matches = sorted(BY_ID_DIR.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def resolve_ping_device(fallback='/dev/ping_sonar'):
    """Return Ping1D serial path: udev symlink, then /dev/serial/by-id, then fallback."""
    udev = Path('/dev/ping_sonar')
    if udev.exists():
        return str(udev)
    return _first_match(PING_GLOB_PATTERNS) or fallback


def resolve_ark_fpv_device(fallback='/dev/ark_fpv'):
    """Return ARK FPV primary MAVLink serial path."""
    udev = Path('/dev/ark_fpv')
    if udev.exists():
        return str(udev)
    return _first_match(ARK_FPV_GLOB_PATTERNS) or fallback


def resolve_explore_hd_device(fallback='/dev/explore_hd'):
    """Return exploreHD V4L2 MJPEG device path."""
    udev = Path('/dev/explore_hd')
    if udev.exists():
        return str(udev)
    return fallback


def resolve_fcu_url(baud=115200, fallback_port='/dev/ark_fpv'):
    """Serial MAVROS fcu_url (direct USB). Prefer DEFAULT_MAVROS_FCU_URL + MAVProxy."""
    port = resolve_ark_fpv_device(fallback=fallback_port)
    return f'serial://{port}:{baud}'


def default_mavros_fcu_url():
    """MAVROS URL when fcu_url launch arg is auto (MAVProxy local UDP)."""
    return DEFAULT_MAVROS_FCU_URL


def is_serial_port_available(port_path):
    try:
        import os
        fd = os.open(port_path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        os.close(fd)
        return True
    except OSError:
        return False


def is_blueos_bridge_running():
    """True when BlueOS bridges holds Ping serial and exposes UDP :9090."""
    import subprocess
    try:
        result = subprocess.run(
            ['pgrep', '-f', r'bridges.*9090'],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def describe_serial_devices():
    """Human-readable summary for shell scripts / diagnostics."""
    lines = []
    if BY_ID_DIR.is_dir():
        for entry in sorted(BY_ID_DIR.iterdir()):
            try:
                target = entry.resolve()
            except OSError:
                target = '(unresolved)'
            lines.append(f'{entry.name} -> {target}')
    else:
        lines.append('(no /dev/serial/by-id directory)')

    ping = resolve_ping_device()
    ark = resolve_ark_fpv_device()
    cam = resolve_explore_hd_device()
    lines.append('')
    lines.append(f'Ping1D resolved: {ping}')
    lines.append(f'ARK FPV resolved: {ark}')
    lines.append(f'exploreHD resolved: {cam}')
    lines.append(f'MAVROS fcu_url (default): {DEFAULT_MAVROS_FCU_URL}')
    lines.append(f'MAVProxy serial master: {resolve_ark_fpv_device()}')
    return '\n'.join(lines)

"""Optional Blue Robotics Ping1D driver (external ping_sonar_ros package)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from marv_bringup.serial_devices import resolve_ping_device


def _launch_ping(context, *args, **kwargs):
    use_ping_driver = LaunchConfiguration('use_ping_driver').perform(context)
    if use_ping_driver.lower() not in ('true', '1', 'yes'):
        return []

    connection = LaunchConfiguration('ping_connection').perform(context)
    ping_device = LaunchConfiguration('ping_device').perform(context)
    udp_host = LaunchConfiguration('ping_udp_host').perform(context)
    udp_port = int(LaunchConfiguration('ping_udp_port').perform(context))

    if ping_device in ('auto', ''):
        ping_device = resolve_ping_device()

    if connection == 'udp':
        log_msg = f'Ping1D via UDP proxy {udp_host}:{udp_port}'
    else:
        connection = 'serial'
        log_msg = f'Ping1D via serial: {ping_device}'

    return [
        LogInfo(msg=log_msg),
        Node(
            package='ping_sonar_ros',
            executable='ping1d_node',
            name='ping1d_node',
            output='screen',
            parameters=[{
                'connection': connection,
                'port': ping_device,
                'udp_host': udp_host,
                'udp_port': udp_port,
            }],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_ping_driver',
            default_value='true',
            description='Start ping_sonar_ros Ping1D node (install separately).',
        ),
        DeclareLaunchArgument(
            'ping_connection',
            default_value='serial',
            description='serial (default, direct USB) or udp (only if a serial proxy is running).',
        ),
        DeclareLaunchArgument(
            'ping_device',
            default_value='auto',
            description='Ping1D path: auto resolves /dev/serial/by-id FTDI device.',
        ),
        DeclareLaunchArgument(
            'ping_udp_host',
            default_value='127.0.0.1',
            description='UDP proxy host when ping_connection:=udp.',
        ),
        DeclareLaunchArgument(
            'ping_udp_port',
            default_value='9090',
            description='UDP proxy port when ping_connection:=udp.',
        ),
        OpaqueFunction(function=_launch_ping),
    ])

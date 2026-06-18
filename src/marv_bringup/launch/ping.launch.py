"""Optional Blue Robotics Ping1D driver (external ping_sonar_ros package)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_ping_driver = LaunchConfiguration('use_ping_driver')
    ping_device = LaunchConfiguration('ping_device')

    ping_node = Node(
        package='ping_sonar_ros',
        executable='ping1d_node',
        name='ping1d_node',
        output='screen',
        parameters=[{'port': ping_device}],
        condition=IfCondition(use_ping_driver),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_ping_driver',
            default_value='true',
            description='Start ping_sonar_ros Ping1D node (install separately).',
        ),
        DeclareLaunchArgument(
            'ping_device',
            default_value='/dev/ttyUSB0',
            description='USB serial device for Ping1D (check dmesg when plugged in).',
        ),
        LogInfo(
            msg='Ping1D driver: install with '
                'git clone --recursive https://github.com/tasada038/ping_sonar_ros',
            condition=IfCondition(use_ping_driver),
        ),
        ping_node,
    ])

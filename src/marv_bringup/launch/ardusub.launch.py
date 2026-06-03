"""Launch marv_ardusub (position estimate + MAVROS actuation)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    command_backend = LaunchConfiguration('command_backend')

    return LaunchDescription([
        DeclareLaunchArgument(
            'command_backend',
            default_value='log_only',
            description=(
                'How to send cmd_vel to MAVROS: log_only, mavros_rc, '
                'setpoint_velocity, or disabled.'
            ),
        ),
        Node(
            package='marv_ardusub',
            executable='ardusub_node',
            name='ardusub_node',
            output='screen',
            parameters=[{'command_backend': command_backend}],
        ),
    ])

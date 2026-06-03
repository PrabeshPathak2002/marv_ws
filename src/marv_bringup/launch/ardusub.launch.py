"""Launch marv_ardusub (position estimate + vehicle I/O)."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='marv_ardusub',
            executable='ardusub_node',
            name='ardusub_node',
            output='screen',
        ),
    ])

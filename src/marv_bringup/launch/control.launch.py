"""Launch marv_control master node."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='marv_control',
            executable='master_control_node',
            name='master_control_node',
            output='screen',
        ),
    ])

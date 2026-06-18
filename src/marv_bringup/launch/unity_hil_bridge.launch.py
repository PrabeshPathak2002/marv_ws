"""Launch Unity HITL bridge (Unity <-> MAVROS)."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='marv_ardusub',
            executable='unity_hil_bridge',
            name='unity_hil_bridge',
            output='screen',
        ),
    ])

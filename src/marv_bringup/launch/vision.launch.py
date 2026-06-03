"""Launch marv_vision camera nodes."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_front_cam = LaunchConfiguration('use_front_cam')
    use_down_cam = LaunchConfiguration('use_down_cam')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_front_cam',
            default_value='true',
            description='Start front camera node (f_cam_node).',
        ),
        DeclareLaunchArgument(
            'use_down_cam',
            default_value='true',
            description='Start down camera node (d_cam_node).',
        ),
        Node(
            package='marv_vision',
            executable='f_cam_node',
            name='f_cam_node',
            output='screen',
            condition=IfCondition(use_front_cam),
        ),
        Node(
            package='marv_vision',
            executable='d_cam_node',
            name='d_cam_node',
            output='screen',
            condition=IfCondition(use_down_cam),
        ),
    ])

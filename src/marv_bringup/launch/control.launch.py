"""Launch marv_control master node."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    enable_control = LaunchConfiguration('enable_control')
    target_depth_m = LaunchConfiguration('target_depth_m')

    return LaunchDescription([
        DeclareLaunchArgument(
            'enable_control',
            default_value='false',
            description='Publish depth-hold cmd_vel (false = bench safe, zero output).',
        ),
        DeclareLaunchArgument(
            'target_depth_m',
            default_value='1.0',
            description='Target depth for depth hold (meters, NED z down).',
        ),
        Node(
            package='marv_control',
            executable='master_control_node',
            name='master_control_node',
            output='screen',
            parameters=[{
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
            }],
        ),
    ])

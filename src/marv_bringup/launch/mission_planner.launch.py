"""Launch mission planner with master control in planner mode."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('marv_bringup')
    default_config = os.path.join(pkg_share, 'config', 'marv.yaml')
    default_plan = os.path.join(pkg_share, 'config', 'plans', 'bench_plan.yaml')

    config_file = LaunchConfiguration('config_file')
    plan_file = LaunchConfiguration('plan_file')
    enable_control = LaunchConfiguration('enable_control')
    target_depth_m = LaunchConfiguration('target_depth_m')
    depth_hold_enabled = LaunchConfiguration('depth_hold_enabled')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config_file',
            default_value=default_config,
            description='Vehicle/behavior YAML config.',
        ),
        DeclareLaunchArgument(
            'plan_file',
            default_value=default_plan,
            description='Mission plan YAML graph.',
        ),
        DeclareLaunchArgument(
            'enable_control',
            default_value='false',
            description='Enable cmd_vel output (bench: keep false).',
        ),
        DeclareLaunchArgument(
            'target_depth_m',
            default_value='1.0',
            description='Depth hold target (meters).',
        ),
        DeclareLaunchArgument(
            'depth_hold_enabled',
            default_value='true',
            description='Master control heave from pose. Disable when ArduPilot ALT_HOLD holds depth.',
        ),
        Node(
            package='marv_control',
            executable='master_control_node',
            name='master_control_node',
            output='screen',
            parameters=[{
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
                'depth_hold_enabled': depth_hold_enabled,
                'config_file': config_file,
                'planner_mode': True,
                'active_behavior': 'hold',
            }],
        ),
        Node(
            package='marv_control',
            executable='mission_planner_node',
            name='mission_planner_node',
            output='screen',
            parameters=[{
                'config_file': config_file,
                'plan_file': plan_file,
                'auto_start': True,
            }],
        ),
    ])

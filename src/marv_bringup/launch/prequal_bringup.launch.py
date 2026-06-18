"""Pre-qualification stack: MAVROS + ardusub + vision + prequal_plan."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bringup_share = get_package_share_directory('marv_bringup')
    launch_dir = os.path.join(bringup_share, 'launch')
    default_config = os.path.join(bringup_share, 'config', 'marv.yaml')
    default_plan = os.path.join(bringup_share, 'config', 'plans', 'prequal_plan.yaml')

    use_mavros = LaunchConfiguration('use_mavros')
    use_ardusub = LaunchConfiguration('use_ardusub')
    use_vision = LaunchConfiguration('use_vision')
    fcu_url = LaunchConfiguration('fcu_url')
    enable_control = LaunchConfiguration('enable_control')
    command_backend = LaunchConfiguration('command_backend')
    config_file = LaunchConfiguration('config_file')
    plan_file = LaunchConfiguration('plan_file')
    target_depth_m = LaunchConfiguration('target_depth_m')
    use_sim = LaunchConfiguration('use_sim')
    use_ping_driver = LaunchConfiguration('use_ping_driver')

    return LaunchDescription([
        DeclareLaunchArgument('use_mavros', default_value='true'),
        DeclareLaunchArgument(
            'fcu_url',
            default_value='serial:///dev/ttyACM0:115200',
        ),
        DeclareLaunchArgument('use_ardusub', default_value='true'),
        DeclareLaunchArgument('use_vision', default_value='true'),
        DeclareLaunchArgument('enable_control', default_value='false'),
        DeclareLaunchArgument('command_backend', default_value='log_only'),
        DeclareLaunchArgument('config_file', default_value=default_config),
        DeclareLaunchArgument('plan_file', default_value=default_plan),
        DeclareLaunchArgument(
            'target_depth_m',
            default_value='1.0',
            description='Gate depth ~1 m below surface per RoboSub pre-qual spec.',
        ),
        DeclareLaunchArgument('use_sim', default_value='false'),
        DeclareLaunchArgument('use_ping_driver', default_value='false'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ping.launch.py')),
            condition=IfCondition(use_ping_driver),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mavros.launch.py')),
            launch_arguments={'fcu_url': fcu_url}.items(),
            condition=IfCondition(use_mavros),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ardusub.launch.py')),
            launch_arguments={'command_backend': command_backend}.items(),
            condition=IfCondition(use_ardusub),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'vision.launch.py')),
            launch_arguments={
                'use_sim': use_sim,
                'use_down_cam': 'false',
                'vision_profile': 'prequal_cv',
                'f_cam_conf_threshold': '0.30',
            }.items(),
            condition=IfCondition(use_vision),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mission_planner.launch.py')),
            launch_arguments={
                'config_file': config_file,
                'plan_file': plan_file,
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
            }.items(),
        ),
    ])

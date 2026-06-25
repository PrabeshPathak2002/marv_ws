"""Competition stack: MAVROS + ardusub + vision + YAML mission planner."""

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
    default_plan = os.path.join(bringup_share, 'config', 'plans', 'competition_plan.yaml')

    use_mavros = LaunchConfiguration('use_mavros')
    use_ardusub = LaunchConfiguration('use_ardusub')
    use_vision = LaunchConfiguration('use_vision')
    fcu_url = LaunchConfiguration('fcu_url')
    enable_control = LaunchConfiguration('enable_control')
    command_backend = LaunchConfiguration('command_backend')
    config_file = LaunchConfiguration('config_file')
    plan_file = LaunchConfiguration('plan_file')
    use_sim = LaunchConfiguration('use_sim')

    return LaunchDescription([
        DeclareLaunchArgument('use_mavros', default_value='true'),
        DeclareLaunchArgument(
            'fcu_url',
            default_value='udp://@127.0.0.1:14555',
            description='MAVROS UDP from MAVProxy.',
        ),
        DeclareLaunchArgument('use_ardusub', default_value='true'),
        DeclareLaunchArgument('use_vision', default_value='true'),
        DeclareLaunchArgument('enable_control', default_value='false'),
        DeclareLaunchArgument('command_backend', default_value='log_only'),
        DeclareLaunchArgument('config_file', default_value=default_config),
        DeclareLaunchArgument('plan_file', default_value=default_plan),
        DeclareLaunchArgument('use_sim', default_value='false'),
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
            launch_arguments={'use_sim': use_sim}.items(),
            condition=IfCondition(use_vision),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mission_planner.launch.py')),
            launch_arguments={
                'config_file': config_file,
                'plan_file': plan_file,
                'enable_control': enable_control,
            }.items(),
        ),
    ])

"""Bring up the full Marv AUV stack (ardusub + control + vision)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bringup_share = get_package_share_directory('marv_bringup')
    launch_dir = os.path.join(bringup_share, 'launch')

    use_ardusub = LaunchConfiguration('use_ardusub')
    use_control = LaunchConfiguration('use_control')
    use_vision = LaunchConfiguration('use_vision')
    use_front_cam = LaunchConfiguration('use_front_cam')
    use_down_cam = LaunchConfiguration('use_down_cam')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_ardusub',
            default_value='true',
            description='Start ardusub_node (pos_est + vehicle I/O).',
        ),
        DeclareLaunchArgument(
            'use_control',
            default_value='true',
            description='Start master_control_node.',
        ),
        DeclareLaunchArgument(
            'use_vision',
            default_value='true',
            description='Start vision launch group (camera nodes).',
        ),
        DeclareLaunchArgument(
            'use_front_cam',
            default_value='true',
            description='Start f_cam_node (only if use_vision is true).',
        ),
        DeclareLaunchArgument(
            'use_down_cam',
            default_value='true',
            description='Start d_cam_node (only if use_vision is true).',
        ),
        LogInfo(msg='Starting Marv AUV stack...'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ardusub.launch.py')),
            condition=IfCondition(use_ardusub),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'control.launch.py')),
            condition=IfCondition(use_control),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'vision.launch.py')),
            launch_arguments={
                'use_front_cam': use_front_cam,
                'use_down_cam': use_down_cam,
            }.items(),
            condition=IfCondition(use_vision),
        ),
    ])

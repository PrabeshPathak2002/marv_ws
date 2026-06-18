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

    use_mavros = LaunchConfiguration('use_mavros')
    use_ardusub = LaunchConfiguration('use_ardusub')
    use_control = LaunchConfiguration('use_control')
    use_vision = LaunchConfiguration('use_vision')
    fcu_url = LaunchConfiguration('fcu_url')
    use_front_cam = LaunchConfiguration('use_front_cam')
    use_down_cam = LaunchConfiguration('use_down_cam')
    enable_control = LaunchConfiguration('enable_control')
    command_backend = LaunchConfiguration('command_backend')
    target_depth_m = LaunchConfiguration('target_depth_m')
    use_sim = LaunchConfiguration('use_sim')
    use_unity_hil_bridge = LaunchConfiguration('use_unity_hil_bridge')
    active_behavior = LaunchConfiguration('active_behavior')
    config_file = LaunchConfiguration('config_file')
    use_ping_driver = LaunchConfiguration('use_ping_driver')
    use_ping = LaunchConfiguration('use_ping')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_mavros',
            default_value='true',
            description='Start MAVROS (ARK FPV over USB). Set false if mavros is already running.',
        ),
        DeclareLaunchArgument(
            'fcu_url',
            default_value='serial:///dev/ttyACM0:115200',
            description='MAVROS serial URL for ARK FPV on Jetson USB.',
        ),
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
        DeclareLaunchArgument(
            'enable_control',
            default_value='false',
            description='Master control publishes depth-hold cmd_vel (bench: keep false).',
        ),
        DeclareLaunchArgument(
            'command_backend',
            default_value='log_only',
            description='ardusub MAVROS output: log_only, mavros_rc, setpoint_velocity.',
        ),
        DeclareLaunchArgument(
            'target_depth_m',
            default_value='1.0',
            description='Depth hold target (meters).',
        ),
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Unity HITL: vision nodes use /unity/*/image_raw topics.',
        ),
        DeclareLaunchArgument(
            'use_unity_hil_bridge',
            default_value='false',
            description='Start unity_hil_bridge (Unity IMU/pose -> MAVROS HIL).',
        ),
        DeclareLaunchArgument(
            'active_behavior',
            default_value='depth_hold',
            description='Master control behavior when not using mission planner.',
        ),
        DeclareLaunchArgument(
            'config_file',
            default_value='',
            description='Optional marv.yaml path for behavior tuning.',
        ),
        DeclareLaunchArgument(
            'use_ping_driver',
            default_value='false',
            description='Start ping_sonar_ros Ping1D node (requires separate install).',
        ),
        DeclareLaunchArgument(
            'use_ping',
            default_value='true',
            description='ardusub_node subscribes to Ping range topic.',
        ),
        LogInfo(msg='Starting Marv AUV stack...'),
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
                os.path.join(launch_dir, 'unity_hil_bridge.launch.py')),
            condition=IfCondition(use_unity_hil_bridge),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ardusub.launch.py')),
            launch_arguments={
                'command_backend': command_backend,
                'use_ping': use_ping,
            }.items(),
            condition=IfCondition(use_ardusub),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'control.launch.py')),
            launch_arguments={
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
                'active_behavior': active_behavior,
                'config_file': config_file,
            }.items(),
            condition=IfCondition(use_control),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'vision.launch.py')),
            launch_arguments={
                'use_front_cam': use_front_cam,
                'use_down_cam': use_down_cam,
                'use_sim': use_sim,
            }.items(),
            condition=IfCondition(use_vision),
        ),
    ])

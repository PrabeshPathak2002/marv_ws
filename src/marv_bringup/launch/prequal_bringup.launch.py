"""Pre-qualification stack: MAVROS + ardusub + vision + prequal_plan."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


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
    sim_image_topic = LaunchConfiguration('sim_image_topic')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    use_ping_driver = LaunchConfiguration('use_ping_driver')
    ping_range_topic = LaunchConfiguration('ping_range_topic')
    use_mapping = LaunchConfiguration('use_mapping')
    camera_device = LaunchConfiguration('camera_device')
    fcu_mode = LaunchConfiguration('fcu_mode')
    auto_arm = LaunchConfiguration('auto_arm')
    hold_depth_with_autopilot = LaunchConfiguration('hold_depth_with_autopilot')
    depth_hold_enabled = LaunchConfiguration('depth_hold_enabled')
    show_debug_window = LaunchConfiguration('show_debug_window')
    vision_profile = LaunchConfiguration('vision_profile')
    model_path = LaunchConfiguration('model_path')

    return LaunchDescription([
        DeclareLaunchArgument('use_mavros', default_value='true'),
        DeclareLaunchArgument(
            'fcu_url',
            default_value='udp://@127.0.0.1:14555',
            description='MAVROS UDP via mavlink-router (start_mavlink_router.sh first).',
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
        DeclareLaunchArgument(
            'sim_image_topic',
            default_value='/unity/f_cam/image_raw',
            description='Front camera image topic when use_sim:=true.',
        ),
        DeclareLaunchArgument(
            'publish_debug_image',
            default_value='false',
            description='Publish annotated front camera on /f_cam/image_annotated.',
        ),
        DeclareLaunchArgument('use_ping_driver', default_value='false'),
        DeclareLaunchArgument(
            'camera_device',
            default_value='/dev/explore_hd',
            description='exploreHD V4L2 MJPEG device (/dev/explore_hd after udev setup).',
        ),
        DeclareLaunchArgument(
            'ping_device',
            default_value='/dev/ping_sonar',
            description='Ping1D USB serial (only when use_ping_driver:=true).',
        ),
        DeclareLaunchArgument(
            'ping_range_topic',
            default_value='/mavros/distance_sensor/lidar',
            description='Ping via FCU MAVROS (default). Use /ping1d/range for USB driver.',
        ),
        DeclareLaunchArgument(
            'ping_topic',
            default_value='/sensors/range_forward',
            description='Range topic for mapping_node (ardusub republish).',
        ),
        DeclareLaunchArgument(
            'use_mapping',
            default_value='true',
            description='Start mapping_node; missions use /sensors/map_pose.',
        ),
        DeclareLaunchArgument(
            'fcu_mode',
            default_value='ALT_HOLD',
            description='ArduSub mode set at startup (untethered: ALT_HOLD). Use MANUAL for bench.',
        ),
        DeclareLaunchArgument(
            'auto_arm',
            default_value='false',
            description='Arm after mode is set (use true for untethered competition).',
        ),
        DeclareLaunchArgument(
            'hold_depth_with_autopilot',
            default_value='true',
            description='FCU holds depth in ALT_HOLD; ROS sends surge/sway/yaw only.',
        ),
        DeclareLaunchArgument(
            'depth_hold_enabled',
            default_value='true',
            description='Master control heave from pose (disable for bench MANUAL).',
        ),
        DeclareLaunchArgument(
            'show_debug_window',
            default_value='false',
            description='Open f_cam OpenCV debug window on the Jetson display.',
        ),
        DeclareLaunchArgument(
            'vision_profile',
            default_value='prequal_cv',
            description='default | prequal (YOLO) | prequal_cv (OpenCV HSV) | prequal_hybrid (both).',
        ),
        DeclareLaunchArgument(
            'model_path',
            default_value='',
            description='Override YOLO weights (empty = profile default, e.g. front_model.pt).',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ping.launch.py')),
            launch_arguments={
                'use_ping_driver': 'true',
                'ping_device': LaunchConfiguration('ping_device'),
            }.items(),
            condition=IfCondition(use_ping_driver),
        ),
        Node(
            package='marv_bringup',
            executable='mavlink_ping_bridge',
            name='mavlink_ping_bridge',
            output='screen',
            parameters=[{
                'mavlink_url': 'udpin:127.0.0.1:14556',
                'topic': LaunchConfiguration('ping_range_topic'),
            }],
            condition=UnlessCondition(use_ping_driver),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mavros.launch.py')),
            launch_arguments={'fcu_url': fcu_url}.items(),
            condition=IfCondition(use_mavros),
        ),
        Node(
            package='marv_bringup',
            executable='fcu_setup_node',
            name='fcu_setup_node',
            output='screen',
            parameters=[{
                'fcu_mode': fcu_mode,
                'auto_arm': auto_arm,
                'arm_force': True,
                'mavlink_udp_port': 14555,
            }],
            condition=IfCondition(use_mavros),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'ardusub.launch.py')),
            launch_arguments={
                'command_backend': command_backend,
                'hold_depth_with_autopilot': hold_depth_with_autopilot,
                'ping_range_topic': ping_range_topic,
            }.items(),
            condition=IfCondition(use_ardusub),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'vision.launch.py')),
            launch_arguments={
                'use_sim': use_sim,
                'sim_image_topic': sim_image_topic,
                'use_down_cam': 'false',
                'vision_profile': vision_profile,
                'model_path': model_path,
                'f_cam_conf_threshold': '0.30',
                'camera_device': camera_device,
                'publish_debug_image': publish_debug_image,
                'show_debug_window': show_debug_window,
            }.items(),
            condition=IfCondition(use_vision),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mapping.launch.py')),
            launch_arguments={
                'ping_topic': LaunchConfiguration('ping_topic'),
            }.items(),
            condition=IfCondition(use_mapping),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mission_planner.launch.py')),
            launch_arguments={
                'config_file': config_file,
                'plan_file': plan_file,
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
                'pose_topic': '/sensors/map_pose',
                'depth_hold_enabled': depth_hold_enabled,
            }.items(),
            condition=IfCondition(use_mapping),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'mission_planner.launch.py')),
            launch_arguments={
                'config_file': config_file,
                'plan_file': plan_file,
                'enable_control': enable_control,
                'target_depth_m': target_depth_m,
                'pose_topic': '/sensors/pose',
                'depth_hold_enabled': depth_hold_enabled,
            }.items(),
            condition=UnlessCondition(use_mapping),
        ),
    ])

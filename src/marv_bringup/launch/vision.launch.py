"""Launch marv_vision camera nodes."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_front_cam = LaunchConfiguration('use_front_cam')
    use_down_cam = LaunchConfiguration('use_down_cam')
    use_sim = LaunchConfiguration('use_sim')
    vision_profile = LaunchConfiguration('vision_profile')
    f_cam_conf = LaunchConfiguration('f_cam_conf_threshold')
    model_path = LaunchConfiguration('model_path')

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
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Unity HITL mode: subscribe to /unity/*/image_raw instead of USB cameras.',
        ),
        DeclareLaunchArgument(
            'vision_profile',
            default_value='default',
            description='default | prequal (YOLO) | prequal_cv (OpenCV HSV/lines).',
        ),
        DeclareLaunchArgument(
            'f_cam_conf_threshold',
            default_value='0.30',
            description='YOLO confidence threshold for front camera.',
        ),
        DeclareLaunchArgument(
            'model_path',
            default_value='',
            description='Override YOLO weights path (empty = use profile default).',
        ),
        Node(
            package='marv_vision',
            executable='f_cam_node',
            name='f_cam_node',
            output='screen',
            parameters=[{
                'use_sim': use_sim,
                'vision_profile': vision_profile,
                'conf_threshold': f_cam_conf,
                'model_path': model_path,
            }],
            condition=IfCondition(use_front_cam),
        ),
        Node(
            package='marv_vision',
            executable='d_cam_node',
            name='d_cam_node',
            output='screen',
            parameters=[{'use_sim': use_sim}],
            condition=IfCondition(use_down_cam),
        ),
    ])

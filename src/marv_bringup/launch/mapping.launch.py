"""Launch marv_mapping node."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('pose_topic', default_value='/sensors/pose'),
        DeclareLaunchArgument(
            'ping_topic',
            default_value='/sensors/range_forward',
            description='Forward range from ardusub_node (FCU Ping or USB driver).',
        ),
        DeclareLaunchArgument('vision_topic', default_value='/f_cam/detections'),
        DeclareLaunchArgument('imu_topic', default_value='/mavros/imu/data'),
        DeclareLaunchArgument('image_width', default_value='1280'),
        DeclareLaunchArgument('update_rate_hz', default_value='10.0'),
        Node(
            package='marv_mapping',
            executable='mapping_node',
            name='mapping_node',
            output='screen',
            parameters=[{
                'pose_topic': LaunchConfiguration('pose_topic'),
                'ping_topic': LaunchConfiguration('ping_topic'),
                'vision_topic': LaunchConfiguration('vision_topic'),
                'imu_topic': LaunchConfiguration('imu_topic'),
                'image_width': LaunchConfiguration('image_width'),
                'update_rate_hz': LaunchConfiguration('update_rate_hz'),
            }],
        ),
    ])

"""Launch marv_ardusub (position estimate + MAVROS actuation)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    command_backend = LaunchConfiguration('command_backend')
    use_ping = LaunchConfiguration('use_ping')
    hold_depth_with_autopilot = LaunchConfiguration('hold_depth_with_autopilot')
    publish_pose = LaunchConfiguration('publish_pose')
    ping_range_topic = LaunchConfiguration('ping_range_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'command_backend',
            default_value='log_only',
            description=(
                'How to send cmd_vel to MAVROS: log_only, mavros_rc, '
                'setpoint_velocity, or disabled.'
            ),
        ),
        DeclareLaunchArgument(
            'use_ping',
            default_value='true',
            description='Subscribe to Ping1D range and publish /sensors/range_forward.',
        ),
        DeclareLaunchArgument(
            'hold_depth_with_autopilot',
            default_value='false',
            description='ALT_HOLD/MANUAL holds depth; do not override vertical RC from /cmd_vel heave.',
        ),
        DeclareLaunchArgument(
            'publish_pose',
            default_value='true',
            description='Publish /sensors/pose from MAVROS. Set false when Gazebo pose bridge is used.',
        ),
        DeclareLaunchArgument(
            'ping_range_topic',
            default_value='/ping1d/range',
            description='sensor_msgs/Range topic from Ping driver or MAVROS.',
        ),
        Node(
            package='marv_ardusub',
            executable='ardusub_node',
            name='ardusub_node',
            output='screen',
            parameters=[{
                'command_backend': command_backend,
                'use_ping': use_ping,
                'hold_depth_with_autopilot': hold_depth_with_autopilot,
                'publish_pose': publish_pose,
                'ping_range_topic': ping_range_topic,
            }],
        ),
    ])

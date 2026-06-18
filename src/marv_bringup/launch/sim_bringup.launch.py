"""Unity simulation bringup — isolated from bench-safe marv_bringup.launch.py defaults.

Starts ROS-TCP-Endpoint, MAVROS (ARK FPV USB), Unity HITL bridge, sim vision,
and master control. Optionally starts ardusub_node for /sensors/pose (MAVROS
odom only) and cmd_vel forwarding — does not publish HIL data (unity_hil_bridge
owns that path).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    fcu_url = LaunchConfiguration('fcu_url')
    ros_tcp_port = LaunchConfiguration('ros_tcp_port')
    enable_control = LaunchConfiguration('enable_control')
    active_behavior = LaunchConfiguration('active_behavior')
    target_depth_m = LaunchConfiguration('target_depth_m')
    use_pos_est_stack = LaunchConfiguration('use_pos_est_stack')
    command_backend = LaunchConfiguration('command_backend')

    return LaunchDescription([
        DeclareLaunchArgument(
            'fcu_url',
            default_value='serial:///dev/ttyACM0:115200',
            description='MAVROS serial URL for ARK FPV over USB.',
        ),
        DeclareLaunchArgument(
            'ros_tcp_port',
            default_value='10000',
            description='ROS-TCP-Endpoint port for Unity.',
        ),
        DeclareLaunchArgument(
            'enable_control',
            default_value='false',
            description='Enable master_control cmd_vel output.',
        ),
        DeclareLaunchArgument(
            'active_behavior',
            default_value='traverse_gate',
            description='master_control behavior for simulation.',
        ),
        DeclareLaunchArgument(
            'target_depth_m',
            default_value='1.0',
            description='Depth hold target when control enabled.',
        ),
        DeclareLaunchArgument(
            'use_pos_est_stack',
            default_value='true',
            description=(
                'Launch ardusub_node: reads /mavros/local_position/odom -> '
                '/sensors/pose and forwards cmd_vel (no HIL overlap).'
            ),
        ),
        DeclareLaunchArgument(
            'command_backend',
            default_value='mavros_rc',
            description='ardusub MAVROS actuation backend for simulation.',
        ),
        LogInfo(msg='Starting Marv Unity simulation stack (sim_bringup)...'),
        # 1. ROS-TCP-Endpoint (Unity network socket)
        Node(
            package='ros_tcp_endpoint',
            executable='default_server_endpoint',
            name='UnityRoboticsTCPEndpoint',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'ROS_IP': '0.0.0.0'},
                {'ROS_TCP_PORT': ros_tcp_port},
            ],
        ),
        # 2. MAVROS (ARK FPV via USB)
        Node(
            package='mavros',
            executable='mavros_node',
            name='mavros',
            output='screen',
            parameters=[{'fcu_url': fcu_url}],
        ),
        # 3. Unity HITL bridge (Unity sensors -> MAVROS HIL, RC -> Unity)
        Node(
            package='marv_ardusub',
            executable='unity_hil_bridge',
            name='unity_hil_bridge',
            output='screen',
        ),
        # 4. Vision stack (Unity image topics, not physical cameras)
        Node(
            package='marv_vision',
            executable='f_cam_node',
            name='f_cam_node',
            output='screen',
            parameters=[{'use_sim': True}],
        ),
        Node(
            package='marv_vision',
            executable='d_cam_node',
            name='d_cam_node',
            output='screen',
            parameters=[{'use_sim': True}],
        ),
        # 5. Control stack
        Node(
            package='marv_control',
            executable='master_control_node',
            name='master_control_node',
            output='screen',
            parameters=[{
                'enable_control': enable_control,
                'active_behavior': active_behavior,
                'target_depth_m': target_depth_m,
            }],
        ),
        # Optional: pos_est via ardusub (MAVROS odom in, cmd_vel out — no HIL publish)
        Node(
            package='marv_ardusub',
            executable='ardusub_node',
            name='ardusub_node',
            output='screen',
            parameters=[{'command_backend': command_backend}],
            condition=IfCondition(use_pos_est_stack),
        ),
    ])

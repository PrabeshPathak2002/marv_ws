"""Launch MAVROS via MAVProxy local UDP (not direct serial)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from marv_bringup.serial_devices import DEFAULT_MAVROS_FCU_URL, default_mavros_fcu_url


def _launch_mavros(context, *args, **kwargs):
    marv_share = get_package_share_directory('marv_bringup')

    fcu_url = LaunchConfiguration('fcu_url').perform(context)
    if fcu_url in ('auto', ''):
        fcu_url = default_mavros_fcu_url()

    apm_config = '/opt/ros/humble/share/mavros/launch/apm_config.yaml'
    params = [
        apm_config,
        os.path.join(marv_share, 'config', 'mavros_config.yaml'),
        {'fcu_url': fcu_url},
        os.path.join(marv_share, 'config', 'mavros_pluginlists.yaml'),
    ]

    return [
        LogInfo(msg=f'MAVROS fcu_url: {fcu_url}'),
        Node(
            package='mavros',
            executable='mavros_node',
            name='mavros',
            output='screen',
            parameters=params,
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'fcu_url',
            default_value=DEFAULT_MAVROS_FCU_URL,
            description=(
                'MAVROS FCU URL. Default udp://@127.0.0.1:14555 listens for '
                'MAVProxy (--out=udp:127.0.0.1:14555). Start MAVProxy first: '
                '~/marv_ws/start_telemetry_bridge.sh'
            ),
        ),
        OpaqueFunction(function=_launch_mavros),
    ])

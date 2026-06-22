"""Launch MAVROS connected to ARK FPV over USB."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from marv_bringup.serial_devices import resolve_fcu_url


def _launch_mavros(context, *args, **kwargs):
    marv_share = get_package_share_directory('marv_bringup')
    mavros_share = get_package_share_directory('mavros')

    fcu_url = LaunchConfiguration('fcu_url').perform(context)
    if fcu_url in ('auto', ''):
        fcu_url = resolve_fcu_url()

    return [
        LogInfo(msg=f'MAVROS fcu_url: {fcu_url}'),
        Node(
            package='mavros',
            executable='mavros_node',
            name='mavros',
            output='screen',
            parameters=[
                {'fcu_url': fcu_url},
                os.path.join(marv_share, 'config', 'mavros_pluginlists.yaml'),
            ],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'fcu_url',
            default_value='auto',
            description='MAVROS FCU URL: auto resolves ARK FPV /dev/serial/by-id path.',
        ),
        OpaqueFunction(function=_launch_mavros),
    ])

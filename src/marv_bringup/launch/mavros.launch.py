"""Launch MAVROS connected to ARK FPV over USB."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    marv_share = get_package_share_directory('marv_bringup')
    mavros_share = get_package_share_directory('mavros')
    fcu_url = LaunchConfiguration('fcu_url')

    return LaunchDescription([
        DeclareLaunchArgument(
            'fcu_url',
            default_value='serial:///dev/ttyACM0:115200',
            description='MAVROS FCU connection URL (ARK FPV on Jetson USB).',
        ),
        Node(
            package='mavros',
            executable='mavros_node',
            name='mavros',
            output='screen',
            parameters=[
                {'fcu_url': fcu_url},
                os.path.join(marv_share, 'config', 'mavros_pluginlists.yaml'),
                os.path.join(mavros_share, 'launch', 'apm_config.yaml'),
            ],
        ),
    ])

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
    camera_device = LaunchConfiguration('camera_device')
    image_width = LaunchConfiguration('image_width')
    image_height = LaunchConfiguration('image_height')
    frame_fps = LaunchConfiguration('frame_fps')
    fourcc = LaunchConfiguration('fourcc')
    sim_image_topic = LaunchConfiguration('sim_image_topic')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    show_debug_window = LaunchConfiguration('show_debug_window')

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
            description='default | prequal (YOLO) | prequal_cv (OpenCV HSV/lines) | prequal_hybrid (both).',
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
        DeclareLaunchArgument(
            'camera_device',
            default_value='/dev/explore_hd',
            description='exploreHD V4L2 MJPEG device (/dev/explore_hd after udev setup).',
        ),
        DeclareLaunchArgument(
            'image_width',
            default_value='1280',
            description='Capture width (exploreHD 720p default).',
        ),
        DeclareLaunchArgument(
            'image_height',
            default_value='720',
            description='Capture height.',
        ),
        DeclareLaunchArgument(
            'frame_fps',
            default_value='30.0',
            description='Requested capture frame rate.',
        ),
        DeclareLaunchArgument(
            'fourcc',
            default_value='MJPG',
            description='V4L2 pixel format (MJPG recommended for exploreHD).',
        ),
        DeclareLaunchArgument(
            'sim_image_topic',
            default_value='/unity/f_cam/image_raw',
            description='Image topic when use_sim=true (Unity or Gazebo bridge).',
        ),
        DeclareLaunchArgument(
            'publish_debug_image',
            default_value='false',
            description='Publish annotated front camera on /f_cam/image_annotated.',
        ),
        DeclareLaunchArgument(
            'show_debug_window',
            default_value='false',
            description='Open local OpenCV window with detection overlays.',
        ),
        Node(
            package='marv_vision',
            executable='f_cam_node',
            name='f_cam_node',
            output='screen',
            parameters=[{
                'use_sim': use_sim,
                'sim_image_topic': sim_image_topic,
                'vision_profile': vision_profile,
                'conf_threshold': f_cam_conf,
                'model_path': model_path,
                'camera_device': camera_device,
                'image_width': image_width,
                'image_height': image_height,
                'frame_fps': frame_fps,
                'fourcc': fourcc,
                'publish_debug_image': publish_debug_image,
                'show_debug_window': show_debug_window,
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

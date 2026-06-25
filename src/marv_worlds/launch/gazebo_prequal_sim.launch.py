"""Gazebo pre-qual: marv_prequal_sim world + Marv AUV + vision + prequal stack."""

import os
import shutil

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _gz_binary() -> str:
    gz = shutil.which('gz')
    if gz:
        return gz
    raise RuntimeError(
        'Gazebo Sim not found (gz). Install:\n'
        '  sudo apt install gz-tools2 gz-sim8-cli libgz-sim8-plugins '
        'python3-gz-transport13 python3-gz-msgs10'
    )


def _gz_resource_path() -> str:
    paths = []
    for pkg in ('marv_worlds', 'bb_worlds'):
        try:
            share = get_package_share_directory(pkg)
            paths.extend([os.path.join(share, 'models'), share])
        except Exception:
            pass
    home = os.path.expanduser('~')
    for extra in ('bluerov2_gz/models', 'bluerov2_gz/worlds', 'ardupilot_gazebo/models'):
        p = os.path.join(home, *extra.split('/'))
        if os.path.isdir(p):
            paths.append(p)
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if existing:
        paths.append(existing)
    seen = set()
    return ':'.join(p for p in paths if p and not (p in seen or seen.add(p)))


def _plugin_path() -> str:
    paths = []
    ap = os.path.join(os.path.expanduser('~'), 'ardupilot_gazebo', 'build')
    if os.path.isdir(ap):
        paths.append(ap)
    existing = os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')
    if existing:
        paths.append(existing)
    return ':'.join(paths)


def _engine_plugin_env() -> dict:
    """Symlink versioned physics/rendering plugins to names gz-sim 8.14 expects."""
    import subprocess

    script = os.path.expanduser('~/marv_ws/scripts/gz_plugin_path_setup.sh')
    if os.path.isfile(script):
        proc = subprocess.run(
            ['bash', '-c', f'source "{script}" && env'],
            capture_output=True,
            text=True,
            check=False,
        )
        env = {}
        for line in proc.stdout.splitlines():
            if line.startswith('GZ_SIM_PHYSICS_ENGINE_PATH='):
                env['GZ_SIM_PHYSICS_ENGINE_PATH'] = line.split('=', 1)[1]
            elif line.startswith('GZ_SIM_RENDER_ENGINE_PATH='):
                env['GZ_SIM_RENDER_ENGINE_PATH'] = line.split('=', 1)[1]
            elif line.startswith('GZ_RENDERING_RESOURCE_PATH='):
                env['GZ_RENDERING_RESOURCE_PATH'] = line.split('=', 1)[1]
            elif line.startswith('LIBGL_ALWAYS_SOFTWARE='):
                env['LIBGL_ALWAYS_SOFTWARE'] = line.split('=', 1)[1]
        if env:
            return env
    return {
        'GZ_SIM_PHYSICS_ENGINE_PATH': os.environ.get('GZ_SIM_PHYSICS_ENGINE_PATH', ''),
        'GZ_SIM_RENDER_ENGINE_PATH': os.environ.get('GZ_SIM_RENDER_ENGINE_PATH', ''),
    }


def _launch_setup(context, *args, **kwargs):
    marv_share = get_package_share_directory('marv_worlds')
    bringup_share = get_package_share_directory('marv_bringup')

    vision_only = LaunchConfiguration('vision_only').perform(context).lower() == 'true'
    headless = LaunchConfiguration('headless').perform(context).lower() == 'true'
    enable_control = LaunchConfiguration('enable_control').perform(context)
    auto_arm = LaunchConfiguration('auto_arm').perform(context)
    fcu_url = LaunchConfiguration('fcu_url').perform(context)
    publish_debug = LaunchConfiguration('publish_debug_image').perform(context)
    spawn_delay = float(LaunchConfiguration('spawn_delay').perform(context))
    world_arg = LaunchConfiguration('world').perform(context).strip()
    start_sitl = LaunchConfiguration('start_sitl').perform(context).lower() == 'true'

    if world_arg:
        world_name = world_arg
    elif vision_only:
        world_name = 'marv_prequal_sim'
    else:
        world_name = 'marv_prequal_full'

    world_path = os.path.join(marv_share, 'worlds', f'{world_name}.world')
    if not os.path.isfile(world_path):
        fallback = 'marv_prequal_simple' if vision_only else 'marv_prequal_sim'
        world_name = fallback
        world_path = os.path.join(marv_share, 'worlds', f'{world_name}.world')

    auv_name = 'marv_auv_simple' if vision_only else 'marv_auv'
    embed_auv = (not vision_only) and world_name.endswith('_full')
    model_path = os.path.join(marv_share, 'models', auv_name, 'model.sdf')
    if not embed_auv and not os.path.isfile(model_path):
        raise RuntimeError(f'AUV model missing: {model_path}')

    spawn_z = '-2.0' if 'prequal' in world_name else '-1.5'

    gz_cmd = [_gz_binary(), 'sim']
    if headless:
        gz_cmd.append('-s')
    gz_cmd.extend(['-r', world_path])

    if vision_only:
        camera_gz = (
            f'/world/{world_name}/model/{auv_name}/link/base_link/'
            'sensor/explore_hd_camera/image'
        )
    else:
        camera_gz = '/explore_hd'
    camera_ros = '/gazebo/f_cam/image_raw'
    pose_gz = f'/world/{world_name}/model/{auv_name}/pose'

    gz_env = {
        'GZ_SIM_RESOURCE_PATH': _gz_resource_path(),
        'GZ_SIM_SYSTEM_PLUGIN_PATH': _plugin_path(),
    }
    gz_env.update({k: v for k, v in _engine_plugin_env().items() if v})

    # ros-humble-ros-gz uses ignition-transport11; Gazebo Sim 8 uses gz-transport13.
    # Native Python bridges talk to the running simulator directly.
    bridge_clock = Node(
        package='marv_worlds',
        executable='gz_clock_bridge.py',
        name='gazebo_clock_bridge',
        output='screen',
        parameters=[{
            'gz_topic': f'/world/{world_name}/clock',
            'ros_topic': '/clock',
        }],
    )

    bridge_camera = Node(
        package='marv_worlds',
        executable='gz_image_bridge.py',
        name='gazebo_front_camera_bridge',
        output='screen',
        parameters=[{
            'gz_topic': camera_gz,
            'ros_topic': camera_ros,
            'frame_id': 'explore_hd_optical_frame',
        }],
    )

    bridge_pose = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[f'{pose_gz}@geometry_msgs/msg/PoseStamped[gz.msgs.Pose'],
        remappings=[(pose_gz, pose_gz)],
    )

    pose_relay = Node(
        package='marv_worlds',
        executable='gz_pose_bridge.py',
        name='gz_pose_bridge',
        output='screen',
        parameters=[{
            'gz_pose_topic': pose_gz,
            'output_topic': '/sensors/pose',
        }],
    )

    if vision_only:
        prequal_args = {
            'use_mavros': 'false',
            'use_ardusub': 'false',
            'use_sim': 'true',
            'sim_image_topic': camera_ros,
            'use_vision': 'true',
            'use_ping_driver': 'false',
            'use_mapping': 'false',
            'enable_control': 'false',
            'command_backend': 'log_only',
            'publish_debug_image': publish_debug,
        }
    else:
        prequal_args = {
            'use_mavros': 'true',
            'use_ardusub': 'true',
            'use_sim': 'true',
            'sim_image_topic': camera_ros,
            'use_vision': 'true',
            'use_ping_driver': 'false',
            'use_mapping': 'true',
            'enable_control': enable_control,
            'command_backend': 'mavros_rc',
            'fcu_url': fcu_url,
            'fcu_mode': 'ALT_HOLD',
            'auto_arm': auto_arm,
            'hold_depth_with_autopilot': 'true',
            'target_depth_m': '1.0',
            'publish_debug_image': publish_debug,
        }

    prequal = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'prequal_bringup.launch.py'),
        ),
        launch_arguments=prequal_args.items(),
    )

    actions = [
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', gz_env['GZ_SIM_RESOURCE_PATH']),
        SetEnvironmentVariable('GZ_SIM_SYSTEM_PLUGIN_PATH', gz_env['GZ_SIM_SYSTEM_PLUGIN_PATH']),
        ExecuteProcess(cmd=gz_cmd, output='screen', additional_env=gz_env),
        TimerAction(
            period=5.0,
            actions=[ExecuteProcess(
                cmd=[
                    os.path.expanduser('~/marv_ws/scripts/gz_unpause_world.sh'),
                    world_name,
                    '90',
                ],
                output='screen',
            )],
        ),
    ]

    if embed_auv:
        # AUV is in the world file — wait for heavy bb pool to load, then SITL, then ROS stack.
        sitl_delay = float(LaunchConfiguration('sitl_delay').perform(context))
        stack_delay = float(LaunchConfiguration('stack_delay').perform(context))
        bridges = [bridge_clock, bridge_camera]
        actions.append(TimerAction(period=sitl_delay, actions=[_sitl_process(gz_env)]))
        actions.append(TimerAction(period=stack_delay, actions=bridges + [prequal]))
    else:
        spawn_process = ExecuteProcess(
            cmd=[
                'ros2', 'run', 'marv_worlds', 'gz_spawn_with_retry.py',
                '--world', world_name,
                '--name', auv_name,
                '--file', model_path,
                '--x', '0', '--y', '0', '--z', spawn_z,
                '--delay', '5',
                '--retries', '36',
            ],
            output='screen',
            additional_env=gz_env,
        )
        post_spawn = [bridge_clock, bridge_camera]
        if vision_only:
            post_spawn.extend([bridge_pose, pose_relay])
            post_spawn.append(TimerAction(period=3.0, actions=[prequal]))
        elif start_sitl:
            post_spawn.append(TimerAction(period=2.0, actions=[_sitl_process(gz_env)]))
            post_spawn.append(TimerAction(period=20.0, actions=[prequal]))
        else:
            post_spawn.append(TimerAction(period=3.0, actions=[prequal]))
        actions.append(TimerAction(period=spawn_delay, actions=[spawn_process]))
        actions.append(RegisterEventHandler(
            OnProcessExit(target_action=spawn_process, on_exit=post_spawn),
        ))

    return actions


def _sitl_process(gz_env: dict) -> ExecuteProcess:
    script = os.path.expanduser('~/marv_ws/scripts/wait_for_gz_auv_and_start_sitl.sh')
    return ExecuteProcess(cmd=[script], output='screen', additional_env=gz_env)


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='',
            description='World without .world suffix. Full sim default: marv_prequal_full.',
        ),
        DeclareLaunchArgument(
            'vision_only',
            default_value='true',
            description='true: lightweight AUV + vision. false: BlueROV heavy + ArduSub.',
        ),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('spawn_delay', default_value='15.0'),
        DeclareLaunchArgument(
            'sitl_delay',
            default_value='25.0',
            description='Seconds after Gazebo start before SITL (embedded-AUV worlds).',
        ),
        DeclareLaunchArgument(
            'stack_delay',
            default_value='40.0',
            description='Seconds after Gazebo start before MAVROS/prequal (after SITL).',
        ),
        DeclareLaunchArgument('enable_control', default_value='false'),
        DeclareLaunchArgument('auto_arm', default_value='false'),
        DeclareLaunchArgument(
            'start_sitl',
            default_value='false',
            description='When spawning AUV dynamically, start SITL after spawn.',
        ),
        DeclareLaunchArgument('fcu_url', default_value='udp://@127.0.0.1:14555'),
        DeclareLaunchArgument('publish_debug_image', default_value='true'),
        OpaqueFunction(function=_launch_setup),
    ])

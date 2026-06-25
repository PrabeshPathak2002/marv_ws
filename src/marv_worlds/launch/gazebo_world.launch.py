"""Launch Gazebo Sim with a Marv mission world (bb_worlds assets by default)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration

# Keep in sync with scripts/generate_worlds.py
MISSION_WORLD_MAP = {
    'prequal': 'marv_prequal',
    'wait_submerged': 'marv_task_wait_submerged',
    'find_gate': 'marv_task_find_gate',
    'traverse_gate': 'marv_task_traverse_gate',
    'pass_gate': 'marv_task_pass_gate',
    'pass_gate_clear': 'marv_task_pass_gate_clear',
    'transit_forward': 'marv_task_transit',
    'find_marker': 'marv_task_find_marker',
    'approach_marker': 'marv_task_approach_marker',
    'circle_marker': 'marv_task_circle_marker',
    'turn_around': 'marv_task_turn_around',
    'find_return_gate': 'marv_task_find_return_gate',
    'hold': 'marv_task_hold',
    'detect_path': 'marv_task_detect_path',
    'return_home': 'marv_task_return_home',
    'depth_hold': 'marv_task_depth_hold',
    'pool': 'marv_pool',
    'competition': 'marv_competition',
}

MISSION_WORLD_MAP_SIMPLE = {
    'prequal': 'marv_prequal_simple',
    'find_gate': 'marv_task_find_gate_simple',
    'traverse_gate': 'marv_task_traverse_gate_simple',
    'circle_marker': 'marv_task_circle_marker_simple',
    'pool': 'marv_pool_simple',
}


def _bb_worlds_paths() -> list[str]:
    paths = []
    # Installed bb_worlds (preferred).
    try:
        bb_share = get_package_share_directory('bb_worlds')
        paths.extend([
            os.path.join(bb_share, 'models'),
            bb_share,
        ])
    except Exception:
        pass
    # Source tree (works before bb_worlds is installed).
    ws_root = os.environ.get('MARV_WS', os.path.expanduser('~/marv_ws'))
    src_models = os.path.join(ws_root, 'src', 'bb_worlds', 'models')
    if os.path.isdir(src_models):
        paths.append(src_models)
    src_share = os.path.join(ws_root, 'src', 'bb_worlds')
    if os.path.isdir(src_share):
        paths.append(src_share)
    return paths


def _gz_resource_path(marv_share: str) -> str:
    paths = [
        os.path.join(marv_share, 'models'),
        marv_share,
    ]
    paths.extend(_bb_worlds_paths())
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if existing:
        paths.append(existing)
    # De-dupe while preserving order.
    seen = set()
    unique = []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    return ':'.join(unique)


def _launch_gz(context, *args, **kwargs):
    mission = LaunchConfiguration('mission').perform(context)
    world = LaunchConfiguration('world').perform(context)
    use_simple = LaunchConfiguration('use_simple').perform(context).lower() == 'true'
    headless = LaunchConfiguration('headless').perform(context).lower() == 'true'
    paused = LaunchConfiguration('paused').perform(context).lower() == 'true'

    if not world:
        world_map = MISSION_WORLD_MAP_SIMPLE if use_simple else MISSION_WORLD_MAP
        world = world_map.get(mission, 'marv_pool' if not use_simple else 'marv_pool_simple')

    marv_share = get_package_share_directory('marv_worlds')
    world_path = os.path.join(marv_share, 'worlds', f'{world}.world')
    if not os.path.isfile(world_path):
        raise RuntimeError(f'World not found: {world_path}')

    cmd = ['gz', 'sim']
    if headless:
        cmd.append('-s')
    if not paused:
        cmd.append('-r')
    cmd.append(world_path)

    return [
        ExecuteProcess(
            cmd=cmd,
            output='screen',
            shell=False,
            additional_env={
                'GZ_SIM_RESOURCE_PATH': _gz_resource_path(marv_share),
            },
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'mission',
            default_value='prequal',
            description='Marv mission key (prequal, traverse_gate, circle_marker, …).',
        ),
        DeclareLaunchArgument(
            'world',
            default_value='',
            description='Override world base name (without .world).',
        ),
        DeclareLaunchArgument(
            'use_simple',
            default_value='false',
            description='Use procedural fallback worlds (no bb_worlds meshes).',
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run gz sim server only (no GUI).',
        ),
        DeclareLaunchArgument(
            'paused',
            default_value='false',
            description='Start simulation paused.',
        ),
        OpaqueFunction(function=_launch_gz),
    ])

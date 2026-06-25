#!/usr/bin/env python3
"""Wait for Gazebo world, spawn AUV once, confirm model topics exist."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


def _topics() -> str:
    try:
        proc = subprocess.run(
            ['gz', 'topic', '-l'],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return proc.stdout or ''
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ''


def _model_present(name: str, world: str) -> bool:
    topics = _topics()
    if f'/model/{name}/' in topics:
        return True
    if f'/world/{world}/model/{name}/' in topics:
        return True
    return False


def _world_ready(world: str) -> bool:
    return f'/world/{world}/clock' in _topics()


def _spawn_gz(world: str, name: str, sdf: str, x: str, y: str, z: str) -> bool:
    req = (
        f'sdf_filename: "{sdf}", '
        f'name: "{name}", '
        f'pose: {{position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{w: 1.0}}}}'
    )
    proc = subprocess.run(
        [
            'gz', 'service',
            '-s', f'/world/{world}/create',
            '--reqtype', 'gz.msgs.EntityFactory',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '120000',
            '--req', req,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or '') + (proc.stderr or '')
    if out.strip():
        print(out, end='', flush=True)
    return 'data: true' in out.lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--world', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--file', required=True)
    parser.add_argument('--x', default='0')
    parser.add_argument('--y', default='0')
    parser.add_argument('--z', default='-2')
    parser.add_argument('--delay', type=float, default=5.0)
    parser.add_argument('--retries', type=int, default=36)
    args = parser.parse_args()

    if _model_present(args.name, args.world):
        print(
            f'[gz_spawn_with_retry] model {args.name} already in {args.world}',
            flush=True,
        )
        return

    for attempt in range(1, args.retries + 1):
        if not _world_ready(args.world):
            print(
                f'[gz_spawn_with_retry] waiting for world {args.world} '
                f'({attempt}/{args.retries})',
                flush=True,
            )
            time.sleep(args.delay)
            continue

        if _model_present(args.name, args.world):
            print(
                f'[gz_spawn_with_retry] OK: {args.name} is in world {args.world}',
                flush=True,
            )
            return

        print(
            f'[gz_spawn_with_retry] spawn attempt {attempt}/{args.retries}: '
            f'{args.name} -> {args.world}',
            flush=True,
        )
        _spawn_gz(args.world, args.name, args.file, args.x, args.y, args.z)

        for _ in range(12):
            time.sleep(1.0)
            if _model_present(args.name, args.world):
                print(
                    f'[gz_spawn_with_retry] OK: {args.name} is in world {args.world}',
                    flush=True,
                )
                return

        if attempt < args.retries:
            time.sleep(args.delay)

    print(
        f'[gz_spawn_with_retry] FAILED: could not spawn {args.name} in {args.world}',
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)


if __name__ == '__main__':
    main()

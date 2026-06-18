"""Tests for demo replay loader."""

import json
import tempfile

from marv_control.demo_replay_node import load_demo_samples


def test_load_demo_samples_reads_cmd_timeline():
  with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as handle:
    handle.write(json.dumps({'type': 'meta', 't': 0.0}) + '\n')
    handle.write(json.dumps({
        'type': 'sample',
        't': 0.0,
        'cmd': {'surge': 0.3, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.1},
    }) + '\n')
    handle.write(json.dumps({
        'type': 'sample',
        't': 1.0,
        'cmd': {'surge': 0.0, 'sway': 0.2, 'heave': 0.0, 'yaw': 0.0},
    }) + '\n')
    path = handle.name

  samples, duration = load_demo_samples(path)
  assert len(samples) == 2
  assert duration == 1.0
  assert samples[0]['cmd']['surge'] == 0.3
  assert samples[1]['cmd']['sway'] == 0.2

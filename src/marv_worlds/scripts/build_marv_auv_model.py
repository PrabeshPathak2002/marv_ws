#!/usr/bin/env python3
"""Build marv_auv SDF from bluerov2_heavy + exploreHD front camera."""

from pathlib import Path

EXPLORE_HD_CAMERA = """
      <!-- Deep Water Exploration exploreHD (1280x720 MJPEG equivalent in sim) -->
      <sensor name="explore_hd_camera" type="camera">
        <pose>0.22 0 0.04 0 0 0</pose>
        <always_on>1</always_on>
        <update_rate>30</update_rate>
        <visualize>true</visualize>
        <topic>explore_hd</topic>
        <camera>
          <horizontal_fov>1.3962634</horizontal_fov>
          <image>
            <width>1280</width>
            <height>720</height>
            <format>R8G8B8</format>
          </image>
          <clip>
            <near>0.15</near>
            <far>40</far>
          </clip>
        </camera>
      </sensor>
"""

# Do not rewrite model://bluerov2_heavy/meshes/ URIs — meshes stay in bluerov2_gz.
REPLACEMENTS = [
    ('<model name="bluerov2_heavy">', '<model name="marv_auv">'),
    ('namespace>bluerov2</namespace>', 'namespace>marv_auv</namespace>'),
    ('namespace>bluerov2_heavy</namespace>', 'namespace>marv_auv</namespace>'),
    ('/model/bluerov2_heavy/', '/model/marv_auv/'),
    ('/model/bluerov2/', '/model/marv_auv/'),
]


def main() -> None:
    ws = Path.home() / 'marv_ws'
    src = Path.home() / 'bluerov2_gz' / 'models' / 'bluerov2_heavy' / 'model.sdf'
    if not src.is_file():
        src = ws.parent / 'bluerov2_gz' / 'models' / 'bluerov2_heavy' / 'model.sdf'
    if not src.is_file():
        raise SystemExit(f'bluerov2_heavy model not found: {src}')

    out_dir = Path(__file__).resolve().parent.parent / 'models' / 'marv_auv'
    out_dir.mkdir(parents=True, exist_ok=True)

    text = src.read_text(encoding='utf-8')
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    imu_end = '        <update_rate>1000.0</update_rate>\n      </sensor>'
    if imu_end not in text:
        raise SystemExit('Unexpected bluerov2_heavy SDF layout — update build script.')
    text = text.replace(imu_end, imu_end + EXPLORE_HD_CAMERA, 1)

    (out_dir / 'model.sdf').write_text(text, encoding='utf-8')
    (out_dir / 'model.config').write_text(
        """<?xml version="1.0"?>
<model>
  <name>marv_auv</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>EagleAUV</name></author>
  <description>Marv AUV (BlueROV2 Heavy 6DOF + exploreHD camera) for Gazebo + ArduSub SITL.</description>
</model>
""",
        encoding='utf-8',
    )
    print(f'wrote {out_dir / "model.sdf"}')


if __name__ == '__main__':
    main()

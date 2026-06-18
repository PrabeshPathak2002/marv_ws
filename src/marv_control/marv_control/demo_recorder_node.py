#!/usr/bin/env python3
"""Record manual teleop demos: cmd_vel, pose, vision, and phase markers."""

import json
import math
import os
from datetime import datetime

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from rclpy.node import Node
from std_msgs.msg import String

from marv_control.lib.pose_utils import normalize_angle


def _yaw_from_orientation(q):
  siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
  cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
  return normalize_angle(math.atan2(siny_cosp, cosy_cosp))


class DemoRecorder(Node):
  """Write timestamped JSON lines for later autonomous replay."""

  def __init__(self):
    super().__init__('demo_recorder')
    self.declare_parameter('output_dir', os.path.expanduser('~/marv_ws/recordings'))
    self.declare_parameter('session_name', '')
    self.declare_parameter('cmd_vel_topic', '/cmd_vel')
    self.declare_parameter('pose_topic', '/sensors/pose')
    self.declare_parameter('vision_topic', '/f_cam/detections')
    self.declare_parameter('record_hz', 10.0)

    out_dir = self.get_parameter('output_dir').value
    os.makedirs(out_dir, exist_ok=True)
    name = self.get_parameter('session_name').value
    if not name:
      name = datetime.now().strftime('%Y%m%d_%H%M%S')
    self._path = os.path.join(out_dir, f'{name}.jsonl')
    self._file = open(self._path, 'w', encoding='utf-8')
    self._t0 = self.get_clock().now()
    self._latest_pose = None
    self._latest_vision = ''
    self._latest_cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    self._sample_count = 0

    cmd_topic = self.get_parameter('cmd_vel_topic').value
    pose_topic = self.get_parameter('pose_topic').value
    vision_topic = self.get_parameter('vision_topic').value

    self.create_subscription(Twist, cmd_topic, self._cmd_callback, 10)
    self.create_subscription(
        PoseWithCovarianceStamped, pose_topic, self._pose_callback, 10)
    self.create_subscription(String, vision_topic, self._vision_callback, 10)
    self.create_subscription(String, '/demo_recorder/marker', self._marker_callback, 10)

    hz = float(self.get_parameter('record_hz').value)
    self.create_timer(1.0 / hz, self._record_sample)
    self._write_meta()
    self.get_logger().info(f'Recording demo to {self._path}')

  def _elapsed_s(self) -> float:
    return (self.get_clock().now() - self._t0).nanoseconds / 1e9

  def _write_line(self, payload: dict):
    self._file.write(json.dumps(payload, separators=(',', ':')) + '\n')
    self._file.flush()

  def _write_meta(self):
    self._write_line({
        'type': 'meta',
        't': 0.0,
        'frame': 'map',
        'notes': 'Marv teleop demo — surge/sway/heave/yaw in cmd field',
    })

  def _cmd_callback(self, msg: Twist):
    self._latest_cmd = {
        'surge': float(msg.linear.x),
        'sway': float(msg.linear.y),
        'heave': float(msg.linear.z),
        'yaw': float(msg.angular.z),
    }

  def _pose_callback(self, msg: PoseWithCovarianceStamped):
    self._latest_pose = msg

  def _vision_callback(self, msg: String):
    self._latest_vision = msg.data

  def _marker_callback(self, msg: String):
    self._write_line({
        'type': 'marker',
        't': round(self._elapsed_s(), 3),
        'label': msg.data,
        'cmd': dict(self._latest_cmd),
    })
    self.get_logger().info(f'Marker saved at t={self._elapsed_s():.1f}s: {msg.data}')

  def _record_sample(self):
    pose = None
    if self._latest_pose is not None:
      p = self._latest_pose.pose.pose
      pose = {
          'x': float(p.position.x),
          'y': float(p.position.y),
          'z': float(p.position.z),
          'yaw': float(_yaw_from_orientation(p.orientation)),
      }
    self._write_line({
        'type': 'sample',
        't': round(self._elapsed_s(), 3),
        'cmd': dict(self._latest_cmd),
        'pose': pose,
        'vision': self._latest_vision,
    })
    self._sample_count += 1

  def close(self):
    if self._file.closed:
      return
    self._write_line({
        'type': 'end',
        't': round(self._elapsed_s(), 3),
        'samples': self._sample_count,
    })
    self._file.close()
    self.get_logger().info(
        f'Demo saved: {self._path} ({self._sample_count} samples)')


def main(args=None):
  rclpy.init(args=args)
  node = DemoRecorder()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.close()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

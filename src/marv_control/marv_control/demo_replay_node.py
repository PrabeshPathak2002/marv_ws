#!/usr/bin/env python3
"""Replay a recorded teleop demo by publishing /cmd_vel on the original timeline."""

import json

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


def load_demo_samples(path: str):
  """Return ordered cmd samples [{t, cmd}, ...] from a JSONL demo file."""
  samples = []
  duration = 0.0
  with open(path, encoding='utf-8') as handle:
    for line in handle:
      line = line.strip()
      if not line:
        continue
      row = json.loads(line)
      if row.get('type') != 'sample':
        continue
      cmd = row.get('cmd') or {}
      samples.append({
          't': float(row['t']),
          'cmd': {
              'surge': float(cmd.get('surge', 0.0)),
              'sway': float(cmd.get('sway', 0.0)),
              'heave': float(cmd.get('heave', 0.0)),
              'yaw': float(cmd.get('yaw', 0.0)),
          },
      })
      duration = max(duration, float(row['t']))
  return samples, duration


class DemoReplayNode(Node):
  """Open-loop replay of a recorded keyboard demo."""

  def __init__(self):
    super().__init__('demo_replay')
    self.declare_parameter('demo_file', '')
    self.declare_parameter('cmd_vel_topic', '/cmd_vel')
    self.declare_parameter('speed_scale', 1.0)
    self.declare_parameter('loop', False)
    self.declare_parameter('publish_rate_hz', 20.0)

    demo_file = self.get_parameter('demo_file').value
    if not demo_file:
      raise RuntimeError('demo_file parameter is required')

    self._samples, self._duration = load_demo_samples(demo_file)
    if not self._samples:
      raise RuntimeError(f'No samples found in {demo_file}')

    self._speed = max(0.1, float(self.get_parameter('speed_scale').value))
    self._loop = bool(self.get_parameter('loop').value)
    self._index = 0
    self._t0 = self.get_clock().now()
    topic = self.get_parameter('cmd_vel_topic').value
    self._pub = self.create_publisher(Twist, topic, 10)

    rate = float(self.get_parameter('publish_rate_hz').value)
    self._timer = self.create_timer(1.0 / rate, self._tick)
    self.get_logger().info(
        f'Replaying {demo_file}: {len(self._samples)} samples, '
        f'{self._duration:.1f}s at {self._speed:.2f}x speed')

  def _elapsed_s(self) -> float:
    return (self.get_clock().now() - self._t0).nanoseconds / 1e9

  def _publish_cmd(self, cmd: dict):
    msg = Twist()
    msg.linear.x = cmd['surge']
    msg.linear.y = cmd['sway']
    msg.linear.z = cmd['heave']
    msg.angular.z = cmd['yaw']
    self._pub.publish(msg)

  def _tick(self):
    t = self._elapsed_s() * self._speed
    while self._index + 1 < len(self._samples) and self._samples[self._index + 1]['t'] <= t:
      self._index += 1

    if t > self._duration:
      if self._loop:
        self._t0 = self.get_clock().now()
        self._index = 0
        return
      self._publish_cmd({'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0})
      self.get_logger().info('Replay complete')
      self.destroy_timer(self._timer)
      return

    self._publish_cmd(self._samples[self._index]['cmd'])


def main(args=None):
  rclpy.init(args=args)
  node = DemoReplayNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

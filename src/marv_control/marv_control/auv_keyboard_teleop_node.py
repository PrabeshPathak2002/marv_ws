#!/usr/bin/env python3
"""Keyboard teleop for Marv AUV — publishes /cmd_vel (surge/sway/heave/yaw)."""

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

HELP = """
AUV keyboard teleop (focus this terminal)
-----------------------------------------
  Tap to set velocity (stays until changed or stop):
  w / s     surge forward / back
  a / d     sway left / right
  q / e     heave up / down
  j / l     yaw left / right
  space     stop all
  m         drop phase marker in demo recording
  h         print help
  Ctrl+C    quit
"""


class AuvKeyboardTeleop(Node):
  """Read keys and publish velocity commands for manual driving."""

  def __init__(self):
    super().__init__('auv_keyboard_teleop')
    self.declare_parameter('cmd_vel_topic', '/cmd_vel')
    self.declare_parameter('surge_speed', 0.55)
    self.declare_parameter('sway_speed', 0.40)
    self.declare_parameter('heave_speed', 0.35)
    self.declare_parameter('yaw_speed', 0.45)
    self.declare_parameter('publish_rate_hz', 50.0)

    topic = self.get_parameter('cmd_vel_topic').value
    self._surge = float(self.get_parameter('surge_speed').value)
    self._sway = float(self.get_parameter('sway_speed').value)
    self._heave = float(self.get_parameter('heave_speed').value)
    self._yaw = float(self.get_parameter('yaw_speed').value)

    self._cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    self._pub = self.create_publisher(Twist, topic, 10)
    self._marker_pub = self.create_publisher(String, '/demo_recorder/marker', 10)

    rate = float(self.get_parameter('publish_rate_hz').value)
    self._timer = self.create_timer(1.0 / rate, self._publish_cmd)
    self.get_logger().info(f'AUV keyboard teleop publishing on {topic}')
    print(HELP)

  def _publish_cmd(self):
    msg = Twist()
    msg.linear.x = self._cmd['surge']
    msg.linear.y = self._cmd['sway']
    msg.linear.z = self._cmd['heave']
    msg.angular.z = self._cmd['yaw']
    self._pub.publish(msg)
    if any(abs(v) > 1e-3 for v in self._cmd.values()):
      self.get_logger().info(
          f'cmd surge={msg.linear.x:.2f} sway={msg.linear.y:.2f} '
          f'heave={msg.linear.z:.2f} yaw={msg.angular.z:.2f}',
          throttle_duration_sec=1.0)

  def _drop_marker(self, label: str):
    msg = String()
    msg.data = label
    self._marker_pub.publish(msg)
    self.get_logger().info(f'Demo marker: {label}')

  def handle_key(self, key: str):
    if key == 'w':
      self._cmd['surge'] = self._surge
    elif key == 's':
      self._cmd['surge'] = -self._surge
    elif key == 'a':
      self._cmd['sway'] = self._sway
    elif key == 'd':
      self._cmd['sway'] = -self._sway
    elif key == 'q':
      self._cmd['heave'] = self._heave
    elif key == 'e':
      self._cmd['heave'] = -self._heave
    elif key == 'j':
      self._cmd['yaw'] = self._yaw
    elif key == 'l':
      self._cmd['yaw'] = -self._yaw
    elif key in (' ', '\x00'):
      self._cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    elif key == 'm':
      self._drop_marker(f'marker_{self.get_clock().now().nanoseconds}')
    elif key == 'h':
      print(HELP)
    elif key in ('\x03', '\x1b'):
      raise KeyboardInterrupt


def _get_key(settings):
  tty.setraw(sys.stdin.fileno())
  rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
  key = sys.stdin.read(1) if rlist else ''
  termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
  return key


def main(args=None):
  settings = termios.tcgetattr(sys.stdin)
  rclpy.init(args=args)
  node = AuvKeyboardTeleop()
  try:
    while rclpy.ok():
      rclpy.spin_once(node, timeout_sec=0.0)
      key = _get_key(settings)
      if key:
        node.handle_key(key)
  except KeyboardInterrupt:
    pass
  finally:
    node._cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    if rclpy.ok():
      try:
        node._publish_cmd()
      except Exception:
        pass
    node.destroy_node()
    if rclpy.ok():
      rclpy.shutdown()


if __name__ == '__main__':
  main()

#!/usr/bin/env python3
"""ArduSub hardware interface ROS 2 node."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

from marv_ardusub.lib import calculate_esc_pwm, estimate_position, maintain_depth


class ArdusubNode(Node):
  """Interfaces with ArduSub: depth hold, ESC PWM, position estimate."""

  def __init__(self):
    super().__init__('ardusub_node')
    self.depth_pub = self.create_publisher(Float32, 'depth', 10)
    self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    self.target_depth = 1.0
    self.get_logger().info('ArduSub node started')

  def cmd_vel_callback(self, msg: Twist):
    calculate_esc_pwm(msg.linear.x, channel=0)
    calculate_esc_pwm(msg.linear.y, channel=1)

  def timer_callback(self):
    maintain_depth(self, self.target_depth)
    pose = estimate_position(self)
    if pose is not None and 'depth' in pose:
      depth_msg = Float32()
      depth_msg.data = float(pose['depth'])
      self.depth_pub.publish(depth_msg)


def main(args=None):
  rclpy.init(args=args)
  node = ArdusubNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

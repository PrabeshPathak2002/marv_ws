#!/usr/bin/env python3
"""Master control ROS 2 node for Marv AUV mission behaviors."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

from marv_control.lib import (
    avoid_obstacles,
    close_grip,
    deploy_torpedo,
    detect_path,
    open_grip,
    return_home,
    traverse_gate,
)


class MasterControlNode(Node):
  """Orchestrates mission behaviors and publishes velocity commands."""

  def __init__(self):
    super().__init__('master_control_node')
    self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
    self.create_subscription(String, 'f_cam/detections', self.vision_callback, 10)
    self.timer = self.create_timer(0.1, self.control_loop)
    self.vision_data = None
    self.get_logger().info('Master control node started')

  def vision_callback(self, msg: String):
    self.vision_data = msg.data

  def control_loop(self):
    avoid_obstacles(self, self.vision_data)
    detect_path(self, self.vision_data)
    return_home(self)
    traverse_gate(self, self.vision_data)
    open_grip(self)
    close_grip(self)
    deploy_torpedo(self)

    cmd = Twist()
    self.cmd_vel_pub.publish(cmd)


def main(args=None):
  rclpy.init(args=args)
  node = MasterControlNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

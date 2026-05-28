#!/usr/bin/env python3
"""Down camera ROS 2 node."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from marv_vision.lib import format_detection_string, process_d_cam


class DCamNode(Node):
  """Publishes down-camera detections."""

  def __init__(self):
    super().__init__('d_cam_node')
    self.detection_pub = self.create_publisher(String, 'd_cam/detections', 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    self.get_logger().info('Down camera node started')

  def timer_callback(self):
    detections = process_d_cam(frame=None)
    msg = String()
    msg.data = format_detection_string(detections)
    self.detection_pub.publish(msg)


def main(args=None):
  rclpy.init(args=args)
  node = DCamNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

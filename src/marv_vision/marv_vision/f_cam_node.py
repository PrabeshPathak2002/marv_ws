#!/usr/bin/env python3
"""Front camera ROS 2 node."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from marv_vision.lib import (
    calculate_obj_coord,
    format_detection_string,
    process_f_cam,
    process_vslam,
)


class FCamNode(Node):
  """Publishes front-camera detections and VSLAM-related vision output."""

  def __init__(self):
    super().__init__('f_cam_node')
    self.detection_pub = self.create_publisher(String, 'f_cam/detections', 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    self.get_logger().info('Front camera node started')

  def timer_callback(self):
    detections = process_f_cam(frame=None)
    vslam = process_vslam()
    for det in detections:
      calculate_obj_coord(det)
    msg = String()
    msg.data = format_detection_string(detections)
    self.detection_pub.publish(msg)


def main(args=None):
  rclpy.init(args=args)
  node = FCamNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

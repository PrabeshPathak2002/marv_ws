#!/usr/bin/env python3
"""Down camera ROS 2 node."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from marv_vision.lib import format_detection_string, process_d_cam
from marv_vision.lib.camera_input import CameraInput

SIM_IMAGE_TOPIC = '/unity/d_cam/image_raw'


class DCamNode(Node):
  """Publishes down-camera detections."""

  def __init__(self):
    super().__init__('d_cam_node')
    self.declare_parameter('use_sim', False)
    self.declare_parameter('sim_image_topic', SIM_IMAGE_TOPIC)
    self.declare_parameter('camera_index', 1)
    self.declare_parameter('conf_threshold', 0.25)
    self.declare_parameter('image_width', 640)
    self.declare_parameter('image_height', 480)

    use_sim = self.get_parameter('use_sim').value
    self._camera = CameraInput(
        self,
        use_sim=use_sim,
        sim_image_topic=self.get_parameter('sim_image_topic').value,
        camera_index=self.get_parameter('camera_index').value,
    )

    self.detection_pub = self.create_publisher(String, 'd_cam/detections', 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    mode = 'simulation' if use_sim else 'hardware'
    self.get_logger().info(f'Down camera node started ({mode})')

  def timer_callback(self):
    frame = self._camera.read_frame()
    conf = self.get_parameter('conf_threshold').value
    detections = process_d_cam(frame, conf=conf)
    msg = String()
    msg.data = format_detection_string(detections)
    self.detection_pub.publish(msg)

  def destroy_node(self):
    self._camera.release()
    super().destroy_node()


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

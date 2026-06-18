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
from marv_vision.lib.camera_input import CameraInput
from marv_vision.lib.model_config import load_front_model_config

SIM_IMAGE_TOPIC = '/unity/f_cam/image_raw'


class FCamNode(Node):
  """Publishes front-camera YOLO detections."""

  def __init__(self):
    super().__init__('f_cam_node')
    self.declare_parameter('use_sim', False)
    self.declare_parameter('sim_image_topic', SIM_IMAGE_TOPIC)
    self.declare_parameter('camera_index', 0)
    self.declare_parameter('conf_threshold', 0.25)
    self.declare_parameter('image_width', 640)
    self.declare_parameter('image_height', 480)

    try:
      cfg = load_front_model_config()
      self.get_logger().info(
          f'Front model: {cfg["model_path"]} ({cfg["nc"]} classes)')
    except FileNotFoundError as exc:
      self.get_logger().error(str(exc))

    use_sim = self.get_parameter('use_sim').value
    self._camera = CameraInput(
        self,
        use_sim=use_sim,
        sim_image_topic=self.get_parameter('sim_image_topic').value,
        camera_index=self.get_parameter('camera_index').value,
    )

    self.detection_pub = self.create_publisher(String, 'f_cam/detections', 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    mode = 'simulation' if use_sim else 'hardware'
    self.get_logger().info(f'Front camera node started ({mode})')

  def timer_callback(self):
    frame = self._camera.read_frame()
    conf = self.get_parameter('conf_threshold').value
    width = self.get_parameter('image_width').value
    height = self.get_parameter('image_height').value

    detections = process_f_cam(frame, conf=conf)
    process_vslam()

    for det in detections:
      coord = calculate_obj_coord(det, image_width=width, image_height=height)
      if coord:
        det['coord'] = coord
        det['x'] = coord['norm_x']
        det['y'] = coord['norm_y']

    msg = String()
    msg.data = format_detection_string(detections)
    self.detection_pub.publish(msg)

  def destroy_node(self):
    self._camera.release()
    super().destroy_node()


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

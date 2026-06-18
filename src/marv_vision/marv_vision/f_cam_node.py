#!/usr/bin/env python3
"""Front camera ROS 2 node."""

import os

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
from marv_vision.lib.prequal_cv import process_prequal_cv

SIM_IMAGE_TOPIC = '/unity/f_cam/image_raw'


def _default_prequal_cv_config():
  try:
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory('marv_bringup')
    path = os.path.join(share, 'config', 'prequal_cv.yaml')
    if os.path.isfile(path):
      return path
  except Exception:
    pass
  return ''


class FCamNode(Node):
  """Publishes front-camera detections (YOLO or OpenCV pre-qual)."""

  def __init__(self):
    super().__init__('f_cam_node')
    self.declare_parameter('use_sim', False)
    self.declare_parameter('sim_image_topic', SIM_IMAGE_TOPIC)
    self.declare_parameter('camera_index', 0)
    self.declare_parameter('conf_threshold', 0.25)
    self.declare_parameter('image_width', 640)
    self.declare_parameter('image_height', 480)
    self.declare_parameter('vision_profile', 'default')
    self.declare_parameter('model_path', '')
    self.declare_parameter('prequal_cv_config', _default_prequal_cv_config())

    profile = self.get_parameter('vision_profile').value
    if profile == 'prequal_cv':
      cfg_path = self.get_parameter('prequal_cv_config').value
      self.get_logger().info(
          f'Front camera: OpenCV pre-qual mode (config={cfg_path or "defaults"})')
    elif profile != 'prequal':
      override = self.get_parameter('model_path').value or None
      try:
        from marv_vision.lib.model_config import resolve_model_path, PREQUAL_MODEL_PATH
        path = resolve_model_path(profile, override_path=override or None)
        if profile == 'prequal' and override is None:
          if not PREQUAL_MODEL_PATH.is_file() or PREQUAL_MODEL_PATH.stat().st_size == 0:
            self.get_logger().warn(
                'prequal_model.pt not found — using front_model.pt (see VISION_PREQUAL.md)')
        self.get_logger().info(f'Front model ({profile}): {path}')
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
    self.get_logger().info(f'Front camera node started ({mode}, profile={profile})')

  def _run_detection(self, frame, conf):
    profile = self.get_parameter('vision_profile').value
    if profile == 'prequal_cv':
      return process_prequal_cv(
          frame,
          config_path=self.get_parameter('prequal_cv_config').value or None,
          min_confidence=conf,
      )
    return process_f_cam(
        frame,
        conf=conf,
        vision_profile=profile,
        model_path=self.get_parameter('model_path').value or None,
    )

  def timer_callback(self):
    frame = self._camera.read_frame()
    conf = self.get_parameter('conf_threshold').value
    width = self.get_parameter('image_width').value
    height = self.get_parameter('image_height').value

    detections = self._run_detection(frame, conf)
    process_vslam()

    for det in detections:
      coord = calculate_obj_coord(det, image_width=width, image_height=height)
      if coord:
        det['coord'] = coord
        det['x'] = coord['norm_x']
        det['y'] = coord['norm_y']
      elif det.get('xyxy'):
        x1, y1, x2, y2 = det['xyxy']
        det['x'] = (x1 + x2) / 2.0 / max(float(width), 1.0)
        det['y'] = (y1 + y2) / 2.0 / max(float(height), 1.0)

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

#!/usr/bin/env python3
"""Front camera ROS 2 node."""

import os

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from marv_vision.lib import (
    calculate_obj_coord,
    format_detection_string,
    process_f_cam,
    process_vslam,
)
from marv_vision.lib.camera_input import CameraInput
from marv_vision.lib.draw_detections import draw_detections
from marv_vision.lib.prequal_cv import process_prequal_cv
from marv_vision.lib.target_tracker import DetectionTracker

try:
    from cv_bridge import CvBridge
except (ImportError, AttributeError):
    CvBridge = None

SIM_IMAGE_TOPIC = '/unity/f_cam/image_raw'
DEBUG_IMAGE_TOPIC = '/f_cam/image_annotated'


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
    self.declare_parameter('camera_device', '/dev/video0')
    self.declare_parameter('frame_fps', 30.0)
    self.declare_parameter('fourcc', 'MJPG')
    self.declare_parameter('conf_threshold', 0.25)
    self.declare_parameter('image_width', 1280)
    self.declare_parameter('image_height', 720)
    self.declare_parameter('vision_profile', 'default')
    self.declare_parameter('model_path', '')
    self.declare_parameter('prequal_cv_config', _default_prequal_cv_config())
    self.declare_parameter('show_debug_window', False)
    self.declare_parameter('publish_debug_image', False)
    self.declare_parameter('smooth_detections', True)
    self.declare_parameter('smooth_alpha', 0.35)

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
    device = self.get_parameter('camera_device').value
    width = int(self.get_parameter('image_width').value)
    height = int(self.get_parameter('image_height').value)
    self._camera = CameraInput(
        self,
        use_sim=use_sim,
        sim_image_topic=self.get_parameter('sim_image_topic').value,
        camera_index=self.get_parameter('camera_index').value,
        camera_device=device,
        frame_width=width,
        frame_height=height,
        frame_fps=self.get_parameter('frame_fps').value,
        fourcc=self.get_parameter('fourcc').value,
    )
    self._frame_width = width
    self._frame_height = height
    self._show_debug = self.get_parameter('show_debug_window').value
    self._publish_debug = self.get_parameter('publish_debug_image').value
    if self._show_debug:
      self._publish_debug = True
    self._bridge = CvBridge() if CvBridge is not None else None
    self._tracker = DetectionTracker(
        alpha=float(self.get_parameter('smooth_alpha').value))
    self._smooth_detections = bool(self.get_parameter('smooth_detections').value)

    self.detection_pub = self.create_publisher(String, 'f_cam/detections', 10)
    self._debug_image_pub = None
    if self._publish_debug:
      if self._bridge is None:
        self.get_logger().error('Debug image requires cv_bridge — use: ros2 run marv_vision f_cam_debug')
      else:
        self._debug_image_pub = self.create_publisher(
            Image, DEBUG_IMAGE_TOPIC, 10)
        self.get_logger().info(f'Publishing annotated frames on {DEBUG_IMAGE_TOPIC}')

    self.timer = self.create_timer(0.1, self.timer_callback)
    mode = 'simulation' if use_sim else 'hardware'
    if self._show_debug:
      self.get_logger().info('Debug window enabled (press q in window to quit)')
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
    if frame is not None:
      height, width = frame.shape[:2]
    else:
      width = self._frame_width
      height = self._frame_height

    detections = self._run_detection(frame, conf)
    if self._smooth_detections:
      detections = self._tracker.smooth_all(detections)
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

    if frame is None:
      return

    show_debug = self._show_debug or self.get_parameter('show_debug_window').value
    publish_debug = self._publish_debug or self.get_parameter('publish_debug_image').value
    if not show_debug and not publish_debug:
      return

    annotated = draw_detections(frame, detections)
    if annotated is None:
      return

    if publish_debug and self._debug_image_pub is None and self._bridge is not None:
      self._debug_image_pub = self.create_publisher(Image, DEBUG_IMAGE_TOPIC, 10)

    if publish_debug and self._debug_image_pub is not None and self._bridge is not None:
      stamp = self.get_clock().now().to_msg()
      img_msg = self._bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
      img_msg.header.stamp = stamp
      img_msg.header.frame_id = 'f_cam_optical_frame'
      self._debug_image_pub.publish(img_msg)

    if show_debug:
      cv2.imshow('f_cam debug', annotated)
      if cv2.waitKey(1) & 0xFF == ord('q'):
        self.get_logger().info('Debug window closed (q pressed)')
        self._show_debug = False
        cv2.destroyAllWindows()

  def destroy_node(self):
    if self._show_debug:
      cv2.destroyAllWindows()
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

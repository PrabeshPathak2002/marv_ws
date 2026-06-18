"""Dual-mode camera input: physical OpenCV capture or Unity sim Image topic."""

from sensor_msgs.msg import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from cv_bridge import CvBridge
except (ImportError, AttributeError):
    CvBridge = None


class CameraInput:
    """Hardware (VideoCapture) or simulation (sensor_msgs/Image + CvBridge)."""

    def __init__(
        self,
        node,
        use_sim,
        sim_image_topic,
        camera_index=0,
    ):
        self._node = node
        self._use_sim = use_sim
        self._latest_frame = None
        self._capture = None
        self._bridge = None

        if use_sim:
            if CvBridge is None:
                node.get_logger().error(
                    'cv_bridge required for use_sim=true but is not installed')
                return
            self._bridge = CvBridge()
            node.create_subscription(
                Image, sim_image_topic, self._sim_image_callback, 10)
            node.get_logger().info(
                f'Simulation mode: subscribed to {sim_image_topic}')
        else:
            if cv2 is None:
                node.get_logger().error(
                    'opencv (cv2) required for hardware mode but is not installed')
                return
            self._capture = cv2.VideoCapture(int(camera_index))
            if not self._capture.isOpened():
                node.get_logger().error(
                    f'Failed to open camera index {camera_index}')
            else:
                node.get_logger().info(
                    f'Hardware mode: opened camera index {camera_index}')

    def _sim_image_callback(self, msg: Image):
        if self._bridge is None:
            return
        try:
            self._latest_frame = self._bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as exc:
            self._node.get_logger().warn(f'CvBridge conversion failed: {exc}')

    def read_frame(self):
        """Return the latest BGR frame, or None if unavailable."""
        if self._use_sim:
            return self._latest_frame

        if self._capture is None or not self._capture.isOpened():
            return None

        ok, frame = self._capture.read()
        return frame if ok else None

    def release(self):
        if self._capture is not None:
            self._capture.release()
            self._capture = None

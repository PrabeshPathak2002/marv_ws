#!/usr/bin/env python3
"""Bridge Gazebo Harmonic (gz-transport13) camera images to ROS."""

import queue
import threading
import time

import rclpy
from gz.msgs10.image_pb2 import Image as GzImage
from gz.transport13 import Node as GzNode
from rclpy.node import Node
from sensor_msgs.msg import Image as RosImage

# gz.msgs.Image.PixelFormatType values used by Gazebo Sim sensors.
_GZ_TO_ROS_ENCODING = {
    1: 'mono8',   # L_INT8
    2: 'rgba8',   # RGBA_INT8
    3: 'rgb8',    # RGB_INT8
    4: 'bgr8',    # BGR_INT8
    5: '16UC1',   # L_INT16
    6: '32FC1',   # FLOAT32
}


def _gz_image_to_ros(msg: GzImage, frame_id: str) -> RosImage | None:
    encoding = _GZ_TO_ROS_ENCODING.get(msg.pixel_format_type)
    if encoding is None:
        return None

    ros_msg = RosImage()
    if msg.HasField('header'):
        ros_msg.header.stamp.sec = msg.header.stamp.sec
        ros_msg.header.stamp.nanosec = msg.header.stamp.nsec
    ros_msg.header.frame_id = frame_id
    ros_msg.height = msg.height
    ros_msg.width = msg.width
    ros_msg.encoding = encoding
    ros_msg.is_bigendian = False
    ros_msg.step = msg.step
    ros_msg.data = bytes(msg.data)
    return ros_msg


class GzImageBridge(Node):
    def __init__(self):
        super().__init__('gz_image_bridge')
        self.declare_parameter('gz_topic', '/explore_hd')
        self.declare_parameter('ros_topic', '/gazebo/f_cam/image_raw')
        self.declare_parameter('frame_id', 'explore_hd_optical_frame')

        gz_topic = self.get_parameter('gz_topic').value
        ros_topic = self.get_parameter('ros_topic').value
        frame_id = self.get_parameter('frame_id').value

        self._pub = self.create_publisher(RosImage, ros_topic, 10)
        self._queue: queue.Queue[RosImage] = queue.Queue(maxsize=2)
        self._unsupported_logged = False
        self._stop = threading.Event()

        def on_gz_image(msg: GzImage):
            ros_msg = _gz_image_to_ros(msg, frame_id)
            if ros_msg is None:
                if not self._unsupported_logged:
                    self._unsupported_logged = True
                    self.get_logger().warn(
                        f'Unsupported Gazebo pixel format {msg.pixel_format_type}')
                return
            try:
                self._queue.put_nowait(ros_msg)
            except queue.Full:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
                self._queue.put_nowait(ros_msg)

        def gz_loop():
            gz_node = GzNode()
            if not gz_node.subscribe(GzImage, gz_topic, on_gz_image):
                self.get_logger().error(f'Failed to subscribe to Gazebo topic {gz_topic}')
                return
            while not self._stop.is_set():
                time.sleep(0.005)

        self._gz_thread = threading.Thread(target=gz_loop, daemon=True)
        self._gz_thread.start()
        self.create_timer(0.001, self._drain_queue)
        self.get_logger().info(f'{gz_topic} -> {ros_topic}')

    def _drain_queue(self):
        while True:
            try:
                self._pub.publish(self._queue.get_nowait())
            except queue.Empty:
                break

    def destroy_node(self):
        self._stop.set()
        super().destroy_node()


def main():
    rclpy.init()
    node = GzImageBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

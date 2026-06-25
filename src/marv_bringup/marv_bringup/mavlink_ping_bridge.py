#!/usr/bin/env python3
"""Publish FCU Ping1D DISTANCE_SENSOR MAVLink as sensor_msgs/Range for pre-qual."""

import threading
import time

import rclpy
from pymavlink import mavutil
from rclpy.node import Node
from sensor_msgs.msg import Range


class MavlinkPingBridge(Node):
    """Read DISTANCE_SENSOR from mavlink-router UDP and publish Range."""

    def __init__(self):
        super().__init__('mavlink_ping_bridge')
        self.declare_parameter('mavlink_url', 'udpin:127.0.0.1:14556')
        self.declare_parameter('topic', '/mavros/distance_sensor/lidar')
        self.declare_parameter('frame_id', 'lidar')
        self.declare_parameter('min_range_m', 0.2)
        self.declare_parameter('max_range_m', 30.0)

        topic = self.get_parameter('topic').value
        self._frame_id = self.get_parameter('frame_id').value
        self._min_range = float(self.get_parameter('min_range_m').value)
        self._max_range = float(self.get_parameter('max_range_m').value)
        self._mavlink_url = self.get_parameter('mavlink_url').value

        self._latest = None
        self._lock = threading.Lock()
        self._pub = self.create_publisher(Range, topic, 10)
        self._worker = threading.Thread(target=self._mavlink_loop, daemon=True)
        self._worker.start()
        self.create_timer(0.1, self._publish_latest)
        self.get_logger().info(
            f'mavlink_ping_bridge: {self._mavlink_url} -> {topic}')

    def _mavlink_loop(self):
        while rclpy.ok():
            try:
                conn = mavutil.mavlink_connection(self._mavlink_url)
                conn.wait_heartbeat(timeout=10)
                self.get_logger().info('mavlink_ping_bridge: FCU heartbeat OK')
                while rclpy.ok():
                    msg = conn.recv_match(
                        type='DISTANCE_SENSOR', blocking=True, timeout=1)
                    if msg is None:
                        continue
                    range_m = float(msg.current_distance) / 100.0
                    min_m = max(float(msg.min_distance) / 100.0, self._min_range)
                    max_m = min(float(msg.max_distance) / 100.0, self._max_range)
                    with self._lock:
                        self._latest = (range_m, min_m, max_m)
            except Exception as exc:
                self.get_logger().warn(
                    f'mavlink_ping_bridge reconnecting: {exc}')
                time.sleep(2.0)

    def _publish_latest(self):
        with self._lock:
            if self._latest is None:
                return
            range_m, min_m, max_m = self._latest

        out = Range()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self._frame_id
        out.radiation_type = Range.ULTRASOUND
        out.field_of_view = 0.26
        out.min_range = min_m
        out.max_range = max_m
        out.range = range_m
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MavlinkPingBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

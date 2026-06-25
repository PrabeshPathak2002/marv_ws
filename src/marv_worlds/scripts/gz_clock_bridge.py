#!/usr/bin/env python3
"""Bridge Gazebo Harmonic simulation clock to ROS /clock."""

import queue
import threading
import time

import rclpy
from gz.msgs10.clock_pb2 import Clock as GzClock
from gz.transport13 import Node as GzNode
from rclpy.node import Node
from rosgraph_msgs.msg import Clock


class GzClockBridge(Node):
    def __init__(self):
        super().__init__('gz_clock_bridge')
        self.declare_parameter('gz_topic', '/clock')
        self.declare_parameter('ros_topic', '/clock')

        gz_topic = self.get_parameter('gz_topic').value
        ros_topic = self.get_parameter('ros_topic').value

        self._pub = self.create_publisher(Clock, ros_topic, 10)
        self._queue: queue.Queue[Clock] = queue.Queue(maxsize=4)
        self._stop = threading.Event()

        def on_gz_clock(msg: GzClock):
            ros_msg = Clock()
            ros_msg.clock.sec = msg.sim.sec
            ros_msg.clock.nanosec = msg.sim.nsec
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
            if not gz_node.subscribe(GzClock, gz_topic, on_gz_clock):
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
    node = GzClockBridge()
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

#!/usr/bin/env python3
"""Bridge Gazebo model pose to /sensors/pose for mission planner in vision-only sim."""

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


class GzPoseBridge(Node):
    def __init__(self):
        super().__init__('gz_pose_bridge')
        self.declare_parameter('gz_pose_topic', '/world/marv_prequal/model/marv_auv/pose')
        self.declare_parameter('output_topic', '/sensors/pose')
        gz_topic = self.get_parameter('gz_pose_topic').value
        out_topic = self.get_parameter('output_topic').value
        self._pub = self.create_publisher(PoseStamped, out_topic, 10)
        self.create_subscription(PoseStamped, gz_topic, self._cb, 10)
        self.get_logger().info(f'{gz_topic} -> {out_topic}')

    def _cb(self, msg: PoseStamped):
        self._pub.publish(msg)


def main():
    rclpy.init()
    node = GzPoseBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

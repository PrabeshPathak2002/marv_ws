#!/usr/bin/env python3
"""Master control ROS 2 node for Marv AUV mission behaviors."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from std_msgs.msg import String

from marv_control.lib import (
    avoid_obstacles,
    close_grip,
    deploy_torpedo,
    detect_path,
    open_grip,
    return_home,
    traverse_gate,
)
from marv_control.lib.motion_control import compute_depth_hold_cmd

TOPIC_POSE = '/sensors/pose'


class MasterControlNode(Node):
  """Orchestrates behaviors; publishes /cmd_vel from pose and vision."""

  def __init__(self):
    super().__init__('master_control_node')

    self.declare_parameter('enable_control', False)
    self.declare_parameter('depth_hold_enabled', True)
    self.declare_parameter('target_depth_m', 1.0)
    self.declare_parameter('depth_kp', 0.25)

    self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
    self.create_subscription(String, 'f_cam/detections', self.vision_callback, 10)
    self.create_subscription(
        PoseWithCovarianceStamped, TOPIC_POSE, self.pose_callback, 10)

    self.timer = self.create_timer(0.1, self.control_loop)
    self.vision_data = None
    self.latest_pose = None
    self._pose_rx = False
    self._log_counter = 0

    self.get_logger().info(
        'Master control started. enable_control=false by default (bench safe). '
        'Set enable_control:=true to publish depth-hold cmd_vel.')

  def vision_callback(self, msg: String):
    self.vision_data = msg.data

  def pose_callback(self, msg: PoseWithCovarianceStamped):
    self.latest_pose = msg
    self._pose_rx = True

  def control_loop(self):
    avoid_obstacles(self, self.vision_data)
    detect_path(self, self.vision_data)
    return_home(self, self.latest_pose)
    traverse_gate(self, self.vision_data)
    open_grip(self)
    close_grip(self)
    deploy_torpedo(self)

    cmd = self._compute_cmd_vel()
    self.cmd_vel_pub.publish(cmd)

    self._log_counter += 1
    if self._log_counter % 50 == 0 and self.get_parameter('enable_control').value:
      self.get_logger().info(
          f'cmd_vel heave={cmd.linear.z:.2f} '
          f'(pose_rx={self._pose_rx})')

  def _compute_cmd_vel(self) -> Twist:
    if not self.get_parameter('enable_control').value:
      return Twist()

    if not self.get_parameter('depth_hold_enabled').value:
      return Twist()

    if self.latest_pose is None:
      return Twist()

    target = self.get_parameter('target_depth_m').value
    kp = self.get_parameter('depth_kp').value
    cmd, current_z, error = compute_depth_hold_cmd(
        self.latest_pose, target, kp=kp)

    if self._log_counter % 50 == 0:
      self.get_logger().debug(
          f'depth hold: z={current_z:.2f} target={target:.2f} err={error:.2f}')

    return cmd


def main(args=None):
  rclpy.init(args=args)
  node = MasterControlNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

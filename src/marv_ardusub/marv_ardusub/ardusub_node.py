#!/usr/bin/env python3
"""ArduSub hardware interface ROS 2 node."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from marv_ardusub.lib import (
    estimate_position,
    maintain_depth,
    publish_position_estimate,
    read_sensor_inputs,
    setup_mavros_subscriptions,
    setup_position_publishers,
)
from marv_ardusub.lib.mavros_actuation import forward_cmd_vel, setup_mavros_actuation


class ArdusubNode(Node):
  """Interfaces with ArduSub: MAVROS actuation, depth hold, pos_est."""

  def __init__(self):
    super().__init__('ardusub_node')
    self.declare_parameter('use_ping', True)
    self.declare_parameter('ping_range_topic', '/mavros/distance_sensor/lidar')
    self.declare_parameter('publish_pose', True)

    setup_position_publishers(self)
    setup_mavros_subscriptions(self)
    setup_mavros_actuation(self)

    if self.get_parameter('use_ping').value:
      from marv_ardusub.lib.ping_io import (
          setup_range_publisher,
          setup_range_subscription,
      )
      setup_range_publisher(self)
      setup_range_subscription(self)

    self._last_cmd_vel = Twist()
    self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
    self.timer = self.create_timer(0.1, self.timer_callback)
    self.target_depth = 1.0
    self._last_depth_m = self.target_depth
    ping_status = 'on' if self.get_parameter('use_ping').value else 'off'
    self.get_logger().info(f'ArduSub node started (forward Ping: {ping_status})')

  def cmd_vel_callback(self, msg: Twist):
    self._last_cmd_vel = msg

  def timer_callback(self):
    maintain_depth(self, self.target_depth, current_depth_m=self._last_depth_m)
    forward_cmd_vel(self, self._last_cmd_vel)
    if self.get_parameter('use_ping').value:
      from marv_ardusub.lib.ping_io import publish_forward_range
      publish_forward_range(self)
    if not self.get_parameter('publish_pose').value:
      return
    inputs = read_sensor_inputs(self)
    estimate = estimate_position(self, inputs)
    publish_position_estimate(self, estimate)


def main(args=None):
  rclpy.init(args=args)
  node = ArdusubNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

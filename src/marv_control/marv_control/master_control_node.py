#!/usr/bin/env python3
"""Master control ROS 2 node for Marv AUV mission behaviors."""

import json

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from sensor_msgs.msg import Range
from std_msgs.msg import String

from marv_control.lib import avoid_obstacles, close_grip, deploy_torpedo, open_grip
from marv_control.lib.cmd_merge import behavior_to_twist, merge_twists
from marv_control.lib.cmd_smooth import smooth_command
from marv_control.lib.config_loader import (
    behavior_config,
    control_config,
    load_marv_config,
    ping_config,
)
from marv_control.lib.motion_control import compute_depth_hold_cmd
from marv_control.missions import MissionContext, create_mission

TOPIC_POSE = '/sensors/pose'
TOPIC_RANGE_FORWARD = '/sensors/range_forward'
TOPIC_SET_BEHAVIOR = 'mission_planner/set_behavior'
TOPIC_MISSION_EVENT = 'mission_planner/mission_event'


class MasterControlNode(Node):
  """Orchestrates mission classes; publishes /cmd_vel from pose and vision."""

  def __init__(self):
    super().__init__('master_control_node')

    self.declare_parameter('enable_control', False)
    self.declare_parameter('depth_hold_enabled', True)
    self.declare_parameter('target_depth_m', 1.0)
    self.declare_parameter('depth_kp', 0.25)
    self.declare_parameter('active_behavior', 'depth_hold')
    self.declare_parameter('config_file', '')
    self.declare_parameter('planner_mode', False)

    self._config = load_marv_config(self.get_parameter('config_file').value)
    self._ping_cfg = ping_config(self._config)
    ctrl = control_config(self._config)
    if ctrl.get('target_depth_m') is not None:
      self.set_parameters([
          Parameter('target_depth_m', Parameter.Type.DOUBLE, float(ctrl['target_depth_m'])),
          Parameter('depth_kp', Parameter.Type.DOUBLE, float(ctrl['depth_kp'])),
      ])

    self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
    self.mission_event_pub = self.create_publisher(String, TOPIC_MISSION_EVENT, 10)
    self.create_subscription(String, 'f_cam/detections', self.vision_callback, 10)
    self.create_subscription(
        PoseWithCovarianceStamped, TOPIC_POSE, self.pose_callback, 10)
    self.create_subscription(
        String, TOPIC_SET_BEHAVIOR, self.set_behavior_callback, 10)
    self.create_subscription(Range, TOPIC_RANGE_FORWARD, self.range_callback, 10)

    self.timer = self.create_timer(0.1, self.control_loop)
    self.vision_data = None
    self.latest_pose = None
    self._forward_range_m = None
    self._forward_range_valid = False
    self._log_counter = 0
    self._mission = None
    self._mission_key = None
    self._mission_started = None
    self._mission_ctx = MissionContext()
    self._mission_done = False
    self._last_cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    self._cmd_smooth_step = float(ctrl.get('command_smooth_step', 0.035))

    self._activate_behavior(self.get_parameter('active_behavior').value)

    self.get_logger().info(
        'Master control started. enable_control=false by default (bench safe).')

  def vision_callback(self, msg: String):
    self.vision_data = msg.data

  def pose_callback(self, msg: PoseWithCovarianceStamped):
    self.latest_pose = msg

  def range_callback(self, msg: Range):
    if msg.range < msg.min_range or msg.range > msg.max_range:
      self._forward_range_valid = False
      self._forward_range_m = None
      return
    self._forward_range_m = float(msg.range)
    self._forward_range_valid = True

  def set_behavior_callback(self, msg: String):
    if not self.get_parameter('planner_mode').value:
      return
    behavior = msg.data.strip()
    if behavior:
      self._activate_behavior(behavior)

  def _activate_behavior(self, behavior_key):
    if behavior_key == self._mission_key and self._mission is not None:
      return
    if self._mission is not None:
      self._mission.cleanup()
    try:
      cfg = behavior_config(self._config, behavior_key)
      if behavior_key == 'return_home':
        cfg.setdefault(
            'home_xy', control_config(self._config).get('home_xy', [0.0, 0.0]))
      self._mission = create_mission(behavior_key, self, cfg)
    except KeyError:
      self.get_logger().error(f'Unknown behavior: {behavior_key}')
      return
    self._mission_key = behavior_key
    self._mission_started = self.get_clock().now()
    self._mission_ctx = MissionContext()
    self._mission_done = False
    self._last_cmd = {'surge': 0.0, 'sway': 0.0, 'heave': 0.0, 'yaw': 0.0}
    self.set_parameters([
        Parameter('active_behavior', Parameter.Type.STRING, behavior_key),
    ])
    self.get_logger().info(f'Active behavior: {behavior_key}')

  def _publish_mission_event(self, success, message):
    payload = {
        'behavior': self._mission_key,
        'success': success,
        'message': message,
    }
    msg = String()
    msg.data = json.dumps(payload)
    self.mission_event_pub.publish(msg)

  def control_loop(self):
    if not self.get_parameter('enable_control').value:
      return

    if self._mission is None or self._mission_done:
      self.cmd_vel_pub.publish(self._compute_cmd_vel(None))
      return

    now = self.get_clock().now()
    elapsed = (now - self._mission_started).nanoseconds / 1e9
    self._mission_ctx.vision_data = self.vision_data
    self._mission_ctx.pose = self.latest_pose
    self._mission_ctx.elapsed_s = elapsed
    self._mission_ctx.step_count += 1
    if self._forward_range_valid:
      self._mission_ctx.extras['forward_range_m'] = self._forward_range_m
    else:
      self._mission_ctx.extras.pop('forward_range_m', None)

    result = self._mission.step(self._mission_ctx)
    behavior_cmd = result.cmd
    if behavior_cmd:
      behavior_cmd = smooth_command(
          self._last_cmd, behavior_cmd, max_step=self._cmd_smooth_step)
      self._last_cmd = dict(behavior_cmd)

    open_grip(self)
    close_grip(self)
    deploy_torpedo(self)

    cmd = self._compute_cmd_vel(behavior_cmd)

    if self._mission_key in (
        'depth_hold', 'traverse_gate', 'detect_path', 'pass_gate', 'pass_gate_clear',
        'transit_forward', 'circle_marker', 'find_gate', 'find_return_gate', 'find_marker',
        'approach_marker',
    ):
      range_m = self._forward_range_m if self._forward_range_valid else None
      obstacle_cmd = avoid_obstacles(
          self, self.vision_data,
          forward_range_m=range_m,
          stop_m=float(self._ping_cfg.get('obstacle_stop_m', 0.8)))
      if obstacle_cmd is not None:
        cmd = merge_twists(behavior_to_twist(obstacle_cmd), cmd)

    self.cmd_vel_pub.publish(cmd)

    if result.complete:
      self._mission.cleanup()
      self._publish_mission_event(result.success, result.message)
      self._mission_done = True
      if not self.get_parameter('planner_mode').value:
        self._activate_behavior('hold')

    self._log_counter += 1
    if self._log_counter % 50 == 0 and self.get_parameter('enable_control').value:
      self.get_logger().info(
          f'behavior={self._mission_key} cmd surge={cmd.linear.x:.2f} '
          f'sway={cmd.linear.y:.2f} heave={cmd.linear.z:.2f}')

  def _compute_cmd_vel(self, behavior_cmd=None) -> Twist:
    if not self.get_parameter('enable_control').value:
      return Twist()

    depth_cmd = Twist()
    if self.get_parameter('depth_hold_enabled').value and self.latest_pose is not None:
      target = self.get_parameter('target_depth_m').value
      kp = self.get_parameter('depth_kp').value
      depth_cmd, _, _ = compute_depth_hold_cmd(
          self.latest_pose, target, kp=kp)

    behavior_twist = behavior_to_twist(behavior_cmd)
    return merge_twists(behavior_twist, depth_cmd)


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

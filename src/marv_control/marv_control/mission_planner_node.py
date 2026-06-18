"""YAML mission graph planner (inspired by Inspiration Robotics mission_planner)."""

import json
import time
from pathlib import Path

import rclpy
import yaml
from rclpy.node import Node
from std_msgs.msg import String

from marv_control.lib.config_loader import load_marv_config


class MissionPlannerNode(Node):
  """Execute a YAML mission plan by driving master_control behaviors."""

  def __init__(self):
    super().__init__('mission_planner_node')

    self.declare_parameter('plan_file', '')
    self.declare_parameter('config_file', '')
    self.declare_parameter('auto_start', True)
    self.declare_parameter('start_delay_s', 3.0)

    self._config = load_marv_config(self.get_parameter('config_file').value)
    self._plan = self._load_plan(self.get_parameter('plan_file').value)

    self._set_behavior_pub = self.create_publisher(
        String, 'mission_planner/set_behavior', 10)
    self._status_pub = self.create_publisher(String, 'mission_planner/status', 10)
    self.create_subscription(
        String, 'mission_planner/mission_event', self._mission_event_callback, 10)

    self._current_node = None
    self._node_cfg = {}
    self._mission_start = None
    self._timeout_s = 0.0
    self._finished = False
    self._waiting_event = False
    self._started = False

    self._timer = self.create_timer(0.5, self._watchdog_tick)

    if self.get_parameter('auto_start').value:
      delay = float(self.get_parameter('start_delay_s').value)
      if delay > 0.0:
        self._start_timer = self.create_timer(delay, self._delayed_start)
      else:
        self._start_plan()

  def _delayed_start(self):
    if self._started:
      return
    if hasattr(self, '_start_timer') and self._start_timer is not None:
      self._start_timer.cancel()
      self._start_timer = None
    self._start_plan()

  def _load_plan(self, plan_file):
    path = Path(plan_file)
    if not path.is_file():
      self.get_logger().error(f'Mission plan not found: {plan_file}')
      return None
    with path.open('r', encoding='utf-8') as handle:
      return yaml.safe_load(handle) or {}

  def _start_plan(self):
    if self._plan is None:
      return
    self._started = True
    start = self._plan.get('start')
    if not start:
      self.get_logger().error('Mission plan missing start node')
      return
    self._enter_node(start)

  def _enter_node(self, node_id):
    missions = self._plan.get('missions', {})
    node_cfg = missions.get(node_id)
    if node_cfg is None:
      self.get_logger().error(f'Unknown mission node: {node_id}')
      self._publish_status('error', f'unknown node {node_id}')
      self._finished = True
      return

    behavior = node_cfg.get('behavior', node_id)
    self._current_node = node_id
    self._node_cfg = node_cfg
    self._mission_start = time.monotonic()
    self._timeout_s = float(node_cfg.get('timeout', 0.0))
    self._waiting_event = True

    msg = String()
    msg.data = behavior
    self._set_behavior_pub.publish(msg)

    self.get_logger().info(
        f'Mission planner: node={node_id} behavior={behavior}')
    self._publish_status('running', node_id)

  def _watchdog_tick(self):
    if self._finished or not self._waiting_event or self._timeout_s <= 0:
      return
    elapsed = time.monotonic() - self._mission_start
    if elapsed >= self._timeout_s:
      self.get_logger().warn(
          f'Mission planner: timeout on node={self._current_node}')
      transitions = self._node_cfg.get('transitions', {})
      next_node = transitions.get('timeout') or transitions.get('failure')
      self._advance(next_node, success=False, message='timeout')

  def _mission_event_callback(self, msg: String):
    if self._finished or not self._waiting_event:
      return
    try:
      event = json.loads(msg.data)
    except json.JSONDecodeError:
      return

    behavior = self._node_cfg.get('behavior', self._current_node)
    if event.get('behavior') != behavior:
      return

    self._waiting_event = False
    success = bool(event.get('success', True))
    message = event.get('message', '')
    transitions = self._node_cfg.get('transitions', {})
    if success:
      next_node = transitions.get('success') or transitions.get('default')
    else:
      next_node = transitions.get('failure') or transitions.get('default')
    self._advance(next_node, success=success, message=message)

  def _advance(self, next_node, success, message):
    self._waiting_event = False
    if next_node:
      self._enter_node(next_node)
      return
    self._finished = True
    status = 'complete' if success else 'failed'
    self.get_logger().info(
        f'Mission planner: plan {status} ({message})')
    self._publish_status(status, self._current_node or '')

  def _publish_status(self, status, detail):
    payload = {'status': status, 'detail': detail, 'node': self._current_node}
    msg = String()
    msg.data = json.dumps(payload)
    self._status_pub.publish(msg)


def main(args=None):
  rclpy.init(args=args)
  node = MissionPlannerNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

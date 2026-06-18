"""Pose helpers for mission navigation."""

import math


def yaw_from_pose(pose_msg):
  """Extract yaw (rad) from PoseWithCovarianceStamped."""
  if pose_msg is None:
    return None
  q = pose_msg.pose.pose.orientation
  siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
  cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
  return math.atan2(siny_cosp, cosy_cosp)


def horizontal_distance(pose_a, pose_b):
  """XY distance between two poses."""
  if pose_a is None or pose_b is None:
    return None
  ax = pose_a.pose.pose.position.x
  ay = pose_a.pose.pose.position.y
  bx = pose_b.pose.pose.position.x
  by = pose_b.pose.pose.position.y
  return math.hypot(bx - ax, by - ay)


def normalize_angle(angle):
  """Wrap angle to [-pi, pi]."""
  while angle > math.pi:
    angle -= 2.0 * math.pi
  while angle < -math.pi:
    angle += 2.0 * math.pi
  return angle

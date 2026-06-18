"""Depth hold unit tests."""

from geometry_msgs.msg import PoseWithCovarianceStamped

from marv_control.lib.motion_control import compute_depth_hold_cmd, depth_from_pose


def _pose(z, frame='map'):
  msg = PoseWithCovarianceStamped()
  msg.header.frame_id = frame
  msg.pose.pose.position.z = z
  return msg


def test_depth_from_pose_enu_map():
  assert depth_from_pose(_pose(-1.0, 'map')) == 1.0


def test_depth_hold_zero_heave_when_at_target_enu():
  cmd, depth, error = compute_depth_hold_cmd(_pose(-1.0, 'map'), 1.0, kp=0.25)
  assert depth == 1.0
  assert abs(error) < 1e-6
  assert cmd.linear.z == 0.0

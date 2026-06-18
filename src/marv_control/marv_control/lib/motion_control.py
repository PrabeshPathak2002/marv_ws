"""Low-level motion commands from pose estimates."""

from geometry_msgs.msg import PoseWithCovarianceStamped, Twist


def depth_from_pose(pose_msg: PoseWithCovarianceStamped):
    """Depth in meters below surface (positive down).

    Gazebo/map poses use ENU (z up, underwater z < 0). MAVROS odom uses NED (z down).
    """
    z = float(pose_msg.pose.pose.position.z)
    frame = (pose_msg.header.frame_id or '').lower()
    if frame in ('map', 'world', 'gazebo'):
        return max(0.0, -z)
    return z


def compute_depth_hold_cmd(
    pose_msg: PoseWithCovarianceStamped,
    target_depth_m: float,
    kp: float = 0.25,
):
    """PI-less depth hold: heave command from z error, clamped to [-1, 1]."""
    current_z = depth_from_pose(pose_msg)
    error = target_depth_m - current_z
    heave = max(-1.0, min(1.0, kp * error))

    cmd = Twist()
    cmd.linear.x = 0.0
    cmd.linear.y = 0.0
    cmd.linear.z = heave
    cmd.angular.z = 0.0
    return cmd, current_z, error

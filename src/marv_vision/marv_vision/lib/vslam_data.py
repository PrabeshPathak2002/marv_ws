"""Visual SLAM data processing."""


def process_vslam(odometry_msg=None):
    """Extract pose summary from a nav_msgs/Odometry or similar message."""
    if odometry_msg is None:
        return {}

    pose = odometry_msg.pose.pose
    twist = odometry_msg.twist.twist
    return {
        'position': (
            pose.position.x,
            pose.position.y,
            pose.position.z,
        ),
        'orientation': (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
        ),
        'linear_velocity': (
            twist.linear.x,
            twist.linear.y,
            twist.linear.z,
        ),
    }

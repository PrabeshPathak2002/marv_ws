"""Position estimation for Marv AUV.

pos_est is the critical fusion module: it consumes sensor inputs and publishes
where the sub is and how it is moving. Raw sensor passthrough (IMU, pressure,
cameras, battery) belongs elsewhere — not here.
"""

from geometry_msgs.msg import PoseWithCovarianceStamped, TwistWithCovarianceStamped

TOPIC_POSE = '/sensors/pose'
TOPIC_VELOCITY = '/sensors/velocity'


def setup_position_publishers(node):
    """Create pose and velocity publishers (call once at startup)."""
    node._pos_est_publishers = {
        'pose': node.create_publisher(PoseWithCovarianceStamped, TOPIC_POSE, 10),
        'velocity': node.create_publisher(
            TwistWithCovarianceStamped, TOPIC_VELOCITY, 10),
    }
    node.get_logger().info(
        'pos_est: publishing position estimate on /sensors/pose and /sensors/velocity')


def estimate_position(node, inputs):
    """Fuse sensor inputs into position, orientation, and velocity estimates.

    Args:
        node: ROS node (stores _last_depth_m for depth-hold feedback).
        inputs: dict from sensor_io.read_sensor_inputs() — depth, IMU, MAVLink, etc.

    Returns:
        Estimate dict with stamp, position, orientation, linear/angular velocity.
    """
    depth_m = inputs.get('depth_m', 0.0)
    pos = inputs.get('position', (0.0, 0.0, depth_m))
    estimate = {
        'stamp': inputs['stamp'],
        'position': (pos[0], pos[1], depth_m),
        'orientation': inputs.get('orientation', (0.0, 0.0, 0.0, 1.0)),
        'linear_velocity': inputs.get('linear_velocity', (0.0, 0.0, 0.0)),
        'angular_velocity': inputs.get('angular_velocity', (0.0, 0.0, 0.0)),
    }
    node._last_depth_m = depth_m
    return estimate


def publish_position_estimate(node, estimate):
    """Publish fused pose and velocity only."""
    pubs = getattr(node, '_pos_est_publishers', None)
    if pubs is None:
        node.get_logger().error(
            'pos_est: publishers not initialized — call setup_position_publishers first')
        return

    stamp = estimate['stamp']
    px, py, pz = estimate['position']
    ox, oy, oz, ow = estimate['orientation']
    lv = estimate['linear_velocity']
    av = estimate['angular_velocity']

    pose_msg = PoseWithCovarianceStamped()
    pose_msg.header.stamp = stamp
    pose_msg.header.frame_id = 'odom'
    pose_msg.pose.pose.position.x = px
    pose_msg.pose.pose.position.y = py
    pose_msg.pose.pose.position.z = pz
    pose_msg.pose.pose.orientation.x = ox
    pose_msg.pose.pose.orientation.y = oy
    pose_msg.pose.pose.orientation.z = oz
    pose_msg.pose.pose.orientation.w = ow
    pubs['pose'].publish(pose_msg)

    vel_msg = TwistWithCovarianceStamped()
    vel_msg.header.stamp = stamp
    vel_msg.header.frame_id = 'odom'
    vel_msg.twist.twist.linear.x, vel_msg.twist.twist.linear.y, vel_msg.twist.twist.linear.z = lv
    vel_msg.twist.twist.angular.x, vel_msg.twist.twist.angular.y, vel_msg.twist.twist.angular.z = av
    pubs['velocity'].publish(vel_msg)

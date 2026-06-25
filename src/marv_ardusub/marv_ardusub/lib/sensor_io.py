"""Raw sensor input gathering for marv_ardusub.

ARK FPV connects to the Jetson over USB. MAVROS bridges MAVLink; this module
subscribes to MAVROS topics and passes a normalized dict to pos_est.
"""

from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry

from marv_ardusub.lib.ping_io import read_forward_range

GRAVITY_M_PER_S2 = 9.80665

# MAVROS serial link to ARK FPV (ArduSub) over USB — resolved via /dev/serial/by-id at launch.
DEFAULT_FCU_URL = 'auto'

from marv_bringup.mavros_topics import TOPIC_IMU, TOPIC_ODOM


def setup_mavros_subscriptions(node):
    """Subscribe to MAVROS topics and cache the latest messages on the node."""
    node._mavros = {
        'imu': None,
        'odom': None,
        'imu_rx': False,
        'odom_rx': False,
    }

    def imu_cb(msg: Imu):
        node._mavros['imu'] = msg
        node._mavros['imu_rx'] = True

    def odom_cb(msg: Odometry):
        node._mavros['odom'] = msg
        node._mavros['odom_rx'] = True

    node.create_subscription(Imu, TOPIC_IMU, imu_cb, 10)
    node.create_subscription(Odometry, TOPIC_ODOM, odom_cb, 10)
    node.get_logger().info(
        f'sensor_io: listening on {TOPIC_IMU} and {TOPIC_ODOM}')


def _quat_from_imu(imu: Imu):
    o = imu.orientation
    return (o.x, o.y, o.z, o.w)


def _depth_m_from_odom(odom: Odometry):
    """Depth below local origin (NED z is positive down)."""
    return max(0.0, float(odom.pose.pose.position.z))


def read_sensor_inputs(node):
    """Build input dict for pos_est from latest MAVROS data (or safe defaults)."""
    mavros = getattr(node, '_mavros', None)
    stamp = node.get_clock().now().to_msg()
    depth_m = getattr(node, '_last_depth_m', 1.0)
    orientation = (0.0, 0.0, 0.0, 1.0)
    angular_velocity = (0.0, 0.0, 0.0)
    linear_acceleration = (0.0, 0.0, GRAVITY_M_PER_S2)
    position = (0.0, 0.0, depth_m)
    linear_velocity = (0.0, 0.0, 0.0)
    forward_range_m = None
    forward_range_valid = False

    forward_range_m, forward_range_valid = read_forward_range(node)

    if mavros is None:
        return {
            'stamp': stamp,
            'depth_m': depth_m,
            'orientation': orientation,
            'angular_velocity': angular_velocity,
            'linear_acceleration': linear_acceleration,
            'position': position,
            'linear_velocity': linear_velocity,
            'forward_range_m': forward_range_m,
            'forward_range_valid': forward_range_valid,
            'mavros_connected': False,
        }

    imu = mavros.get('imu')
    odom = mavros.get('odom')

    if imu is not None:
        stamp = imu.header.stamp
        orientation = _quat_from_imu(imu)
        av = imu.angular_velocity
        angular_velocity = (av.x, av.y, av.z)
        la = imu.linear_acceleration
        linear_acceleration = (la.x, la.y, la.z)

    if odom is not None:
        stamp = odom.header.stamp
        p = odom.pose.pose.position
        position = (p.x, p.y, p.z)
        depth_m = _depth_m_from_odom(odom)
        lv = odom.twist.twist.linear
        linear_velocity = (lv.x, lv.y, lv.z)
        if not mavros.get('imu_rx'):
            o = odom.pose.pose.orientation
            orientation = (o.x, o.y, o.z, o.w)

    return {
        'stamp': stamp,
        'depth_m': depth_m,
        'orientation': orientation,
        'angular_velocity': angular_velocity,
        'linear_acceleration': linear_acceleration,
        'position': position,
        'linear_velocity': linear_velocity,
        'forward_range_m': forward_range_m,
        'forward_range_valid': forward_range_valid,
        'mavros_connected': mavros.get('imu_rx') or mavros.get('odom_rx'),
    }

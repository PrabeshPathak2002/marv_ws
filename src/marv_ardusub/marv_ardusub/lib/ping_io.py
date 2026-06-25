"""Blue Robotics Ping1D forward range input.

Subscribes to a sensor_msgs/Range topic (default: ping_sonar_ros /ping1d/range)
and republishes on /sensors/range_forward for marv_control.
"""

from sensor_msgs.msg import Range

TOPIC_RANGE_FORWARD = '/sensors/range_forward'
DEFAULT_PING_TOPIC = '/ping1d/range'
MAVROS_RANGEFINDER_TOPIC = '/mavros/distance_sensor/lidar'


def setup_range_subscription(node):
  """Subscribe to Ping / MAVROS rangefinder Range messages."""
  topic = node.get_parameter('ping_range_topic').value
  node._forward_range = {
      'msg': None,
      'valid': False,
      'topic': topic,
  }

  def range_cb(msg: Range):
    node._forward_range['msg'] = msg
    node._forward_range['valid'] = True

  node.create_subscription(Range, topic, range_cb, 10)
  node.get_logger().info(f'ping_io: listening on {topic}')


def setup_range_publisher(node):
  """Create /sensors/range_forward publisher."""
  node._range_forward_pub = node.create_publisher(
      Range, TOPIC_RANGE_FORWARD, 10)


def read_forward_range(node):
  """Return (range_m, valid) from latest Ping message."""
  cache = getattr(node, '_forward_range', None)
  if cache is None or not cache.get('valid') or cache.get('msg') is None:
    return None, False
  msg = cache['msg']
  if msg.range < msg.min_range or msg.range > msg.max_range:
    return None, False
  return float(msg.range), True


def publish_forward_range(node):
  """Republish latest Ping range on /sensors/range_forward."""
  pub = getattr(node, '_range_forward_pub', None)
  if pub is None:
    return
  cache = getattr(node, '_forward_range', None)
  if cache is None or cache.get('msg') is None:
    return
  pub.publish(cache['msg'])

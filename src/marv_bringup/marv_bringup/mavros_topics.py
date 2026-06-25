"""MAVROS2 topic/service paths (Humble plugin namespace)."""

from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

# MAVROS publishes /mavros/state with transient-local durability on Humble.
MAVROS_STATE_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)

# Plugin topics live under /mavros/mavros/ on ROS 2 Humble mavros_node.
TOPIC_STATE = '/mavros/state'
TOPIC_IMU = '/mavros/mavros/data'
TOPIC_ODOM = '/mavros/mavros/odom'
TOPIC_RC_OVERRIDE = '/mavros/rc/override'
# Humble mavros_node may also expose the rc_io subscription here (plugin namespace).
TOPIC_RC_OVERRIDE_ALT = '/mavros/mavros/override'
TOPIC_SETPOINT_VEL = '/mavros/mavros/cmd_vel'

SVC_ARMING = '/mavros/mavros/arming'
SVC_SET_MODE = '/mavros/set_mode'

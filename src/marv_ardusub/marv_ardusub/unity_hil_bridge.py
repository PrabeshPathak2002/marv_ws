#!/usr/bin/env python3
"""Unity HITL bridge: Unity simulation <-> MAVROS (ArduSub on ARK FPV)."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Vector3
from mavros_msgs.msg import HilSensor, RCOut
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32MultiArray

# MAVLink HIL_SENSOR fields_updated bitmask (bits 0-12)
HIL_FIELDS_ALL = (
    (1 << 0) | (1 << 1) | (1 << 2)   # acc
    | (1 << 3) | (1 << 4) | (1 << 5)  # gyro
    | (1 << 9) | (1 << 10)            # abs_pressure, diff_pressure
    | (1 << 11)                       # pressure_alt
    | (1 << 12)                       # temperature
)

ATM_PRESSURE_HPA = 1013.25
WATER_DENSITY_KG_M3 = 1025.0
GRAVITY_M_S2 = 9.80665
DEFAULT_WATER_TEMP_C = 15.0

TOPIC_UNITY_IMU = '/unity/imu'
TOPIC_UNITY_POSE = '/unity/pose'
TOPIC_MAVROS_HIL = '/mavros/hil/sensor'
TOPIC_MAVROS_RC_OUT = '/mavros/rc/out'
TOPIC_UNITY_THRUSTERS = '/unity/thruster_forces'


class UnityHilBridge(Node):
  """Bridge Unity sensor input to MAVROS HIL and RC output back to Unity."""

  def __init__(self):
    super().__init__('unity_hil_bridge')

    self.declare_parameter('thruster_channel_indices', [2, 3, 4, 5])
    self.declare_parameter('pwm_neutral', 1500)
    self.declare_parameter('pwm_scale', 400.0)

    self._latest_imu = None
    self._latest_pose = None

    self._hil_pub = self.create_publisher(HilSensor, TOPIC_MAVROS_HIL, 10)
    self._thruster_pub = self.create_publisher(
        Float32MultiArray, TOPIC_UNITY_THRUSTERS, 10)

    self.create_subscription(Imu, TOPIC_UNITY_IMU, self._imu_callback, 10)
    self.create_subscription(PoseStamped, TOPIC_UNITY_POSE, self._pose_callback, 10)
    self.create_subscription(RCOut, TOPIC_MAVROS_RC_OUT, self._rc_out_callback, 10)

    self.get_logger().info(
        'Unity HITL bridge active: '
        f'{TOPIC_UNITY_IMU} + {TOPIC_UNITY_POSE} -> {TOPIC_MAVROS_HIL}; '
        f'{TOPIC_MAVROS_RC_OUT} -> {TOPIC_UNITY_THRUSTERS}')

  def _imu_callback(self, msg: Imu):
    self._latest_imu = msg
    self._publish_hil_sensor()

  def _pose_callback(self, msg: PoseStamped):
    self._latest_pose = msg
    self._publish_hil_sensor()

  def _depth_m_from_pose(self, pose: PoseStamped):
    """NED z is positive down; depth below surface is positive."""
    return max(0.0, float(pose.pose.position.z))

  def _pressure_from_depth_m(self, depth_m):
    """Absolute pressure in hPa (mbar) from depth."""
    water_hpa = (WATER_DENSITY_KG_M3 * GRAVITY_M_S2 * depth_m) / 100.0
    return ATM_PRESSURE_HPA + water_hpa

  def _publish_hil_sensor(self):
    if self._latest_imu is None:
      return

    imu = self._latest_imu
    depth_m = 0.0
    stamp = imu.header.stamp
    if self._latest_pose is not None:
      depth_m = self._depth_m_from_pose(self._latest_pose)
      stamp = self._latest_pose.header.stamp

    hil = HilSensor()
    hil.header.stamp = stamp
    hil.header.frame_id = 'unity_hil'

    hil.acc = Vector3(
        x=imu.linear_acceleration.x,
        y=imu.linear_acceleration.y,
        z=imu.linear_acceleration.z,
    )
    hil.gyro = Vector3(
        x=imu.angular_velocity.x,
        y=imu.angular_velocity.y,
        z=imu.angular_velocity.z,
    )
    hil.mag = Vector3(x=0.0, y=0.0, z=0.0)

    hil.abs_pressure = float(self._pressure_from_depth_m(depth_m))
    hil.diff_pressure = 0.0
    hil.pressure_alt = float(-depth_m)
    hil.temperature = DEFAULT_WATER_TEMP_C
    hil.fields_updated = HIL_FIELDS_ALL

    self._hil_pub.publish(hil)

  def _pwm_to_normalized(self, pwm):
    neutral = float(self.get_parameter('pwm_neutral').value)
    scale = float(self.get_parameter('pwm_scale').value)
    if scale <= 0.0:
      return 0.0
    return max(-1.0, min(1.0, (float(pwm) - neutral) / scale))

  def _rc_out_callback(self, msg: RCOut):
    indices = list(self.get_parameter('thruster_channel_indices').value)
    channels = list(msg.channels)

    forces = []
    for idx in indices:
      if 0 <= idx < len(channels):
        forces.append(self._pwm_to_normalized(channels[idx]))
      else:
        forces.append(0.0)

    out = Float32MultiArray()
    out.data = forces
    self._thruster_pub.publish(out)


def main(args=None):
  rclpy.init(args=args)
  node = UnityHilBridge()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()

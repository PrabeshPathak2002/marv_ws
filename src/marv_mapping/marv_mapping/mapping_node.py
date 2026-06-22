#!/usr/bin/env python3
"""ROS 2 bridge for vendored auv_mapping (AndrewMontgomeryUSM/marv_auv).

Fuses MAVROS/FCU pose deltas, forward Ping, and f_cam detections into a
landmark-assisted 2D pose published on /sensors/map_pose.
"""

import json
import math

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from sensor_msgs.msg import Imu, Range
from std_msgs.msg import String

from marv_mapping.auv_mapping.compass import Compass
from marv_mapping.auv_mapping.mapping import MappingEngine
from marv_mapping.auv_mapping.sensor_buffer import SensorBuffer
from marv_mapping.auv_mapping.types import SonarDetection, VisionDetection
from marv_vision.lib.detection_format import parse_detection_string

TOPIC_MAP_POSE = '/sensors/map_pose'
TOPIC_LANDMARKS = '/mapping/landmarks'
TOPIC_FCU_POSE = '/sensors/pose'
TOPIC_PING = '/ping1d/range'
TOPIC_VISION = '/f_cam/detections'
TOPIC_IMU = '/mavros/imu/data'

PREQUAL_CLASSES = ('black_gate', 'gate', 'yellow_pole', 'circle', 'Circle', 'cross')


def _yaw_deg_from_quaternion(qx, qy, qz, qw):
    return Compass.quaternion_to_yaw(qx, qy, qz, qw)


def _yaw_rad_to_quaternion(yaw_rad):
    half = yaw_rad * 0.5
    return 0.0, 0.0, math.sin(half), math.cos(half)


class MappingNode(Node):
    """Landmark mapping + dead-reckoning fusion node."""

    def __init__(self):
        super().__init__('mapping_node')

        self.declare_parameter('pose_topic', TOPIC_FCU_POSE)
        self.declare_parameter('ping_topic', TOPIC_PING)
        self.declare_parameter('vision_topic', TOPIC_VISION)
        self.declare_parameter('imu_topic', TOPIC_IMU)
        self.declare_parameter('image_width', 1280)
        self.declare_parameter('map_classes', list(PREQUAL_CLASSES))
        self.declare_parameter('update_rate_hz', 10.0)

        pose_topic = self.get_parameter('pose_topic').value
        ping_topic = self.get_parameter('ping_topic').value
        vision_topic = self.get_parameter('vision_topic').value
        imu_topic = self.get_parameter('imu_topic').value
        self._image_width = int(self.get_parameter('image_width').value)
        self._map_classes = {
            str(c).lower() for c in self.get_parameter('map_classes').value}
        rate = float(self.get_parameter('update_rate_hz').value)

        self._engine = MappingEngine()
        self._buffer = SensorBuffer()
        self._heading_initialized = False
        self._last_pose_xy = None
        self._last_depth_z = 0.0

        self._map_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, TOPIC_MAP_POSE, 10)
        self._landmarks_pub = self.create_publisher(String, TOPIC_LANDMARKS, 10)

        self.create_subscription(
            PoseWithCovarianceStamped, pose_topic, self._pose_callback, 10)
        self.create_subscription(Range, ping_topic, self._ping_callback, 10)
        self.create_subscription(String, vision_topic, self._vision_callback, 10)
        self.create_subscription(Imu, imu_topic, self._imu_callback, 10)
        self.create_timer(1.0 / max(rate, 1.0), self._update_loop)

        self.get_logger().info(
            f'mapping_node: pose={pose_topic} ping={ping_topic} '
            f'vision={vision_topic} -> {TOPIC_MAP_POSE}')

    def _imu_callback(self, msg: Imu):
        q = msg.orientation
        heading_deg = _yaw_deg_from_quaternion(q.x, q.y, q.z, q.w)
        self._buffer.update_heading(heading_deg)
        if not self._heading_initialized:
            self._engine.initialize_heading(heading_deg)
            self._heading_initialized = True
            self.get_logger().info(
                f'mapping reference heading set ({heading_deg:.1f} deg)')

    def _pose_callback(self, msg: PoseWithCovarianceStamped):
        x = float(msg.pose.pose.position.x)
        y = float(msg.pose.pose.position.y)
        self._last_depth_z = float(msg.pose.pose.position.z)
        if self._last_pose_xy is not None:
            dx = x - self._last_pose_xy[0]
            dy = y - self._last_pose_xy[1]
            self._buffer.update_distance(math.hypot(dx, dy))
        self._last_pose_xy = (x, y)

    def _ping_callback(self, msg: Range):
        if msg.range < msg.min_range or msg.range > msg.max_range:
            return
        self._buffer.update_sonar(
            SonarDetection(distance=float(msg.range), angle=0.0, valid=True))

    def _vision_callback(self, msg: String):
        detections = parse_detection_string(msg.data)
        best = None
        for det in detections:
            name = str(det.get('class_name', '')).lower()
            if name not in self._map_classes:
                continue
            if best is None or det.get('confidence', 0.0) > best.get('confidence', 0.0):
                best = det
        if best is None:
            return
        pixel_x = int(float(best.get('x', 0.5)) * self._image_width)
        pixel_y = int(float(best.get('y', 0.5)) * 720)
        self._buffer.update_vision(
            VisionDetection(
                label=str(best.get('class_name', '')),
                confidence=float(best.get('confidence', 0.0)),
                pixel_x=pixel_x,
                pixel_y=pixel_y,
            ))

    def _publish_map_pose(self):
        pose = self._engine.pose
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.pose.position.x = float(pose.x)
        msg.pose.pose.position.y = float(pose.y)
        msg.pose.pose.position.z = self._last_depth_z
        yaw_rad = math.radians(float(pose.yaw))
        qx, qy, qz, qw = _yaw_rad_to_quaternion(yaw_rad)
        msg.pose.pose.orientation.x = qx
        msg.pose.pose.orientation.y = qy
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        self._map_pose_pub.publish(msg)

    def _publish_landmarks(self):
        landmarks = []
        for lm in self._engine.landmarks.landmarks:
            landmarks.append({
                'label': lm.label,
                'x': lm.x,
                'y': lm.y,
                'z': lm.z,
                'confidence': lm.confidence,
                'observations': lm.observations,
            })
        out = String()
        out.data = json.dumps(landmarks)
        self._landmarks_pub.publish(out)

    def _update_loop(self):
        if not self._heading_initialized:
            return

        snap = self._buffer.snapshot()
        self._engine.update(
            heading=snap.heading,
            distance_traveled=snap.distance_traveled,
            sonar_detection=snap.sonar,
            vision_detection=snap.vision,
        )
        self._buffer.clear_transient()
        self._buffer.update_distance(0.0)
        self._publish_map_pose()
        self._publish_landmarks()


def main(args=None):
    rclpy.init(args=args)
    node = MappingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

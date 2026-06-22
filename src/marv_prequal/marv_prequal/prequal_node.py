#!/usr/bin/env python3
"""Pre-qual autonomy: black/red gate pass + neon yellow marker orbit.

Fuses gyro dead-reckoning (ARK IMU), classical OpenCV (exploreHD), Bar02 depth,
and forward-facing Blue Robotics Ping sonar for approach, clearance, and orbit
radius control.
"""

import math
from enum import Enum, auto

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Image, Imu, Range
from std_msgs.msg import Float32

try:
    from cv_bridge import CvBridge
except (ImportError, AttributeError):
    CvBridge = None


class PrequalState(Enum):
    APPROACH_GATE = auto()
    BLOW_THROUGH = auto()
    SPRINT_AND_SEARCH = auto()
    APPROACH_MARKER = auto()
    ORBIT_MARKER = auto()
    SURFACE = auto()


def _normalize_angle(angle_rad):
    while angle_rad > math.pi:
        angle_rad -= 2.0 * math.pi
    while angle_rad < -math.pi:
        angle_rad += 2.0 * math.pi
    return angle_rad


def _yaw_from_quaternion(qx, qy, qz, qw):
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


class PrequalNode(Node):
    """8-thruster AUV pre-qual state machine (BlueROV2 Heavy layout)."""

    def __init__(self):
        super().__init__('prequal_node')

        self.declare_parameter('target_depth', -1.2)
        self.declare_parameter('gate_clearance_time', 4.0)
        self.declare_parameter('max_sprint_time', 20.0)
        self.declare_parameter('orbit_radius', 1.0)
        self.declare_parameter('crash_distance', 0.5)
        self.declare_parameter('ping_topic', '/bluerobotics/ping/distance')
        self.declare_parameter(
            'ping_message_type',
            'float32',
            description='Ping topic type: float32 or range',
        )

        self._target_depth = float(self.get_parameter('target_depth').value)
        self._gate_clearance_time = float(self.get_parameter('gate_clearance_time').value)
        self._max_sprint_time = float(self.get_parameter('max_sprint_time').value)
        self._orbit_radius = float(self.get_parameter('orbit_radius').value)
        self._crash_distance = float(self.get_parameter('crash_distance').value)
        ping_topic = str(self.get_parameter('ping_topic').value)
        ping_msg_type = str(self.get_parameter('ping_message_type').value).lower()

        self._state = PrequalState.APPROACH_GATE
        self._bridge = CvBridge() if CvBridge is not None else None

        self.gate_visible = False
        self.gate_x_error = 0.0
        self.marker_visible = False
        self.marker_x_error = 0.0

        self.current_depth = 0.0
        self.current_yaw = 0.0
        self.ping_distance = float('inf')
        self.initial_yaw = 0.0

        self._blow_through_start = None
        self._sprint_start = None
        self._orbit_yaw_accum = 0.0
        self._orbit_prev_yaw = None
        self._gate_was_visible = False

        self._kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Image, '/explore_hd/image_raw', self.front_cam_callback, 10)
        self.create_subscription(Imu, '/ark/imu/data', self.imu_callback, 10)
        self.create_subscription(Float32, '/bluerobotics/bar02/depth', self.depth_callback, 10)

        if ping_msg_type == 'range':
            self.create_subscription(Range, ping_topic, self.ping_range_callback, 10)
        else:
            self.create_subscription(Float32, ping_topic, self.ping_float_callback, 10)

        self.create_timer(0.05, self.control_loop)

        self.get_logger().info(
            f'prequal_node started — state={self._state.name}, '
            f'target_depth={self._target_depth}, orbit_radius={self._orbit_radius}, '
            f'crash_distance={self._crash_distance}, ping={ping_topic} ({ping_msg_type})')

    def imu_callback(self, msg: Imu):
        q = msg.orientation
        self.current_yaw = _yaw_from_quaternion(q.x, q.y, q.z, q.w)

    def depth_callback(self, msg: Float32):
        self.current_depth = float(msg.data)

    def ping_float_callback(self, msg: Float32):
        self.ping_distance = float(msg.data)

    def ping_range_callback(self, msg: Range):
        if math.isfinite(msg.range) and msg.range >= 0.0:
            self.ping_distance = float(msg.range)

    def _roi_slice(self, frame):
        h = frame.shape[0]
        top = int(h * 0.30)
        bottom = int(h * 0.80)
        return frame[top:bottom, :], top

    def _morph_clean(self, mask):
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)
        return cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, self._kernel)

    def _vertical_contours(self, mask, min_area=400.0, min_aspect=3.5):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        vertical = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w <= 0:
                continue
            area = float(cv2.contourArea(contour))
            aspect = float(h) / float(w)
            if area > min_area and aspect > min_aspect:
                vertical.append((area, x, y, w, h))
        vertical.sort(key=lambda item: item[0], reverse=True)
        return vertical

    def _process_gate(self, roi_bgr):
        self.gate_visible = False
        self.gate_x_error = 0.0

        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60]))
        black_mask = self._morph_clean(black_mask)

        legs = self._vertical_contours(black_mask)
        if len(legs) < 2:
            return

        _, x1, y1, w1, h1 = legs[0]
        _, x2, y2, w2, h2 = legs[1]
        mid_x = ((x1 + w1 / 2.0) + (x2 + w2 / 2.0)) / 2.0
        roi_center_x = roi_bgr.shape[1] / 2.0

        self.gate_x_error = mid_x - roi_center_x
        self.gate_visible = True

    def _process_marker(self, roi_bgr):
        self.marker_visible = False
        self.marker_x_error = 0.0

        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        yellow_mask = cv2.inRange(
            hsv, np.array([20, 100, 100]), np.array([40, 255, 255]))
        yellow_mask = self._morph_clean(yellow_mask)

        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        if w <= 0 or cv2.contourArea(largest) <= 0:
            return

        center_x = x + w / 2.0
        roi_center_x = roi_bgr.shape[1] / 2.0
        self.marker_x_error = center_x - roi_center_x
        self.marker_visible = True

    def front_cam_callback(self, msg: Image):
        if self._bridge is None:
            self.get_logger().warn('cv_bridge unavailable — vision disabled', throttle_duration_sec=5.0)
            return

        try:
            bgr = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn(f'image conversion failed: {exc}', throttle_duration_sec=2.0)
            return

        roi, _ = self._roi_slice(bgr)

        if self._state == PrequalState.APPROACH_GATE:
            self._process_gate(roi)
        elif self._state in (
            PrequalState.SPRINT_AND_SEARCH,
            PrequalState.APPROACH_MARKER,
            PrequalState.ORBIT_MARKER,
        ):
            self._process_marker(roi)

    def _depth_hold(self, twist: Twist):
        twist.linear.z = (self._target_depth - self.current_depth) * 1.5

    def _heading_lock(self, twist: Twist, gain=2.0):
        twist.angular.z = (self.initial_yaw - self.current_yaw) * gain

    def _transition(self, new_state: PrequalState, reason: str):
        self.get_logger().info(f'{self._state.name} -> {new_state.name}: {reason}')
        self._state = new_state

    def _check_ping_failsafe(self):
        if self._state in (PrequalState.ORBIT_MARKER, PrequalState.SURFACE):
            return False
        if self.ping_distance >= self._crash_distance:
            return False
        self.get_logger().error(
            f'COLLISION WARNING — ping {self.ping_distance:.2f} m < '
            f'crash_distance {self._crash_distance:.2f} m; aborting to SURFACE')
        self._transition(PrequalState.SURFACE, 'ping crash failsafe')
        return True

    def control_loop(self):
        twist = Twist()
        now = self.get_clock().now()

        self._depth_hold(twist)

        if self._check_ping_failsafe():
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.angular.z = 0.0
            twist.linear.z = 1.0
            self._cmd_pub.publish(twist)
            return

        if self._state == PrequalState.APPROACH_GATE:
            twist.linear.x = 0.35
            twist.angular.z = -self.gate_x_error * 0.002
            if self.gate_visible:
                self._gate_was_visible = True
            elif self._gate_was_visible:
                self.initial_yaw = self.current_yaw
                self._blow_through_start = now
                self._transition(PrequalState.BLOW_THROUGH, 'gate no longer visible (too close)')

        elif self._state == PrequalState.BLOW_THROUGH:
            twist.linear.x = 0.5
            self._heading_lock(twist)
            elapsed = (now - self._blow_through_start).nanoseconds * 1e-9
            if elapsed >= self._gate_clearance_time:
                self._sprint_start = now
                self._transition(PrequalState.SPRINT_AND_SEARCH, 'gate clearance time elapsed')

        elif self._state == PrequalState.SPRINT_AND_SEARCH:
            twist.linear.x = 0.55
            self._heading_lock(twist)
            if self.marker_visible:
                self._transition(PrequalState.APPROACH_MARKER, 'early catch — marker visible')
            else:
                elapsed = (now - self._sprint_start).nanoseconds * 1e-9
                if elapsed >= self._max_sprint_time:
                    self._transition(PrequalState.SURFACE, 'sprint timeout — marker not found')

        elif self._state == PrequalState.APPROACH_MARKER:
            twist.linear.x = 0.3
            twist.angular.z = -self.marker_x_error * 0.002
            if self.ping_distance <= self._orbit_radius:
                self.initial_yaw = self.current_yaw
                self._orbit_yaw_accum = 0.0
                self._orbit_prev_yaw = self.current_yaw
                self._transition(
                    PrequalState.ORBIT_MARKER,
                    f'ping {self.ping_distance:.2f} m <= orbit_radius {self._orbit_radius:.2f} m')

        elif self._state == PrequalState.ORBIT_MARKER:
            twist.linear.y = 0.35
            twist.angular.z = -self.marker_x_error * 0.003
            ping_err = self.ping_distance - self._orbit_radius
            twist.linear.x = max(-0.35, min(0.35, ping_err * 1.2))

            if self._orbit_prev_yaw is not None:
                delta = abs(_normalize_angle(self.current_yaw - self._orbit_prev_yaw))
                self._orbit_yaw_accum += delta
                self._orbit_prev_yaw = self.current_yaw

            if self._orbit_yaw_accum >= 2.0 * math.pi:
                self._transition(
                    PrequalState.SURFACE,
                    f'full orbit complete ({self._orbit_yaw_accum:.2f} rad)')

        elif self._state == PrequalState.SURFACE:
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.angular.z = 0.0
            twist.linear.z = 1.0

        self._cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = PrequalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

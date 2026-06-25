#!/usr/bin/env python3
"""Bench Ping/range simulator for pre-qual TV testing.

Publishes sensor_msgs/Range so traverse_gate / pass_gate can progress without
a real Ping sonar. Vision mode maps gate bbox area to forward range; pass_gate
auto-clears after a short delay so the mission advances through the gate.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import String

from marv_vision.lib.detection_format import parse_detection_string


def _clamp(value, low, high):
    return max(low, min(high, value))


def area_to_range(area, far_m, close_m, area_far, area_close):
    """Larger gate bbox -> shorter simulated range (closer)."""
    if area <= area_far:
        return far_m
    if area >= area_close:
        return close_m
    t = (area - area_far) / max(area_close - area_far, 1e-6)
    return far_m - t * (far_m - close_m)


class BenchRangeSim(Node):
    def __init__(self):
        super().__init__('bench_range_sim')

        self.declare_parameter('topic', '/mavros/distance_sensor/lidar')
        self.declare_parameter('rate_hz', 10.0)
        self.declare_parameter('mode', 'vision')  # vision | ramp | fixed
        self.declare_parameter('fixed_range_m', 3.0)
        self.declare_parameter('ramp_start_m', 6.0)
        self.declare_parameter('ramp_end_m', 0.9)
        self.declare_parameter('ramp_period_s', 25.0)
        self.declare_parameter('far_range_m', 3.0)
        self.declare_parameter('close_range_m', 0.7)
        self.declare_parameter('area_far', 0.06)
        self.declare_parameter('area_close', 0.38)
        self.declare_parameter('gate_classes', ['gate'])
        self.declare_parameter('conf_min', 0.20)
        self.declare_parameter('no_detection_range_m', 3.0)
        self.declare_parameter('pass_gate_clear_delay_s', 2.5)
        self.declare_parameter('pass_gate_cleared_range_m', 3.5)
        self.declare_parameter('pass_gate_clear_ramp_s', 2.0)
        self.declare_parameter('vision_topic', '/f_cam/detections')
        self.declare_parameter('behavior_topic', 'mission_planner/set_behavior')

        topic = self.get_parameter('topic').value
        self._mode = self.get_parameter('mode').value
        self._gate_classes = {
            c.lower() for c in self.get_parameter('gate_classes').value}
        self._conf_min = float(self.get_parameter('conf_min').value)
        self._far_m = float(self.get_parameter('far_range_m').value)
        self._close_m = float(self.get_parameter('close_range_m').value)
        self._area_far = float(self.get_parameter('area_far').value)
        self._area_close = float(self.get_parameter('area_close').value)
        self._no_det_m = float(self.get_parameter('no_detection_range_m').value)
        self._fixed_m = float(self.get_parameter('fixed_range_m').value)
        self._ramp_start = float(self.get_parameter('ramp_start_m').value)
        self._ramp_end = float(self.get_parameter('ramp_end_m').value)
        self._ramp_period = float(self.get_parameter('ramp_period_s').value)
        self._clear_delay = float(self.get_parameter('pass_gate_clear_delay_s').value)
        self._cleared_m = float(self.get_parameter('pass_gate_cleared_range_m').value)
        self._clear_ramp = float(self.get_parameter('pass_gate_clear_ramp_s').value)

        self._vision_data = ''
        self._behavior = ''
        self._behavior_since = None
        self._ramp_t0 = self.get_clock().now()
        self._range_m = self._no_det_m

        self._pub = self.create_publisher(Range, topic, 10)
        self.create_subscription(
            String, self.get_parameter('vision_topic').value,
            self._vision_cb, 10)
        self.create_subscription(
            String, self.get_parameter('behavior_topic').value,
            self._behavior_cb, 10)

        rate = float(self.get_parameter('rate_hz').value)
        self._timer = self.create_timer(1.0 / max(rate, 1.0), self._publish)

        self.get_logger().info(
            f'bench_range_sim: mode={self._mode} topic={topic} '
            f'(vision maps gate area -> range; pass_gate auto-clears)')

    def _vision_cb(self, msg: String):
        self._vision_data = msg.data or ''

    def _behavior_cb(self, msg: String):
        behavior = (msg.data or '').strip()
        if behavior != self._behavior:
            self._behavior = behavior
            self._behavior_since = self.get_clock().now()

    def _best_gate_area(self):
        detections = parse_detection_string(self._vision_data)
        best = None
        for det in detections:
            name = det.get('class_name', '').lower()
            if name not in self._gate_classes:
                continue
            if det.get('confidence', 0.0) < self._conf_min:
                continue
            area = float(det.get('area', 0.0))
            if best is None or area > best:
                best = area
        return best

    def _vision_range(self):
        area = self._best_gate_area()
        if area is None:
            return self._no_det_m
        return area_to_range(
            area, self._far_m, self._close_m, self._area_far, self._area_close)

    def _ramp_range(self):
        elapsed = (self.get_clock().now() - self._ramp_t0).nanoseconds * 1e-9
        phase = (elapsed % max(self._ramp_period, 1.0)) / max(self._ramp_period, 1.0)
        # Triangle: far -> close -> far
        if phase < 0.5:
            t = phase * 2.0
            return self._ramp_start + t * (self._ramp_end - self._ramp_start)
        t = (phase - 0.5) * 2.0
        return self._ramp_end + t * (self._ramp_start - self._ramp_end)

    def _pass_gate_boost(self, base_range):
        if self._behavior not in ('pass_gate', 'pass_gate_clear'):
            return base_range
        if self._behavior_since is None:
            return base_range
        elapsed = (self.get_clock().now() - self._behavior_since).nanoseconds * 1e-9
        if elapsed < self._clear_delay:
            return base_range
        ramp_t = min(
            1.0,
            (elapsed - self._clear_delay) / max(self._clear_ramp, 0.1),
        )
        return base_range + ramp_t * max(self._cleared_m - base_range, 0.0)

    def _compute_range(self):
        if self._mode == 'fixed':
            base = self._fixed_m
        elif self._mode == 'ramp':
            base = self._ramp_range()
        else:
            base = self._vision_range()
        if self._mode == 'vision':
            base = self._pass_gate_boost(base)
        return _clamp(base, 0.2, 49.0)

    def _publish(self):
        self._range_m = self._compute_range()
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'bench_range_sim'
        msg.radiation_type = Range.INFRARED
        msg.field_of_view = 0.26
        msg.min_range = 0.1
        msg.max_range = 50.0
        msg.range = float(self._range_m)
        self._pub.publish(msg)

        if not hasattr(self, '_log_count'):
            self._log_count = 0
        self._log_count += 1
        if self._log_count == 1 or self._log_count % 20 == 0:
            area = self._best_gate_area()
            area_txt = f'{area:.3f}' if area is not None else 'none'
            self.get_logger().info(
                f'range={self._range_m:.2f} m behavior={self._behavior or "-"} '
                f'gate_area={area_txt}')


def main(args=None):
    rclpy.init(args=args)
    node = BenchRangeSim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

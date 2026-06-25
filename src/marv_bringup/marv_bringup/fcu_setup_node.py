#!/usr/bin/env python3
"""Set FCU flight mode (and optionally arm) after MAVROS connects — for untethered ops."""

import time

import rclpy
from sensor_msgs.msg import Imu
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from marv_bringup.mavros_topics import (
    MAVROS_STATE_QOS,
    SVC_SET_MODE,
    TOPIC_IMU,
    TOPIC_STATE,
)


class FcuSetupNode(Node):
    def __init__(self):
        super().__init__('fcu_setup_node')
        self.declare_parameter('fcu_mode', 'ALT_HOLD')
        self.declare_parameter('auto_arm', False)
        self.declare_parameter('arm_force', True)
        self.declare_parameter('connect_timeout_s', 90.0)
        self.declare_parameter('mavlink_udp_port', 14555)
        self.declare_parameter('mavlink2rest_url', 'http://127.0.0.1:6040/v1/mavlink')

        self._mode = str(self.get_parameter('fcu_mode').value)
        self._auto_arm = bool(self.get_parameter('auto_arm').value)
        self._arm_force = bool(self.get_parameter('arm_force').value)
        self._mavlink_port = int(self.get_parameter('mavlink_udp_port').value)
        self._deadline = time.time() + float(
            self.get_parameter('connect_timeout_s').value)

        self._state = State()
        self._imu_rx = False
        self._mode_sent = False
        self._arm_attempts = 0
        self._done = False
        self._pending = None

        self.create_subscription(State, TOPIC_STATE, self._state_cb, MAVROS_STATE_QOS)
        self.create_subscription(
            Imu, TOPIC_IMU, self._imu_cb, qos_profile_sensor_data)

        self._set_mode_cli = self.create_client(SetMode, SVC_SET_MODE)
        self._arm_cli = self.create_client(CommandBool, '/mavros/mavros/arming')
        self._timer = self.create_timer(1.0, self._tick)
        self.get_logger().info(
            f'fcu_setup: mode={self._mode!r} auto_arm={self._auto_arm} '
            f'arm_force={self._arm_force}')

    def _state_cb(self, msg: State):
        self._state = msg

    def _imu_cb(self, _msg: Imu):
        self._imu_rx = True

    def _link_up(self):
        return self._state.connected or self._imu_rx or bool(self._state.mode)

    def _tick(self):
        if self._done or self._pending is not None:
            return
        if time.time() > self._deadline:
            self.get_logger().error(
                f'fcu_setup: timeout (connected={self._state.connected} '
                f'mode={self._state.mode!r} armed={self._state.armed})')
            self._done = True
            return
        if not self._link_up():
            self.get_logger().info('fcu_setup: waiting for MAVROS link...', 
                                   throttle_duration_sec=5.0)
            return

        if self._state.mode != self._mode and not self._mode_sent:
            if not self._set_mode_cli.wait_for_service(timeout_sec=0.5):
                self.get_logger().warn('fcu_setup: /mavros/set_mode not ready')
                return
            req = SetMode.Request(base_mode=0, custom_mode=self._mode)
            self._pending = self._set_mode_cli.call_async(req)
            self._pending.add_done_callback(self._on_set_mode)
            return

        if self._auto_arm and not self._state.armed:
            self._arm_attempts += 1
            if self._arm_force:
                self._force_arm_mavlink()
            if not self._arm_cli.wait_for_service(timeout_sec=0.5):
                self.get_logger().warn('fcu_setup: arming service not ready')
                return
            req = CommandBool.Request(value=True)
            self._pending = self._arm_cli.call_async(req)
            self._pending.add_done_callback(self._on_arm)
            return

        self.get_logger().info(
            f'fcu_setup: ready mode={self._state.mode} armed={self._state.armed}')
        self._done = True

    def _on_set_mode(self, future):
        self._pending = None
        try:
            result = future.result()
            if result is not None and result.mode_sent:
                self._mode_sent = True
                self.get_logger().info(f'fcu_setup: set mode {self._mode} sent')
            else:
                self.get_logger().warn(f'fcu_setup: set mode {self._mode} rejected')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f'fcu_setup: set mode error: {exc}')

    def _on_arm(self, future):
        self._pending = None
        if self._state.armed:
            self.get_logger().info('fcu_setup: armed')
            self._done = True
            return
        try:
            result = future.result()
            if result is not None and result.success:
                self.get_logger().info('fcu_setup: arm command accepted')
            else:
                self.get_logger().warn(
                    f'fcu_setup: arm attempt {self._arm_attempts} failed '
                    f'(prearm? force={self._arm_force})')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f'fcu_setup: arm error: {exc}')
        if self._state.armed:
            self._done = True

    def _force_arm_mavlink(self):
        import json
        import urllib.request

        url = str(self.get_parameter('mavlink2rest_url').value)
        try:
            urllib.request.urlopen(url.replace('/v1/mavlink', '/v1/mavlink'), timeout=1)
            payload = json.dumps({
                'header': {'system_id': 255, 'component_id': 240, 'sequence': 0},
                'message': {
                    'type': 'COMMAND_LONG',
                    'param1': 1.0, 'param2': 2989.0,
                    'param3': 0.0, 'param4': 0.0, 'param5': 0.0,
                    'param6': 0.0, 'param7': 0.0,
                    'command': {'type': 'MAV_CMD_COMPONENT_ARM_DISARM'},
                    'target_system': 1, 'target_component': 1, 'confirmation': 1,
                },
            }).encode()
            req = urllib.request.Request(
                url, data=payload,
                headers={'Content-Type': 'application/json'}, method='POST')
            urllib.request.urlopen(req, timeout=3)
            self.get_logger().info('fcu_setup: force arm via mavlink2rest')
            return
        except (OSError, ValueError, urllib.error.URLError):
            pass

        try:
            from pymavlink import mavutil
        except ImportError:
            self.get_logger().warn('fcu_setup: pymavlink missing for force arm')
            return
        try:
            port = int(self.get_parameter('mavlink_udp_port').value)
            conn = f'udp:127.0.0.1:{port}'
            m = mavutil.mavlink_connection(conn)
            m.wait_heartbeat(timeout=3)
            m.mav.command_long_send(
                1, 1, 400, 0, 1, 2989, 0, 0, 0, 0, 0)
            self.get_logger().info(f'fcu_setup: force arm mavlink sent ({conn})')
        except (OSError, ValueError, TimeoutError) as exc:
            self.get_logger().warn(f'fcu_setup: force arm mavlink failed: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = FcuSetupNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

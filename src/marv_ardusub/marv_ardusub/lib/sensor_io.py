"""Raw sensor input gathering for marv_ardusub.

Reads hardware / MAVLink data and passes a normalized dict to pos_est.
Raw sensor publishing (IMU, pressure, battery) can be added here later
without touching the position-estimation pipeline.
"""

GRAVITY_M_PER_S2 = 9.80665


def read_sensor_inputs(node):
    """Read raw sensor inputs from ArduSub / MAVLink. Returns inputs dict for pos_est."""
    # TODO: subscribe to /mavros/imu/data, pressure, local_position, etc.
    stamp = node.get_clock().now().to_msg()
    depth_m = getattr(node, '_last_depth_m', 1.0)
    return {
        'stamp': stamp,
        'depth_m': depth_m,
        'orientation': (0.0, 0.0, 0.0, 1.0),
        'angular_velocity': (0.0, 0.0, 0.0),
        'linear_acceleration': (0.0, 0.0, GRAVITY_M_PER_S2),
        'position': (0.0, 0.0, depth_m),
        'linear_velocity': (0.0, 0.0, 0.0),
    }

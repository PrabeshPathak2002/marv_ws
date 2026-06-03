"""Forward /cmd_vel from Marv to MAVROS (ArduSub on ARK FPV)."""

from geometry_msgs.msg import Twist
from mavros_msgs.msg import OverrideRCIn, State

TOPIC_STATE = '/mavros/state'
TOPIC_RC_OVERRIDE = '/mavros/rc/override'
TOPIC_SETPOINT_VEL = '/mavros/setpoint_velocity/cmd_vel'


def setup_mavros_actuation(node):
    """Publishers and MAVROS state cache for actuation."""
    node.declare_parameter('command_backend', 'mavros_rc')
    node.declare_parameter('hold_depth_with_autopilot', False)
    node.declare_parameter('heave_pwm_invert', False)
    node.declare_parameter('rc_neutral_pwm', 1500)
    node.declare_parameter('rc_scale_pwm', 400)
    node.declare_parameter('rc_min_pwm', 1100)
    node.declare_parameter('rc_max_pwm', 1900)

    node._actuation = {
        'backend': node.get_parameter('command_backend').value,
        'hold_depth_with_autopilot': node.get_parameter(
            'hold_depth_with_autopilot').value,
        'heave_pwm_invert': node.get_parameter('heave_pwm_invert').value,
        'rc_neutral_pwm': int(node.get_parameter('rc_neutral_pwm').value),
        'rc_scale_pwm': int(node.get_parameter('rc_scale_pwm').value),
        'rc_min_pwm': int(node.get_parameter('rc_min_pwm').value),
        'rc_max_pwm': int(node.get_parameter('rc_max_pwm').value),
        'mavros_state': State(),
        'cmd_count': 0,
    }

    def state_cb(msg: State):
        node._actuation['mavros_state'] = msg

    node.create_subscription(State, TOPIC_STATE, state_cb, 10)
    node._actuation['rc_pub'] = node.create_publisher(
        OverrideRCIn, TOPIC_RC_OVERRIDE, 10)
    node._actuation['setpoint_pub'] = node.create_publisher(
        Twist, TOPIC_SETPOINT_VEL, 10)

    node.get_logger().info(
        f"mavros_actuation: backend={node._actuation['backend']}")


def _velocity_to_pwm(node, value):
    act = node._actuation
    value = max(-1.0, min(1.0, float(value)))
    pwm = act['rc_neutral_pwm'] + value * act['rc_scale_pwm']
    return int(max(act['rc_min_pwm'], min(act['rc_max_pwm'], pwm)))


def _publish_rc_override(node, surge, sway, heave, yaw):
    act = node._actuation
    thr_pwm = None
    if not act['hold_depth_with_autopilot']:
        if act['heave_pwm_invert']:
            heave = -heave
        thr_pwm = _velocity_to_pwm(node, heave)

    msg = OverrideRCIn()
    msg.channels = [OverrideRCIn.CHAN_NOCHANGE] * 18
    if thr_pwm is not None:
        msg.channels[2] = thr_pwm
    msg.channels[3] = _velocity_to_pwm(node, yaw)
    msg.channels[4] = _velocity_to_pwm(node, surge)
    msg.channels[5] = _velocity_to_pwm(node, sway)
    act['rc_pub'].publish(msg)


def forward_cmd_vel(node, cmd: Twist):
    """Send Marv /cmd_vel to MAVROS using the configured backend."""
    act = node._actuation
    backend = act['backend']

    if backend == 'disabled':
        return

    if not act['mavros_state'].connected:
        return

    surge = cmd.linear.x
    sway = cmd.linear.y
    heave = cmd.linear.z
    yaw = cmd.angular.z

    if backend == 'mavros_rc':
        _publish_rc_override(node, surge, sway, heave, yaw)
    elif backend == 'setpoint_velocity':
        act['setpoint_pub'].publish(cmd)
    elif backend == 'log_only':
        pass
    else:
        node.get_logger().warn(f'Unknown command_backend: {backend}')
        return

    act['cmd_count'] += 1
    if act['cmd_count'] == 1 or act['cmd_count'] % 50 == 0:
        node.get_logger().info(
            f'cmd_vel -> MAVROS ({backend}): '
            f'surge={surge:.2f} sway={sway:.2f} heave={heave:.2f} yaw={yaw:.2f}')

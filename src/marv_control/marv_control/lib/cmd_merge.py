"""Merge behavior velocity commands into a single Twist."""

from geometry_msgs.msg import Twist


def behavior_to_twist(cmd_dict):
    """Convert {surge, sway, heave, yaw} dict to Twist."""
    if not cmd_dict:
        return Twist()
    msg = Twist()
    msg.linear.x = float(cmd_dict.get('surge', 0.0))
    msg.linear.y = float(cmd_dict.get('sway', 0.0))
    msg.linear.z = float(cmd_dict.get('heave', 0.0))
    msg.angular.z = float(cmd_dict.get('yaw', 0.0))
    return msg


def merge_twists(primary, secondary):
    """Use non-zero primary surge/sway/yaw; keep secondary heave if primary heave is zero."""
    out = Twist()
    out.linear.x = primary.linear.x if primary.linear.x else secondary.linear.x
    out.linear.y = primary.linear.y if primary.linear.y else secondary.linear.y
    out.linear.z = primary.linear.z if primary.linear.z else secondary.linear.z
    out.angular.z = primary.angular.z if primary.angular.z else secondary.angular.z
    return out

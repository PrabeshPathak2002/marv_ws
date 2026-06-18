"""Depth hold control."""

DEPTH_KP = 0.25


def maintain_depth(node, target_depth_m=1.0, current_depth_m=None):
    """Compute heave command to hold target depth (NED z positive down)."""
    if current_depth_m is None:
        current_depth_m = getattr(node, '_last_depth_m', target_depth_m)

    error = target_depth_m - current_depth_m
    heave = max(-1.0, min(1.0, DEPTH_KP * error))
    return {'heave': heave, 'error_m': error, 'current_depth_m': current_depth_m}

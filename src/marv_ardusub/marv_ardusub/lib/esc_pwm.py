"""ESC PWM calculation for thrusters."""

RC_NEUTRAL = 1500
RC_SCALE = 400
RC_MIN = 1100
RC_MAX = 1900


def calculate_esc_pwm(thrust_command, channel=0, neutral=RC_NEUTRAL,
                      scale=RC_SCALE, pwm_min=RC_MIN, pwm_max=RC_MAX):
    """Convert normalized thrust [-1, 1] to ESC PWM microseconds."""
    value = max(-1.0, min(1.0, float(thrust_command)))
    pwm = int(neutral + value * scale)
    return max(pwm_min, min(pwm_max, pwm))

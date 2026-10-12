"""Wheel speed mapping and physically limited setpoint ramps."""
from dataclasses import dataclass
import math


MAX_WHEEL_SPEED = 14.0
MAX_STEER_DIFFERENCE = 0.72
MAX_ACCELERATION = 24.0
BRAKE_ACCELERATION = 38.0


def wheel_targets(throttle: float, steer: float = 0.0, *, direction: int = 1,
                  turn: str = "straight", max_speed: float = MAX_WHEEL_SPEED,
                  max_difference: float = MAX_STEER_DIFFERENCE) -> tuple[float, float]:
    """Return left/right wheel angular velocity setpoints in rad/s.

    The steering delta uses the magnitude of the base speed. This makes a left
    command produce positive robot yaw in both forward and reverse motion.
    """
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    throttle = max(0.0, min(100.0, float(throttle)))
    steer = max(0.0, min(100.0, float(steer)))
    base = direction * (throttle / 100.0) * max_speed
    delta = (steer / 100.0) * max_difference * abs(base)
    if turn == "left":
        left, right = base - delta, base + delta
    elif turn == "right":
        left, right = base + delta, base - delta
    elif turn == "straight":
        left = right = base
    elif turn == "brake":
        left = right = 0.0
    else:
        raise ValueError(f"unknown turn: {turn}")

    peak = max(abs(left), abs(right))
    if peak > max_speed:
        factor = max_speed / peak
        left, right = left * factor, right * factor
    return left, right


@dataclass
class RateLimitedDrive:
    left: float = 0.0
    right: float = 0.0

    def step(self, target_left: float, target_right: float, dt: float,
             *, braking: bool = False) -> tuple[float, float]:
        rate = BRAKE_ACCELERATION if braking else MAX_ACCELERATION
        limit = rate * max(0.0, dt)
        self.left = _approach(self.left, target_left, limit)
        self.right = _approach(self.right, target_right, limit)
        return self.left, self.right

    def stop(self) -> None:
        self.left = self.right = 0.0


def _approach(value: float, target: float, limit: float) -> float:
    if math.isclose(value, target, abs_tol=limit):
        return target
    return value + math.copysign(limit, target - value)

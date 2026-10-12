"""Geometric overlap approximation for unique cone contact penalties."""
from dataclasses import dataclass, field
import math


def _overlap_box_circle(dx: float, dy: float, orientation: tuple[float, ...],
                        half_x: float, half_y: float, radius: float) -> bool:
    # Webots orientation matrices are row-major; the first two columns are
    # the robot-local X/Y axes in world coordinates.
    local_x = dx * orientation[0] + dy * orientation[3]
    local_y = dx * orientation[1] + dy * orientation[4]
    nearest_x = max(-half_x, min(half_x, local_x))
    nearest_y = max(-half_y, min(half_y, local_y))
    return math.hypot(local_x - nearest_x, local_y - nearest_y) <= radius


def car_cone_overlap(car_position: tuple[float, ...], orientation: tuple[float, ...],
                     cone_position: tuple[float, ...]) -> bool:
    """Approximate actual Box/Cylinder bounding-object intersection in 3D.

    Tests the chassis OBB and four wheel bounding boxes against the cone's
    vertical cylinder. A simple center-distance pass is deliberately avoided.
    """
    dx, dy = cone_position[0] - car_position[0], cone_position[1] - car_position[1]
    if abs(cone_position[2] - car_position[2]) <= 0.065 + 0.125:
        if _overlap_box_circle(dx, dy, orientation, 0.25, 0.17, 0.12):
            return True

    for wheel_x in (-0.17, 0.17):
        for wheel_y in (-0.22, 0.22):
            wheel_z = -0.08
            wx = car_position[0] + orientation[0] * wheel_x + orientation[1] * wheel_y + orientation[2] * wheel_z
            wy = car_position[1] + orientation[3] * wheel_x + orientation[4] * wheel_y + orientation[5] * wheel_z
            wz = car_position[2] + orientation[6] * wheel_x + orientation[7] * wheel_y + orientation[8] * wheel_z
            if abs(cone_position[2] - wz) > 0.08 + 0.125:
                continue
            if _overlap_box_circle(cone_position[0] - wx, cone_position[1] - wy,
                                   orientation, 0.08, 0.035, 0.12):
                return True
    return False


@dataclass
class ConePenaltyLedger:
    known_ids: tuple[str, ...]
    hit_ids: set[str] = field(default_factory=set)

    def contact(self, cone_id: str) -> bool:
        if cone_id not in self.known_ids or cone_id in self.hit_ids:
            return False
        self.hit_ids.add(cone_id)
        return True

    @property
    def seconds(self) -> float:
        return 2.0 * len(self.hit_ids)

    def reset(self) -> None:
        self.hit_ids.clear()

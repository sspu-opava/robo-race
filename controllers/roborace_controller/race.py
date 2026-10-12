"""Geometry helpers for ordered, directional checkpoint timing."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Gate:
    x: float
    y: float
    nx: float
    ny: float
    half_width: float
    label: str


@dataclass(frozen=True)
class GateCrossing:
    crossed: bool
    in_bounds: bool
    reverse: bool = False


def crossing(previous: tuple[float, float], current: tuple[float, float], gate: Gate) -> GateCrossing:
    """Detect center-of-robot crossing of a finite oriented gate segment."""
    x0, y0 = previous[0] - gate.x, previous[1] - gate.y
    x1, y1 = current[0] - gate.x, current[1] - gate.y
    s0 = x0 * gate.nx + y0 * gate.ny
    s1 = x1 * gate.nx + y1 * gate.ny
    if s0 > 0.0 and s1 <= 0.0:
        return GateCrossing(False, False, True)
    if not (s0 <= 0.0 and s1 > 0.0):
        return GateCrossing(False, False)
    ratio = s0 / (s0 - s1)
    px = x0 + ratio * (x1 - x0)
    py = y0 + ratio * (y1 - y0)
    tangent = -gate.ny * px + gate.nx * py
    return GateCrossing(True, abs(tangent) <= gate.half_width)


def distance_to_segment(point: tuple[float, float], start: tuple[float, float],
                        end: tuple[float, float]) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class RouteTracker:
    def __init__(self, checkpoints: list[Gate], finish: Gate):
        self.checkpoints = checkpoints
        self.finish = finish
        self.next_checkpoint = 0
        self.finished = False

    def update(self, previous: tuple[float, float], current: tuple[float, float]) -> str | None:
        gates = self.checkpoints + [self.finish]
        for index, gate in enumerate(gates):
            event = crossing(previous, current, gate)
            if event.reverse and index <= self.next_checkpoint:
                return f"Brána {gate.label} byla projetá opačným směrem."
            if not event.crossed:
                continue
            if not event.in_bounds:
                continue
            if index < self.next_checkpoint:
                continue
            if index > self.next_checkpoint:
                return f"Brány musíš projet ve správném pořadí (nejdříve {gates[self.next_checkpoint].label})."
            if index == len(self.checkpoints):
                self.finished = True
            else:
                self.next_checkpoint += 1
        return None

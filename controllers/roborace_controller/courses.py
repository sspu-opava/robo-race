"""Course geometry and physical feature placement for each RoboRace level."""
from dataclasses import dataclass

from race import Gate


EASY_SAMPLE = """# Základní trať se dvěma zatáčkami.
PLYN(45)
DOPREDU(5.00)
DOPREDU(1.50)
PLYN(35)
VLEVO(100, 2.60)
DOPREDU(3.80)
VPRAVO(100, 2.60)
PLYN(45)
DOPREDU(5.00)
DOPREDU(1.50)
BRZDA(0.60)
"""

SLALOM_SAMPLE = """# Projeď vlny a slalom; před zatáčkou uber.
PLYN(45)
DOPREDU(3.60)
VPRAVO(100, 1.00)
VLEVO(100, 1.00)
DOPREDU(1.30)
VLEVO(100, 2.60)
DOPREDU(3.20)
PLYN(35)
VPRAVO(100, 2.60)
DOPREDU(5.00)
DOPREDU(1.50)
BRZDA(0.60)
"""

MOUNTAIN_SAMPLE = """# Serpentiny: drž směr na rovinách a zatoč na konci každé řady.
PLYN(100)
DOPREDU(5.00)
DOPREDU(2.20)
VLEVO(65, 1.10)
VLEVO(65, 1.10)
DOPREDU(5.00)
DOPREDU(2.20)
VPRAVO(65, 1.10)
VPRAVO(65, 1.10)
DOPREDU(5.00)
DOPREDU(2.20)
BRZDA(0.60)
"""


@dataclass(frozen=True)
class Course:
    level: int
    name: str
    description: str
    track_segments: tuple[tuple[tuple[float, float], tuple[float, float]], ...]
    checkpoints: tuple[Gate, ...]
    finish: Gate
    # x, y, road height, half-height, length, width, rotation about Z
    bumps: tuple[tuple[float, float, float, float, float, float, float], ...]
    # x, y, centre height, rotation about Z
    chicanes: tuple[tuple[float, float, float, float], ...]
    sample_program: str
    road_segments: tuple[
        tuple[tuple[float, float, float], tuple[float, float, float]], ...
    ] = ()


_BASE_SEGMENTS = (
    ((-3.8, -1.5), (0.0, -1.5)),
    ((0.0, -1.5), (0.0, 1.5)),
    ((0.0, 1.5), (3.8, 1.5)),
)
_BASE_GATES = (
    Gate(-2.4, -1.5, 1.0, 0.0, 0.62, "1"),
    Gate(0.0, -0.05, 0.0, 1.0, 0.62, "2"),
    Gate(2.0, 1.5, 1.0, 0.0, 0.62, "3"),
)
_FINISH = Gate(3.35, 1.5, 1.0, 0.0, 0.62, "CÍL")

_SLALOM_SEGMENTS = (
    ((-3.8, -1.5), (-2.4, -1.5)),
    ((-2.4, -1.5), (-2.05, -1.94)),
    ((-2.05, -1.94), (-1.30, -1.94)),
    ((-1.30, -1.94), (-0.28, -1.94)),
    ((-0.28, -1.94), (0.0, -1.12)),
    ((0.0, -1.12), (0.0, 1.5)),
    ((0.0, 1.5), (0.40, 1.5)),
    ((0.40, 1.5), (0.62, 1.34)),
    ((0.62, 1.34), (1.43, 1.34)),
    ((1.43, 1.34), (1.92, 1.84)),
    ((1.92, 1.84), (2.76, 1.84)),
    ((2.76, 1.84), (3.10, 1.5)),
    ((3.10, 1.5), (3.8, 1.5)),
)

# The mountain level is a three-row switchback. Its first row climbs 0.45 m;
# the remaining two elevated rows and hairpins continue at the summit.
_MOUNTAIN_PATH = (
    (-3.8, -1.5, 0.0),
    (-2.3, -1.5, 0.0),
    (0.0, -1.5, 0.45),
    (3.8, -1.5, 0.45),
    (4.2, -1.5, 0.45),
    (4.5, -1.2, 0.45),
    (4.5, -0.3, 0.45),
    (4.2, 0.0, 0.45),
    (3.8, 0.0, 0.45),
    (0.0, 0.0, 0.45),
    (-3.8, 0.0, 0.45),
    (-4.2, 0.0, 0.45),
    (-4.5, 0.3, 0.45),
    (-4.5, 1.2, 0.45),
    (-4.2, 1.5, 0.45),
    (-3.8, 1.5, 0.45),
    (0.0, 1.5, 0.45),
    (3.8, 1.5, 0.45),
)


def _xy_segments(path: tuple[tuple[float, float, float], ...]):
    return tuple(((a[0], a[1]), (b[0], b[1])) for a, b in zip(path, path[1:]))


def _xyz_segments(path: tuple[tuple[float, float, float], ...]):
    return tuple((a, b) for a, b in zip(path, path[1:]))


COURSES = {
    1: Course(
        1, "Základní zatáčky", "Plochá trať se dvěma zatáčkami.",
        _BASE_SEGMENTS, _BASE_GATES, _FINISH, (), (), EASY_SAMPLE,
    ),
    2: Course(
        2, "Nerovnosti", "Stejný okruh doplňují dvě fyzické vlny.",
        _BASE_SEGMENTS, _BASE_GATES, _FINISH,
        ((-1.35, -1.5, 0.0, 0.008, 0.42, 1.30, 0.0),
         (0.0, 0.45, 0.0, 0.010, 0.42, 1.30, 1.57079632679)),
        (), EASY_SAMPLE,
    ),
    3: Course(
        3, "Slalom a překážky", "Čtyři vlny a bariéry jsou umístěné přímo v klikaté dráze.",
        _SLALOM_SEGMENTS, _BASE_GATES, _FINISH,
        ((-3.0, -1.5, 0.0, 0.008, 0.34, 1.30, 0.0),
         (-2.0, -1.94, 0.0, 0.010, 0.42, 1.30, 0.0),
         (-0.75, -1.94, 0.0, 0.008, 0.34, 1.20, 0.0),
         (0.0, 0.45, 0.0, 0.010, 0.38, 1.30, 1.57079632679)),
        ((-1.3, -1.58, 0.15, 0.0),
         (-0.12, -1.58, 0.15, 0.0),
         (1.0, 1.69, 0.15, 0.0),
         (2.9, 1.36, 0.15, -0.78539816339)),
        SLALOM_SAMPLE,
    ),
    4: Course(
        4, "Horská serpentina",
        "Dlouhá třířadá serpentina se stoupáním 0,45 m, čtyřmi bariérami a nepravidelnými hrboly.",
        _xy_segments(_MOUNTAIN_PATH),
        (
            Gate(0.8, -1.5, 1.0, 0.0, 0.62, "1"),
            Gate(0.0, 0.0, -1.0, 0.0, 0.62, "2"),
            Gate(0.5, 1.5, 1.0, 0.0, 0.62, "3"),
        ),
        _FINISH,
        ((2.6, -1.5, 0.45, 0.035, 0.34, 1.12, 0.0),
         (0.8, 0.0, 0.45, 0.050, 0.62, 0.86, 0.15),
         (-1.8, 0.0, 0.45, 0.030, 0.38, 1.18, -0.12),
         (-2.0, 1.5, 0.45, 0.045, 0.56, 0.92, 0.28)),
        ((-2.8, -1.15, 0.15, 0.0),
         (2.0, 0.35, 0.60, 0.0),
         (1.2, 1.15, 0.60, 0.0),
         (-4.15, 0.75, 0.60, 1.57079632679)),
        MOUNTAIN_SAMPLE,
        _xyz_segments(_MOUNTAIN_PATH),
    ),
}

# Geometry changes on level 3 get a fresh leaderboard identity. Existing
# levels 1 and 2 remain compatible; the new course starts its own table.
LEVEL_CONFIG_IDS = {
    1: "junior-track-v2-level-1",
    2: "junior-track-v2-level-2",
    3: "junior-track-v3-level-3",
    4: "junior-track-v1-level-4",
}


def course_for(level: int) -> Course | None:
    return COURSES.get(level)

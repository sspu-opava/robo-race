"""Webots Supervisor controller and WWI endpoint for RoboRace Junior."""
from collections import deque
import math
from pathlib import Path
import time

from controller import Supervisor

from collisions import ConePenaltyLedger, car_cone_overlap
from courses import COURSES, LEVEL_CONFIG_IDS
from drivetrain import RateLimitedDrive
from interpreter import Interpreter
from language import ParseError, parse_program
from leaderboard import Leaderboard, clean_nickname
from protocol import decode_message, encode_message
from race import RouteTracker, distance_to_segment


TIME_LIMIT = 35.0
OFFICIAL_RUNS_PER_NICKNAME = 2
COUNTDOWN_SECONDS = 1.0
MAX_TILT_DEGREES = 50.0
TILT_HOLD_SECONDS = 0.25
TRACK_HALF_WIDTH = 0.72
START_POSITION = (-3.8, -1.5, 0.16)
START_ORIENTATION = (0.0, 0.0, 1.0, 0.0)
CONE_DEFS = ("CONE_1", "CONE_2", "CONE_3")
CONE_STARTS = ((-1.45, -2.00, 0.13), (0.47, 0.35, 0.13), (2.55, 1.03, 0.13))
CONE_STARTS_BY_LEVEL = {
    1: CONE_STARTS,
    2: CONE_STARTS,
    3: ((-3.4, -1.5, 0.13), (0.0, -0.5, 0.13), (2.3, 1.84, 0.13)),
    4: ((-3.5, -1.85, 0.13), (-3.0, -0.35, 0.58), (1.8, 1.85, 0.58)),
}
BUMP_DEFS = ("BUMP_1", "BUMP_2", "BUMP_3", "BUMP_4")
CHICANE_DEFS = ("CHICANE_1", "CHICANE_2", "CHICANE_3", "CHICANE_4")
ROAD_DEFS = tuple(f"COURSE_ROAD_{index:02d}" for index in range(1, 18))
MOUNTAIN_GATE_DEFS = (
    "MOUNTAIN_GATE_START", "MOUNTAIN_GATE_1", "MOUNTAIN_GATE_2",
    "MOUNTAIN_GATE_3", "MOUNTAIN_GATE_FINISH",
)
ROAD_WIDTH = 1.40
ROAD_THICKNESS = 0.12
SAMPLE_PROGRAM = COURSES[1].sample_program


class RoboRaceController:
    def __init__(self):
        self.robot = Supervisor()
        self.step_ms = int(self.robot.getBasicTimeStep())
        self.dt = self.step_ms / 1000.0
        self.motors = [self.robot.getDevice(name) for name in
                       ("left_front", "left_rear", "right_front", "right_rear")]
        if any(motor is None for motor in self.motors):
            raise RuntimeError("Chybí některý z motorů robota.")
        for motor in self.motors:
            motor.setPosition(float("inf"))
            motor.setVelocity(0.0)
        self.drive = RateLimitedDrive()
        self.car = self.robot.getFromDef("ROBORACE_CAR")
        self.viewpoint = self.robot.getFromDef("COURSE_VIEW")
        self.cones = [self.robot.getFromDef(name) for name in CONE_DEFS]
        self.bumps = [self.robot.getFromDef(name) for name in BUMP_DEFS]
        self.chicanes = [self.robot.getFromDef(name) for name in CHICANE_DEFS]
        self.course_art = self.robot.getFromDef("CLASSIC_COURSE_ART")
        self.checkpoint_labels = self.robot.getFromDef("CLASSIC_CHECKPOINT_LABELS")
        self.road_tiles = [self.robot.getFromDef(name) for name in ROAD_DEFS]
        self.mountain_gates = [self.robot.getFromDef(name) for name in MOUNTAIN_GATE_DEFS]
        if (self.car is None or self.course_art is None or self.checkpoint_labels is None
                or any(node is None for node in self.cones + self.bumps + self.chicanes
                       + self.road_tiles + self.mountain_gates)):
            raise RuntimeError("Svět neobsahuje všechny objekty RoboRace.")
        self.level = 1
        self.course = COURSES[self.level]
        self.leaderboard_path = Path(__file__).resolve().parents[2] / "data" / "leaderboard.json"
        self.leaderboard = self._leaderboard_for(self.level)
        self.state = "IDLE"
        self.mode = None
        self.nickname = ""
        self.interpreter = None
        self.route = None
        self.previous_xy = None
        self.started_at = 0.0
        self.countdown_left = 0.0
        self.tilt_time = 0.0
        self.cone_penalties = ConePenaltyLedger(CONE_DEFS)
        self.last_line = None
        self.source = ""
        self.last_telemetry = 0.0
        self.result = None
        self.attempts: dict[tuple[int, str], int] = {}
        self.default_nickname_index = 1
        self.seen_requests: deque[str] = deque(maxlen=256)
        self.seen_request_set: set[str] = set()
        self._restore_scene()

    def _leaderboard_for(self, level: int) -> Leaderboard:
        path = self.leaderboard_path if level == 1 else self.leaderboard_path.with_name(f"leaderboard-level-{level}.json")
        return Leaderboard(path, LEVEL_CONFIG_IDS[level])

    def send(self, payload: dict) -> None:
        self.robot.wwiSendText(encode_message(payload))

    def run(self) -> None:
        self._send_ready()
        while self.robot.step(self.step_ms) != -1:
            now = self.robot.getTime()
            self._receive_messages()
            self._advance(now)
            self._publish(now)

    def _receive_messages(self) -> None:
        raw = self.robot.wwiReceiveText()
        while raw:
            if raw == "init robot window":
                self._send_ready()
                raw = self.robot.wwiReceiveText()
                continue
            message, error = decode_message(raw)
            if error:
                self.send({"type": "error", "message": error})
            elif message:
                request_id = message.get("request_id")
                if request_id and request_id in self.seen_request_set:
                    raw = self.robot.wwiReceiveText()
                    continue
                if request_id:
                    if len(self.seen_requests) == self.seen_requests.maxlen:
                        oldest = self.seen_requests.popleft()
                        self.seen_request_set.discard(oldest)
                    self.seen_requests.append(request_id)
                    self.seen_request_set.add(request_id)
                self._handle(message)
            raw = self.robot.wwiReceiveText()

    def _send_ready(self) -> None:
        self.send({"type": "ready", "state": self.state, "config_id": LEVEL_CONFIG_IDS[self.level],
                   "level": self.level,
                   "levels": [{"id": item.level, "name": item.name, "description": item.description}
                              for item in COURSES.values()],
                   "basic_time_step_ms": self.step_ms, "time_limit": TIME_LIMIT,
                   "official_runs_per_player": OFFICIAL_RUNS_PER_NICKNAME,
                   "leaderboard": self.leaderboard.top(), "warning": self.leaderboard.warning,
                   "sample_program": self.course.sample_program})

    def _handle(self, message: dict) -> None:
        kind = message["type"]
        request_id = message.get("request_id")
        if kind == "hello":
            self._send_ready()
            if self.state in {"COUNTDOWN", "RUNNING"}:
                self._publish(self.robot.getTime())
            if self.result is not None:
                self.send(self.result)
            return
        if kind == "restore_view":
            if self.viewpoint is not None:
                self.viewpoint.getField("position").setSFVec3f([0.0, -8.0, 11.0])
                self.viewpoint.getField("orientation").setSFRotation(
                    [-0.413223395, 0.413223395, 0.811475725, 1.778194113])
                self.viewpoint.getField("fieldOfView").setSFFloat(0.9)
            self.send({"type": "view_restored", "message": "Obnoven pohled na celou dráhu."})
            return
        if kind == "set_level":
            if self.state in {"COUNTDOWN", "RUNNING"}:
                self.send({"type": "error", "request_id": request_id,
                           "message": "Obtížnost lze změnit až po jízdě."})
                return
            level = message.get("level")
            if type(level) is not int or level not in COURSES:
                self.send({"type": "error", "request_id": request_id,
                           "message": "Vyber platnou úroveň 1 až 4."})
                return
            self.level = level
            self.course = COURSES[level]
            self.leaderboard = self._leaderboard_for(level)
            self._clear_run()
            self.state = "IDLE"
            self._restore_scene()
            self.send({"type": "level_changed", "level": level,
                       "name": self.course.name, "description": self.course.description,
                       "sample_program": self.course.sample_program,
                       "config_id": LEVEL_CONFIG_IDS[level],
                       "leaderboard": self.leaderboard.top(), "warning": self.leaderboard.warning})
            return
        if kind == "validate":
            try:
                instructions, warnings = parse_program(message.get("source", ""))
                self.send({"type": "validation_result", "request_id": request_id,
                           "valid": True, "instruction_count": len(instructions), "warnings": warnings})
            except ParseError as error:
                self.send({"type": "validation_result", "request_id": request_id, "valid": False,
                           "line": error.line, "message": error.message})
            return
        if kind == "start":
            if self.state in {"COUNTDOWN", "RUNNING"}:
                self.send({"type": "error", "request_id": request_id, "message": "Jízda už probíhá."})
                return
            mode = message.get("mode")
            if mode not in {"test", "official"}:
                self.send({"type": "error", "request_id": request_id, "message": "Neznámý režim jízdy."})
                return
            try:
                instructions, warnings = parse_program(message.get("source", ""))
            except ParseError as error:
                self.send({"type": "error", "request_id": request_id, "line": error.line,
                           "message": error.message})
                return
            nickname = clean_nickname(message.get("nickname"), "Hrac-001")
            key = (self.level, nickname.casefold())
            if mode == "official" and self.attempts.get(key, 0) >= OFFICIAL_RUNS_PER_NICKNAME:
                self.send({"type": "error", "request_id": request_id,
                           "message": "Tento soutěžící už využil oba oficiální pokusy. Zvol „Nový soutěžící“."})
                return
            if mode == "official":
                self.attempts[key] = self.attempts.get(key, 0) + 1
            self._set_wheels(0.0, 0.0)
            self._restore_scene()
            self.drive.stop()
            self.interpreter = Interpreter(instructions)
            self.route = RouteTracker(list(self.course.checkpoints), self.course.finish)
            self.previous_xy = None
            self.started_at = 0.0
            self.countdown_left = COUNTDOWN_SECONDS
            self.tilt_time = 0.0
            self.cone_penalties.reset()
            self.last_line = None
            self.mode = mode
            self.nickname = nickname
            self.source = message.get("source", "")
            self.result = None
            self.state = "COUNTDOWN"
            self.send({"type": "accepted", "request_id": request_id, "state": self.state,
                       "mode": mode, "nickname": nickname, "warnings": warnings,
                       "remaining_attempts": (OFFICIAL_RUNS_PER_NICKNAME - self.attempts[key]
                                               if mode == "official" else None)})
            return
        if kind == "reset":
            self._set_wheels(0.0, 0.0)
            self._restore_scene()
            self._clear_run()
            self.state = "IDLE"
            self.result = None
            self.send({"type": "reset", "state": self.state})
            return
        if kind == "new_competitor":
            nickname = clean_nickname(message.get("nickname"), self._next_default_nickname())
            nickname_key = nickname.casefold()
            for key in tuple(self.attempts):
                if key[1] == nickname_key:
                    self.attempts.pop(key, None)
            self.send({"type": "competitor_ready", "nickname": nickname,
                       "message": "Počítadlo lokální relace bylo vynulováno.",
                       "remaining_attempts": OFFICIAL_RUNS_PER_NICKNAME})
            return
        if kind == "admin_reset":
            if message.get("confirm") is not True:
                self.send({"type": "error", "message": "Vymazání žebříčku vyžaduje potvrzení."})
                return
            self.leaderboard.reset()
            self.send({"type": "leaderboard", "entries": self.leaderboard.top(), "message": "Žebříček byl vymazán."})

    def _advance(self, now: float) -> None:
        if self.state == "COUNTDOWN":
            self._set_wheels(0.0, 0.0)
            self.countdown_left -= self.dt
            if self.countdown_left <= 0.0:
                self.state = "RUNNING"
                self.started_at = now
                self.previous_xy = self._xy()
                self.send({"type": "execution", "state": self.state, "elapsed": 0.0,
                           "checkpoint": 0, "checkpoint_total": len(self.course.checkpoints), "penalties": 0})
                self._apply_next_instruction()
            return
        if self.state != "RUNNING":
            return

        elapsed = max(0.0, now - self.started_at)
        current_xy = self._xy()
        if min(distance_to_segment(current_xy, start, end)
               for start, end in self.course.track_segments) > TRACK_HALF_WIDTH:
            self._finish(False, elapsed, "Robot opustil povolený koridor.")
            return
        tilt = self._tilt_degrees()
        if tilt > MAX_TILT_DEGREES:
            self.tilt_time += self.dt
            if self.tilt_time >= TILT_HOLD_SECONDS:
                self._finish(False, elapsed, "Robot se převrátil.")
                return
        else:
            self.tilt_time = 0.0

        race_error = self.route.update(self.previous_xy, current_xy) if self.previous_xy is not None else None
        self.previous_xy = current_xy
        if race_error:
            self._finish(False, elapsed, race_error)
            return

        self._check_cones()
        if self.route.finished:
            self._finish(True, elapsed, "Cíl projet.")
            return
        if elapsed >= TIME_LIMIT:
            self._finish(False, elapsed, "Vypršel limit 35 sekund.")
            return

        self._apply_next_instruction(elapsed)

    def _apply_next_instruction(self, elapsed: float = 0.0) -> None:
        step = self.interpreter.step(self.dt)
        self.last_line = step.source_line
        left, right = self.drive.step(step.left, step.right, self.dt, braking=step.braking)
        self._set_wheels(left, right)
        if step.program_finished:
            self._finish(False, elapsed, "Program skončil a robot nedojel do cíle.")

    def _publish(self, now: float) -> None:
        if self.state == "RESULT":
            return
        wall_now = time.monotonic()
        if wall_now - self.last_telemetry < 0.12:
            return
        self.last_telemetry = wall_now
        elapsed = max(0.0, now - self.started_at) if self.state == "RUNNING" else 0.0
        self.send({"type": "execution", "state": self.state, "source_line": self.last_line,
                   "elapsed": round(elapsed, 3), "checkpoint": self.route.next_checkpoint if self.route else 0,
                   "checkpoint_total": len(self.course.checkpoints), "penalties": len(self.cone_penalties.hit_ids),
                   "penalty_seconds": self.cone_penalties.seconds, "mode": self.mode,
                   "position": [round(v, 2) for v in self._xy()]})

    def _finish(self, success: bool, raw_time: float, reason: str) -> None:
        self._set_wheels(0.0, 0.0)
        self.drive.stop()
        penalty_seconds = self.cone_penalties.seconds
        final_time = raw_time + penalty_seconds if success else None
        result = {"type": "result", "state": "FINISHED" if success else "FAILED",
                  "valid": success, "raw_time": round(raw_time, 6),
                  "penalties": len(self.cone_penalties.hit_ids), "penalty_seconds": penalty_seconds,
                  "final_time": round(final_time, 6) if final_time is not None else None,
                  "mode": self.mode, "nickname": self.nickname, "reason": reason,
                  "source_line": self.last_line, "cone_ids": sorted(self.cone_penalties.hit_ids),
                  "checkpoint": len(self.course.checkpoints) if success else (self.route.next_checkpoint if self.route else 0),
                  "checkpoint_total": len(self.course.checkpoints),
                  "position": [round(v, 3) for v in self.car.getPosition()]}
        if success and self.mode == "official":
            self.leaderboard.add_result(self.nickname, raw_time, len(self.cone_penalties.hit_ids), penalty_seconds,
                                        getattr(self, "source", ""))
            result["leaderboard"] = self.leaderboard.top()
        self.result = result
        self.state = "RESULT"
        self._restore_scene()
        self._clear_run(keep_result=True)
        self.state = "RESULT"
        self.send(result)

    def _restore_scene(self) -> None:
        mountain_level = self.level == 4
        art_position = [0.0, 0.0, -50.0 if mountain_level else 0.0]
        self.course_art.getField("translation").setSFVec3f(art_position)
        self.checkpoint_labels.getField("translation").setSFVec3f(art_position)

        for node in self.road_tiles:
            node.getField("translation").setSFVec3f([0.0, 0.0, -50.0])
        for node, (start, end) in zip(self.road_tiles, self.course.road_segments):
            self._place_road_tile(node, start, end)

        for node in self.mountain_gates:
            node.getField("translation").setSFVec3f([0.0, 0.0, -50.0])
        if mountain_level:
            gate_positions = (
                (-3.1, -1.5, 0.0, 0.0),
                (0.8, -1.5, 0.45, 0.0),
                (0.0, 0.0, 0.45, 0.0),
                (0.5, 1.5, 0.45, 0.0),
                (3.35, 1.5, 0.45, 0.0),
            )
            for node, (x, y, road_z, angle) in zip(self.mountain_gates, gate_positions):
                node.getField("translation").setSFVec3f([x, y, road_z + 0.012])
                node.getField("rotation").setSFRotation([0.0, 0.0, 1.0, angle])

        for node in self.bumps:
            node.getField("translation").setSFVec3f([0.0, 0.0, -50.0])
        for node, (x, y, road_z, half_height, size_x, size_y, angle) in zip(self.bumps, self.course.bumps):
            dimensions = [size_x, size_y, half_height * 2.0]
            shape = node.getField("children").getMFNode(0)
            shape.getField("geometry").getSFNode().getField("size").setSFVec3f(dimensions)
            node.getField("boundingObject").getSFNode().getField("size").setSFVec3f(dimensions)
            node.getField("rotation").setSFRotation([0.0, 0.0, 1.0, angle])
            node.getField("translation").setSFVec3f([x, y, road_z + half_height])
        for node in self.chicanes:
            node.getField("translation").setSFVec3f([0.0, 0.0, -50.0])
            node.resetPhysics()
        for node, (x, y, z, angle) in zip(self.chicanes, self.course.chicanes):
            node.getField("translation").setSFVec3f([x, y, z])
            node.getField("rotation").setSFRotation([0.0, 0.0, 1.0, angle])
            node.resetPhysics()
        self.car.getField("translation").setSFVec3f(list(START_POSITION))
        self.car.getField("rotation").setSFRotation(list(START_ORIENTATION))
        self.car.resetPhysics()
        for node, position in zip(self.cones, CONE_STARTS_BY_LEVEL[self.level]):
            node.getField("translation").setSFVec3f(list(position))
            node.getField("rotation").setSFRotation([0.0, 0.0, 1.0, 0.0])
            node.resetPhysics()

    @staticmethod
    def _place_road_tile(node, start, end) -> None:
        dx, dy, dz = (end[index] - start[index] for index in range(3))
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length <= 1e-9:
            return
        # Rotate local +X onto the 3D route segment, allowing uphill ramps.
        dot = max(-1.0, min(1.0, dx / length))
        angle = math.acos(dot)
        ax, ay, az = 0.0, -dz, dy
        axis_length = math.sqrt(ax * ax + ay * ay + az * az)
        if axis_length <= 1e-9:
            ax, ay, az = 0.0, 0.0, 1.0
        else:
            ax, ay, az = ax / axis_length, ay / axis_length, az / axis_length
        node.getField("translation").setSFVec3f([
            (start[0] + end[0]) * 0.5,
            (start[1] + end[1]) * 0.5,
            (start[2] + end[2]) * 0.5 - ROAD_THICKNESS * 0.5,
        ])
        node.getField("rotation").setSFRotation([ax, ay, az, angle])
        tile_size = [length + 0.05, ROAD_WIDTH, ROAD_THICKNESS]
        node.getField("size").setSFVec3f(tile_size)
        node.getField("edgeSize").setSFVec3f([length + 0.05, 0.035, 0.008])
        edge_y = ROAD_WIDTH * 0.5 - 0.03
        edge_z = ROAD_THICKNESS * 0.5 + 0.005
        node.getField("leftEdgeTranslation").setSFVec3f([0.0, edge_y, edge_z])
        node.getField("rightEdgeTranslation").setSFVec3f([0.0, -edge_y, edge_z])

    def _clear_run(self, keep_result: bool = False) -> None:
        self.interpreter = None
        self.route = None
        self.previous_xy = None
        self.started_at = 0.0
        self.countdown_left = 0.0
        self.tilt_time = 0.0
        self.cone_penalties.reset()
        self.last_line = None
        self.mode = None
        self.nickname = ""
        self.drive.stop()
        if not keep_result:
            self.result = None

    def _set_wheels(self, left: float, right: float) -> None:
        for motor in self.motors[:2]:
            motor.setVelocity(left)
        for motor in self.motors[2:]:
            motor.setVelocity(right)

    def _xy(self) -> tuple[float, float]:
        position = self.car.getPosition()
        return float(position[0]), float(position[1])

    def _tilt_degrees(self) -> float:
        matrix = self.car.getOrientation()
        # The third column is the robot-local up vector in world coordinates.
        vertical_alignment = max(-1.0, min(1.0, float(matrix[8])))
        return math.degrees(math.acos(vertical_alignment))

    def _check_cones(self) -> None:
        car_position = self.car.getPosition()
        matrix = self.car.getOrientation()
        for name, node in zip(CONE_DEFS, self.cones):
            if name in self.cone_penalties.hit_ids:
                continue
            if car_cone_overlap(car_position, matrix, node.getPosition()):
                self.cone_penalties.contact(name)

    def _next_default_nickname(self) -> str:
        nickname = f"Hrac-{self.default_nickname_index:03d}"
        self.default_nickname_index += 1
        return nickname


if __name__ == "__main__":
    RoboRaceController().run()

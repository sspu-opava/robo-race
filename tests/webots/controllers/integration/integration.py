"""Real Webots integration probe; never writes to the competition leaderboard."""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "controllers" / "roborace_controller"))
print("INTEGRATION: importing controller", flush=True)
from roborace_controller import RoboRaceController, SAMPLE_PROGRAM
from courses import COURSES, LEVEL_CONFIG_IDS
from leaderboard import Leaderboard

REPORTS = Path(__file__).resolve().parents[2] / "reports"
REPORTS.mkdir(exist_ok=True)


class Integration(RoboRaceController):
    def _leaderboard_for(self, level):
        return Leaderboard(REPORTS / f"leaderboard-level-{level}.json", LEVEL_CONFIG_IDS[level])

    def __init__(self):
        print("INTEGRATION: connecting to Webots", flush=True)
        super().__init__()
        for level in COURSES:
            self._leaderboard_for(level).reset()
        self.leaderboard = self._leaderboard_for(self.level)
        self.final_pose = None
        print("INTEGRATION: connected", flush=True)

    def send(self, payload):
        if payload["type"] in {"result", "error", "accepted"}:
            print(json.dumps({key: payload[key] for key in ("type", "state", "valid", "raw_time", "penalties", "message")
                              if key in payload}, ensure_ascii=True), flush=True)
        super().send(payload)

    def _finish(self, success, raw_time, reason):
        self.final_pose = {
            "position": self.car.getPosition(),
            "yaw": math.atan2(self.car.getOrientation()[3], self.car.getOrientation()[0]),
        }
        super()._finish(success, raw_time, reason)

    def run(self):
        self.robot.simulationSetMode(self.robot.SIMULATION_MODE_FAST)
        for _ in range(64):
            if self.robot.step(self.step_ms) == -1:
                return
        self.robot.exportImage(str(REPORTS / "course.png"), 100)
        print("INTEGRATION: course image exported", flush=True)
        cases_path = REPORTS / "cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8")) if cases_path.exists() else [
            {"name": "forward", "source": "PLYN(35)\nDOPREDU(1.5)\nBRZDA(0.6)", "check": "forward"},
            {"name": "reverse", "source": "PLYN(35)\nDOZADU(0.5)\nBRZDA(0.6)", "check": "reverse"},
            {"name": "left", "source": "PLYN(35)\nVLEVO(100, 0.8)\nBRZDA(0.6)", "check": "left"},
            {"name": "right", "source": "PLYN(35)\nVPRAVO(100, 0.8)\nBRZDA(0.6)", "check": "right"},
            {"name": "reverse-left", "source": "PLYN(35)\nDOZADU(0.2)\nVLEVO(100, 0.7)\nBRZDA(0.6)", "check": "left"},
            {"name": "reverse-right", "source": "PLYN(35)\nDOZADU(0.2)\nVPRAVO(100, 0.7)\nBRZDA(0.6)", "check": "right"},
            {"name": "cone-contact", "source": "PLYN(35)\nDOPREDU(1.5)\nBRZDA(0.6)",
             "cone_position": [-3.15, -1.5, 0.13], "check": "contact"},
            {"name": "outside", "source": "PLYN(45)\nDOZADU(3)\nBRZDA(0.6)", "check": "outside"},
            *[{"name": f"sample-{i + 1}", "source": SAMPLE_PROGRAM, "check": "finish"} for i in range(10)],
            {"name": "level-2-sample", "level": 2, "source": COURSES[2].sample_program, "check": "finish"},
            {"name": "level-3-sample", "level": 3, "source": COURSES[3].sample_program, "check": "finish"},
            {"name": "official", "source": SAMPLE_PROGRAM, "mode": "official", "check": "official"},
        ]
        results = []
        for index, case in enumerate(cases):
            level = case.get("level", 1)
            if level != self.level:
                self._handle({"type": "set_level", "level": level, "request_id": f"level-{index}"})
            self._handle({"type": "start", "mode": case.get("mode", "test"),
                          "nickname": case.get("nickname", "Integration"),
                          "source": case["source"], "request_id": f"integration-{index}"})
            if "cone_position" in case:
                self.cones[0].getField("translation").setSFVec3f(case["cone_position"])
                self.cones[0].resetPhysics()
            trace = []
            cone_contacts = set()
            tick = 0
            while self.state in {"COUNTDOWN", "RUNNING"}:
                if self.robot.step(self.step_ms) == -1:
                    return
                self._receive_messages()
                self._advance(self.robot.getTime())
                self._publish(self.robot.getTime())
                if case.get("check") == "contact":
                    car_points = self.car.getContactPoints(True)
                    for cone in self.cones:
                        if any(sum((a - b) ** 2 for a, b in zip(car_point.point, cone_point.point)) < 1e-10
                               and car_point.point[2] > 0.02
                               for car_point in car_points for cone_point in cone.getContactPoints()):
                            cone_contacts.add(cone.getId())
                tick += 1
                if self.state == "RUNNING" and tick % 5 == 0:
                    trace.append({"t": round(self.robot.getTime() - self.started_at, 3),
                                  "line": self.last_line, "cp": self.route.next_checkpoint,
                                  "position": self.car.getPosition(),
                                  "yaw": math.atan2(self.car.getOrientation()[3], self.car.getOrientation()[0])})
            check = case.get("check")
            pose = self.final_pose
            passed = True
            if check == "forward": passed = pose["position"][0] > -3.4
            elif check == "reverse": passed = pose["position"][0] < -3.9
            elif check == "left": passed = pose["yaw"] > 0.1
            elif check == "right": passed = pose["yaw"] < -0.1
            elif check == "contact": passed = self.result["penalties"] == 1 and bool(cone_contacts)
            elif check == "outside": passed = not self.result["valid"] and "koridor" in self.result["reason"]
            elif check in {"finish", "official"}:
                passed = self.result["valid"] and self.result["checkpoint"] == 3 and self.result["penalties"] == 0
                if check == "finish": passed = passed and not self.leaderboard.top()
                else:
                    saved = Leaderboard(REPORTS / "leaderboard-level-1.json", LEVEL_CONFIG_IDS[1]).top()
                    passed = passed and len(saved) == 1 and saved[0]["nickname"] == "Integration"
            restored = self.car.getField("translation").getSFVec3f() == [-3.8, -1.5, 0.16]
            passed = passed and restored
            results.append({"name": case["name"], "passed": passed, "result": self.result,
                            "final_pose": self.final_pose, "cone_contacts": sorted(cone_contacts), "trace": trace})
            print(f"INTEGRATION: {case['name']} {'PASS' if passed else 'FAIL'}", flush=True)
            (REPORTS / "integration.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("INTEGRATION: completed", flush=True)
        self.robot.simulationQuit(0 if all(result["passed"] for result in results) else 1)
        self.robot.step(self.step_ms)


Integration().run()

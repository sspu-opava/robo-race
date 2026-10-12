"""Prepare an isolated course and run physical checks using installed Webots."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--webots", default=shutil.which("webots") or
                        "C:/Program Files/Webots/msys64/mingw64/bin/webots.exe")
    parser.add_argument("--port", type=int, default=1250)
    args = parser.parse_args()
    test_project = ROOT / "tests" / "webots"
    worlds = test_project / "worlds"
    worlds.mkdir(exist_ok=True)
    world = (ROOT / "worlds" / "roborace.wbt").read_text(encoding="utf-8")
    world = world.replace("../protos/RoboRaceCar.proto", "../../../protos/RoboRaceCar.proto")
    world = world.replace("../protos/CourseRoad.proto", "../../../protos/CourseRoad.proto")
    world = world.replace("../protos/CourseGate.proto", "../../../protos/CourseGate.proto")
    world = world.replace('DEF ROBORACE_CAR RoboRaceCar { }',
                          'DEF ROBORACE_CAR RoboRaceCar { controller "integration" window "<none>" }')
    world_path = worlds / "integration.wbt"
    world_path.write_text(world, encoding="utf-8")
    report_path = test_project / "reports" / "integration.json"
    previous_modified = report_path.stat().st_mtime_ns if report_path.exists() else None
    result = subprocess.run([args.webots, "--mode=fast", "--batch", "--stdout", "--stderr",
                             f"--port={args.port}", str(world_path)], cwd=ROOT, timeout=180)
    if not report_path.exists() or report_path.stat().st_mtime_ns == previous_modified:
        return result.returncode or 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    times = [case["result"]["raw_time"] for case in report if case["name"].startswith("sample-")]
    failed = [case["name"] for case in report if not case["passed"]]
    print(f"Integration: {len(report) - len(failed)}/{len(report)} passed")
    if times:
        print(f"Sample: {len(times)} trials; {min(times):.3f}–{max(times):.3f} s; spread {max(times)-min(times):.3f} s")
    if failed:
        print("Failed: " + ", ".join(failed))
    print(f"Report: {report_path}")
    return 1 if failed or len(report) != 21 or result.returncode else 0


if __name__ == "__main__":
    sys.exit(main())

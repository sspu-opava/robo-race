# RoboRace project guide

## Architecture

- `worlds/roborace.wbt` assembles the physical course and the single Supervisor robot. Levels 1–3 share the original layout; level 4 builds its raised road from Supervisor-positioned tiles.
- `protos/RoboRaceCar.proto` owns the robot body and four powered wheel joints.
- `controllers/roborace_controller/language.py` parses RoboScript with a strict regex grammar; it never evaluates user source.
- `interpreter.py` advances one timed command per simulation step. `drivetrain.py` maps throttle and steering to side wheel targets and ramps them.
- `race.py` contains finite directed gate geometry and route tracking. The main Webots controller handles Supervisor node state, run state, collision approximation, time, and WWI messages.
- `leaderboard.py` persists official valid results as atomic JSON replacements and a last-valid backup.
- `plugins/robot_windows/roborace/` is a local HTML/CSS/JS Webots Robot Window. It uses the local Webots WebSocket endpoint and does not fetch libraries or fonts.

## Development commands

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

Open `worlds/roborace.wbt` in Webots R2025a and run the simulation for integration checks. Confirm controller startup, WWI messages, motor direction, gate progression, cone contacts, reset and repeated runs. Do not report a Webots integration check unless Webots actually ran.

## Axes and simulation constants

Use Webots `coordinateSystem "ENU"`: world X/Y are horizontal and world Z is up. The car's local +X points forward; local +Y points left; the wheel axle is local Y. Gate normals point along the allowed travel direction. Use the orientation matrix's local-up column to estimate tilt.

R2025a Cylinder/Cone primitives have a local Z axis: rotate wheel Solids by -π/2 about X so the cylinders align with +Y. HingeJoint axes must be +Y for positive wheel velocity to drive along +X. Keep cones upright without an extra rotation. Viewpoint looks along local +X, so its yaw and pitch must aim from `(0, -8, 11)` towards the arena centre. `COURSE_VIEW` is also used by the panel's restore-view action.

Serialize WWI JSON with `ensure_ascii=True`: the R2025a Python binding's `wwiSendText` uses character count for byte length, truncating raw Unicode. Send an explicit application `hello` after WebSocket connect, because Webots consumes `init robot window` itself. On reconnect, send current state and the last result.

Current settings are `basicTimeStep 16 ms`, wheel radius `0.08 m`, wheel speed cap `14 rad/s`, steering asymmetry `0.72`, wheel command ramp `24 rad/s²`, brake ramp `38 rad/s²`, corridor half-width `0.72 m`, level 4 road width `1.40 m`, level 4 climb `0.45 m`, tilt threshold `50°` held for `0.25 s`, race limit `35 s`, unique cone penalty `2 s`, program limit `40` commands and `32 s` timed duration. Keep geometry, controller constants, documentation, and `LEVEL_CONFIG_IDS` in agreement.

## Calibration steps

1. In Webots, verify the wheel joints turn the car toward local +X for positive wheel setpoints. Check that `VLEVO` gives positive robot yaw both forward and in reverse.
2. Tune tire contact friction, wheel torque, chassis mass/COM, and the controller ramp while keeping body and wheel bounding objects realistic.
3. Adjust checkpoint gate locations/widths and the route corridor to match visible lane markings and rail clearance; keep every cone, bump, and barrier inside its selected road.
4. Tune `SAMPLE_PROGRAM` with physical test runs until it reliably passes every gate without leaving the corridor. Run at least ten identical trials before calling it reproducible.
5. If any course or physics constant changes, update that course's `LEVEL_CONFIG_IDS` entry; do not merge results across configurations.

`python tests/run_webots_integration.py` regenerates the isolated world and runs 19 physical checks, including ten identical calibrated sample trials. The default runner requires all cases; `reports/cases.json` is only a local calibration override. `node tests/robot_window_smoke.mjs PORT` exercises the production WWI client against an active main world.

## RoboScript rules

Preserve exactly the six commands `PLYN`, `DOPREDU`, `DOZADU`, `VLEVO`, `VPRAVO`, and `BRZDA`, their ranges, strict uppercase syntax, one command per line, and server-side limits. Keep controller modules importable without Webots when possible so pure logic remains unit-testable.

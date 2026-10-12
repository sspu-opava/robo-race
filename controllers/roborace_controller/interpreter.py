"""Non-blocking RoboScript interpreter advanced once per simulation step."""
from dataclasses import dataclass
from language import Instruction
from drivetrain import wheel_targets


@dataclass(frozen=True)
class DriveStep:
    left: float
    right: float
    source_line: int | None
    braking: bool = False
    program_finished: bool = False


class Interpreter:
    def __init__(self, instructions: list[Instruction], coast_seconds: float = 2.0):
        self.instructions = instructions
        self.coast_seconds = coast_seconds
        self.index = 0
        self.current: Instruction | None = None
        self.remaining = 0.0
        self.throttle = 40.0
        self.direction = 1
        self.coast_remaining: float | None = None
        self.done = False
        self.last_line: int | None = None

    def step(self, dt: float) -> DriveStep:
        if self.done:
            return DriveStep(0.0, 0.0, self.last_line, True, True)

        # PLYN has no duration; consume it immediately without creating a pause.
        while self.current is None and self.index < len(self.instructions):
            instruction = self.instructions[self.index]
            if instruction.opcode == "PLYN":
                self.throttle = instruction.args[0]
                self.last_line = instruction.source_line
                self.index += 1
                continue
            self.current = instruction
            self.remaining = instruction.duration
            self.last_line = instruction.source_line

        if self.current is None:
            if self.coast_remaining is None:
                self.coast_remaining = self.coast_seconds
            self.coast_remaining -= dt
            if self.coast_remaining <= 0.0:
                self.done = True
            return DriveStep(0.0, 0.0, self.last_line, True, self.done)

        command = self.current
        if command.opcode == "DOPREDU":
            self.direction = 1
            targets = wheel_targets(self.throttle, direction=self.direction)
            braking = False
        elif command.opcode == "DOZADU":
            self.direction = -1
            targets = wheel_targets(self.throttle, direction=self.direction)
            braking = False
        elif command.opcode in {"VLEVO", "VPRAVO"}:
            steer = command.args[0]
            turn = "left" if command.opcode == "VLEVO" else "right"
            targets = wheel_targets(self.throttle, steer, direction=self.direction, turn=turn)
            braking = False
        else:  # BRZDA
            targets = (0.0, 0.0)
            braking = True

        self.remaining -= dt
        if self.remaining <= 1e-9:
            self.index += 1
            self.current = None
        return DriveStep(targets[0], targets[1], command.source_line, braking)

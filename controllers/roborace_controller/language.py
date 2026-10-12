"""Strict, non-executing parser for the six RoboScript 1.0 commands."""
from dataclasses import dataclass
import re


MAX_INSTRUCTIONS = 40
MAX_TOTAL_DURATION = 32.0
MAX_SOURCE_LENGTH = 10_000
_NUMBER = r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)"
_COMMAND = re.compile(rf"^([A-Z]+)\s*\(\s*({_NUMBER})(?:\s*,\s*({_NUMBER}))?\s*\)$")


@dataclass(frozen=True)
class Instruction:
    opcode: str
    args: tuple[float, ...]
    source_line: int

    @property
    def duration(self) -> float:
        return self.args[-1] if self.opcode != "PLYN" else 0.0


class ParseError(ValueError):
    def __init__(self, line: int, message: str):
        self.line = line
        self.message = message
        super().__init__(f"Řádek {line}: {message}")


def parse_program(source: str) -> tuple[list[Instruction], list[str]]:
    if not isinstance(source, str):
        raise ParseError(1, "Program musí být text.")
    if len(source) > MAX_SOURCE_LENGTH:
        raise ParseError(1, f"Program je příliš dlouhý (maximum {MAX_SOURCE_LENGTH} znaků).")

    instructions: list[Instruction] = []
    warnings: list[str] = []
    total_duration = 0.0
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = _COMMAND.fullmatch(line)
        if not match:
            raise ParseError(line_number, "Použij jeden příkaz ve tvaru NÁZEV(čísla); desetinná místa odděluj tečkou.")
        opcode = match.group(1)
        if opcode not in {"PLYN", "DOPREDU", "DOZADU", "VLEVO", "VPRAVO", "BRZDA"}:
            raise ParseError(line_number, f"Neznámý příkaz {opcode}.")
        values = tuple(float(value) for value in match.groups()[1:] if value is not None)
        expected = 1 if opcode in {"PLYN", "DOPREDU", "DOZADU", "BRZDA"} else 2
        if len(values) != expected:
            raise ParseError(line_number, f"{opcode} očekává {expected} {'parametr' if expected == 1 else 'parametry'}.")
        if opcode == "PLYN":
            if not 0.0 <= values[0] <= 100.0:
                raise ParseError(line_number, "Plyn musí být v rozsahu 0 až 100 %.")
            if values[0] == 0.0:
                warnings.append(f"Řádek {line_number}: PLYN(0) nechá další pohybové povely stát.")
        elif opcode in {"DOPREDU", "DOZADU", "BRZDA"}:
            if not 0.05 <= values[0] <= 5.0:
                raise ParseError(line_number, "Doba musí být v rozsahu 0,05 až 5,00 s.")
        else:
            if not 0.0 <= values[0] <= 100.0:
                raise ParseError(line_number, "Intenzita zatáčení musí být v rozsahu 0 až 100 %.")
            if not 0.05 <= values[1] <= 5.0:
                raise ParseError(line_number, "Doba musí být v rozsahu 0,05 až 5,00 s.")
        instruction = Instruction(opcode, values, line_number)
        instructions.append(instruction)
        total_duration += instruction.duration
        if len(instructions) > MAX_INSTRUCTIONS:
            raise ParseError(line_number, f"Program může obsahovat nejvýše {MAX_INSTRUCTIONS} instrukcí.")
        if total_duration > MAX_TOTAL_DURATION + 1e-9:
            raise ParseError(line_number, f"Součet dob nesmí překročit {MAX_TOTAL_DURATION:.0f} s.")

    if not instructions:
        raise ParseError(1, "Program musí obsahovat alespoň jeden příkaz.")
    return instructions, warnings

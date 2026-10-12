import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from interpreter import Interpreter
from language import parse_program


class InterpreterTests(unittest.TestCase):
    def test_throttle_persists_and_reverse_turn_remembers_direction(self):
        program, _ = parse_program("PLYN(50)\nDOZADU(0.10)\nVLEVO(50, 0.10)")
        interpreter = Interpreter(program)
        reverse = interpreter.step(0.05)
        self.assertEqual(reverse.source_line, 2)
        self.assertLess(reverse.left, 0)
        interpreter.step(0.05)
        turn = interpreter.step(0.05)
        self.assertEqual(turn.source_line, 3)
        self.assertLess(turn.left, turn.right)

    def test_brake_and_program_end_use_bounded_coast(self):
        program, _ = parse_program("PLYN(60)\nDOPREDU(0.05)\nBRZDA(0.05)")
        interpreter = Interpreter(program, coast_seconds=0.1)
        interpreter.step(0.05)
        brake = interpreter.step(0.05)
        self.assertEqual(brake.left, 0.0)
        interpreter.step(0.05)
        self.assertFalse(interpreter.done)
        final = interpreter.step(0.05)
        self.assertTrue(final.program_finished)
        self.assertEqual(final.left, 0.0)


if __name__ == "__main__":
    unittest.main()

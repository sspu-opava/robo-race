import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from language import ParseError, parse_program


class LanguageTests(unittest.TestCase):
    def test_all_six_commands_and_comments(self):
        program, warnings = parse_program("""# poznámka
PLYN(45) # plyn
DOPREDU(.5)
DOZADU(5.00)
VLEVO(60, 0.8)
VPRAVO(0, 0.05)
BRZDA(1.2)
""")
        self.assertEqual([p.opcode for p in program], ["PLYN", "DOPREDU", "DOZADU", "VLEVO", "VPRAVO", "BRZDA"])
        self.assertEqual(program[3].args, (60.0, 0.8))
        self.assertEqual(program[1].source_line, 3)
        self.assertEqual(warnings, [])

    def test_zero_throttle_warns(self):
        _, warnings = parse_program("PLYN(0)\nDOPREDU(1)")
        self.assertEqual(len(warnings), 1)

    def test_rejects_invalid_syntax_and_ranges(self):
        for source in [
            "VLEVO 60 0.8", "VLEVO(60)", "PLYN(200)", "DOPREDU(-1)",
            "DOPREDU(1,5)", "PYTHON(1)", "DOPREDU(1))", "PLYN(NaN)",
            "PLYN(Infinity)", "DOPREDU(1e2)", "PLYN(50) DOPREDU(1)",
            "Plyn(50)", "VLEVO(30, 5.01)", "BRZDA(0.01)", "",
        ]:
            with self.subTest(source=source), self.assertRaises(ParseError):
                parse_program(source)

    def test_instruction_count_and_total_duration_limits(self):
        with self.assertRaises(ParseError):
            parse_program("\n".join(["PLYN(20)"] * 41))
        parse_program("\n".join(["DOPREDU(5)"] * 6 + ["BRZDA(2)"]))
        with self.assertRaises(ParseError):
            parse_program("\n".join(["DOPREDU(5)"] * 6 + ["BRZDA(2.05)"]))
        with self.assertRaises(ParseError):
            parse_program("PLYN(20)" + " " * 10_000)


if __name__ == "__main__":
    unittest.main()

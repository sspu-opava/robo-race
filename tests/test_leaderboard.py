import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from leaderboard import Leaderboard, clean_nickname


class LeaderboardTests(unittest.TestCase):
    def test_best_result_sorting_and_atomic_json_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaderboard.json"
            board = Leaderboard(path, "track-a")
            board.add_result("Ada", 10.0, 1, 2.0, "PLYN(50)")
            board.add_result("ada", 9.5, 0, 0.0, "PLYN(45)")
            board.add_result("Bob", 9.0, 0, 0.0, "PLYN(40)")
            self.assertEqual([row["nickname"] for row in board.top()], ["Bob", "ada"])
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["competition_config_id"], "track-a")
            self.assertEqual(saved["entries"][0]["source"], "PLYN(45)")
            self.assertEqual(len(saved["entries"][0]["official_runs"]), 2)
            self.assertTrue(path.with_suffix(".json.bak").exists())

    def test_corrupt_file_is_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaderboard.json"
            path.write_text("not-json", encoding="utf-8")
            path.with_suffix(".json.bak").write_text(json.dumps({"entries": [{"nickname": "Ok"}]}), encoding="utf-8")
            board = Leaderboard(path, "track")
            self.assertEqual(board.top(), [])
            self.assertIn("poškozený", board.warning)

    def test_nickname_is_bounded_and_plain_text(self):
        self.assertEqual(clean_nickname("  A\nB <b>  "), "AB <b>")
        self.assertEqual(len(clean_nickname("x" * 100)), 20)

    def test_course_configurations_do_not_mix(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaderboard.json"
            Leaderboard(path, "track-a").add_result("Ada", 10.0, 0, 0.0, "PLYN(40)")
            other = Leaderboard(path, "track-b")
            self.assertEqual(other.top(), [])
            self.assertIn("jiné konfiguraci", other.warning)


if __name__ == "__main__":
    unittest.main()

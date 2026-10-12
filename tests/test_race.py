import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from race import Gate, RouteTracker, crossing, distance_to_segment


class RaceTests(unittest.TestCase):
    def test_finite_gate_and_direction(self):
        gate = Gate(0, 0, 1, 0, 0.5, "1")
        self.assertTrue(crossing((-1, 0.2), (1, 0.2), gate).in_bounds)
        self.assertFalse(crossing((-1, 0.8), (1, 0.8), gate).in_bounds)
        self.assertTrue(crossing((1, 0), (-1, 0), gate).reverse)

    def test_route_requires_order_and_finishes(self):
        first = Gate(0, 0, 1, 0, 1, "1")
        second = Gate(2, 0, 1, 0, 1, "2")
        finish = Gate(3, 0, 1, 0, 1, "CÍL")
        tracker = RouteTracker([first, second], finish)
        self.assertIsNotNone(tracker.update((1, 0), (2.5, 0)))

        tracker = RouteTracker([first, second], finish)
        self.assertIsNone(tracker.update((-1, 0), (1, 0)))
        self.assertEqual(tracker.next_checkpoint, 1)
        self.assertIsNone(tracker.update((1, 0), (2.5, 0)))
        self.assertEqual(tracker.next_checkpoint, 2)
        self.assertIsNone(tracker.update((2.5, 0), (3.5, 0)))
        self.assertTrue(tracker.finished)

    def test_segment_distance(self):
        self.assertAlmostEqual(distance_to_segment((1, 2), (0, 0), (2, 0)), 2)
        self.assertAlmostEqual(distance_to_segment((3, 0), (0, 0), (2, 0)), 1)


if __name__ == "__main__":
    unittest.main()

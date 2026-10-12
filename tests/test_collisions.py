import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from collisions import ConePenaltyLedger, car_cone_overlap


class CollisionTests(unittest.TestCase):
    def test_actual_box_or_wheel_overlap_and_near_miss(self):
        car = (0.0, 0.0, 0.16)
        orientation = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        self.assertTrue(car_cone_overlap(car, orientation, (0.34, 0.0, 0.13)))
        self.assertTrue(car_cone_overlap(car, orientation, (0.0, 0.32, 0.13)))
        self.assertFalse(car_cone_overlap(car, orientation, (0.60, 0.0, 0.13)))
        self.assertFalse(car_cone_overlap(car, orientation, (0.0, 0.0, 1.0)))

    def test_unique_cone_penalty_is_added_once(self):
        ledger = ConePenaltyLedger(("CONE_1", "CONE_2"))
        self.assertTrue(ledger.contact("CONE_1"))
        self.assertFalse(ledger.contact("CONE_1"))
        self.assertFalse(ledger.contact("OTHER"))
        self.assertEqual(ledger.seconds, 2.0)
        ledger.contact("CONE_2")
        self.assertEqual(ledger.seconds, 4.0)
        ledger.reset()
        self.assertEqual(ledger.seconds, 0.0)


if __name__ == "__main__":
    unittest.main()

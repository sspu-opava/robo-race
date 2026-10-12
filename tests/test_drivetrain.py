import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from drivetrain import RateLimitedDrive, wheel_targets


class DrivetrainTests(unittest.TestCase):
    def test_straight_and_turn_signs_forward_and_reverse(self):
        self.assertEqual(wheel_targets(50, direction=1), (7.0, 7.0))
        left, right = wheel_targets(50, 80, direction=1, turn="left")
        self.assertLess(left, right)
        left_back, right_back = wheel_targets(50, 80, direction=-1, turn="left")
        self.assertLess(left_back, right_back)
        self.assertTrue(all(value <= 0 for value in (left_back, right_back)))
        left_right, right_right = wheel_targets(50, 80, direction=-1, turn="right")
        self.assertGreater(left_right, right_right)

    def test_normalization_never_exceeds_limit(self):
        left, right = wheel_targets(100, 100, turn="left", max_speed=14, max_difference=2.0)
        self.assertAlmostEqual(max(abs(left), abs(right)), 14.0)
        self.assertLess(left, 0)
        self.assertGreater(right, 0)

    def test_acceleration_ramp_is_limited_and_brake_is_faster(self):
        drive = RateLimitedDrive()
        left, right = drive.step(10, 10, 0.1)
        self.assertAlmostEqual(left, 2.4)
        self.assertAlmostEqual(right, 2.4)
        brake_left, _ = drive.step(0, 0, 0.1, braking=True)
        self.assertAlmostEqual(brake_left, 0.0)


if __name__ == "__main__":
    unittest.main()

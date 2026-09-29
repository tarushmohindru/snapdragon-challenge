"""Regression for the control's discovered priority-versus-time bug."""
import unittest
from correct_hybrid import corrected_selection


class HybridCorrectionTests(unittest.TestCase):
    def test_late_changes_are_not_replaced_by_early_timestamps(self):
        changes = [0.] * 240
        for i in range(180, 188):
            changes[i] = 1. - (i - 180) / 100
        result = corrected_selection('hybrid', changes, 16)
        self.assertEqual(len(result), 16)
        self.assertTrue(set(range(180, 188)).issubset(result))
        self.assertNotIn(1, result)

    def test_coarse_anchor_duplicate_does_not_reduce_budget(self):
        changes = [0.] * 240
        changes[0] = 1.
        self.assertEqual(len(set(corrected_selection('hybrid', changes, 16))), 16)


if __name__ == '__main__':
    unittest.main()

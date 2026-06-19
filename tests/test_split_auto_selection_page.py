# coding: utf-8
"""Tests for UI-neutral formatting helpers used by Split auto-selection."""

import unittest

from pages.page_split_auto_selection import (
    _candidate_rows,
    _time_status_label,
)
from translations import get_translator


class SplitAutoSelectionPageTest(unittest.TestCase):
    def setUp(self):
        self.t = get_translator("en")

    def test_candidate_rows_use_public_pair_label(self):
        rows = _candidate_rows(
            [
                {
                    "high_plus_run": 1,
                    "low_plus_run": 2,
                    "high_minus_run": 3,
                    "low_minus_run": 4,
                    "F0_mean": 100.0,
                    "F2_mean": 0.004,
                    "energy": 1.5,
                    "F0_plus": 99.0,
                    "F0_minus": 101.0,
                    "F2_plus": 0.0039,
                    "F2_minus": 0.0041,
                }
            ],
            "energy",
            self.t,
        )

        self.assertEqual(
            rows[0][self.t("split_pair")],
            "[+]: Run 1 / Run 2 | [-]: Run 3 / Run 4",
        )
        self.assertEqual(rows[0]["F0"], 100.0)
        self.assertNotIn(self.t("split_auto_target_score"), rows[0])

    def test_target_candidate_rows_include_score(self):
        rows = _candidate_rows(
            [
                {
                    "high_plus_run": 1,
                    "low_plus_run": 2,
                    "high_minus_run": 3,
                    "low_minus_run": 4,
                    "target_score": 0.25,
                }
            ],
            "target",
            self.t,
        )

        self.assertEqual(rows[0][self.t("split_auto_target_score")], 0.25)

    def test_time_status_labels_cover_three_states(self):
        self.assertEqual(
            _time_status_label(True, self.t),
            self.t("split_auto_time_status_passed"),
        )
        self.assertEqual(
            _time_status_label(False, self.t),
            self.t("split_auto_time_status_failed"),
        )
        self.assertEqual(
            _time_status_label(None, self.t),
            self.t("split_auto_time_status_inconclusive"),
        )


if __name__ == "__main__":
    unittest.main()

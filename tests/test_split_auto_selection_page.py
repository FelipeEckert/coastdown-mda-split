# coding: utf-8
"""Tests for UI-neutral formatting helpers used by Split auto-selection."""

import unittest
from copy import deepcopy

from pages.page_split_auto_selection import (
    _candidate_run_time_label,
    _candidate_rows,
    _candidate_table,
    _format_candidate_display_value,
    _replace_dialog_state_is_valid,
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

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[2][self.t("split_pair")],
            "[+]: Run 1 / Run 2 | [-]: Run 3 / Run 4",
        )
        self.assertEqual(rows[0]["F0 [N]"], 99.0)
        self.assertEqual(rows[2]["F0 [N]"], 100.0)
        self.assertIsNone(rows[2][self.t("split_auto_target_score")])
        self.assertTrue(rows[2]["_is_average"])
        self.assertEqual(
            list(rows[2])[-2:],
            [self.t("split_energy_with_unit"), "_is_average"],
        )

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

        self.assertEqual(rows[2][self.t("split_auto_target_score")], 0.25)

    def test_candidate_display_value_replaces_visual_missing_values(self):
        for value in (None, float("nan"), "nan", "N/A", "None", ""):
            self.assertEqual(_format_candidate_display_value(value, 2), "-")
        self.assertEqual(_format_candidate_display_value(1.23456, 4), "1.2346")

    def test_candidate_run_time_label_uses_time_fallbacks(self):
        candidate = {
            "high_plus_run": 5,
            "high_plus_delta_t_s": 26.214,
            "low_plus_run": 11,
            "time_components": {"low_plus": {"delta_t_s": 12.3}},
            "high_minus": {"run_id": 7, "delta_t_s": 27.456},
            "low_minus_run": 13,
        }

        self.assertEqual(
            _candidate_run_time_label(candidate, "high_plus"),
            "Run 5 | dt = 26.21 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "low_plus"),
            "Run 11 | dt = 12.30 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "high_minus"),
            "Run 7 | dt = 27.46 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "low_minus"),
            "Run 13 | dt = -",
        )
        self.assertEqual(
            _candidate_run_time_label({}, "high_plus"),
            "Run - | dt = -",
        )

    def test_candidate_table_has_three_rows_and_energy_as_last_column(self):
        candidate = {
            "high_plus_run": 1,
            "low_plus_run": 2,
            "high_minus_run": 3,
            "low_minus_run": 4,
            "F0_plus": 99.0,
            "F0_minus": 101.0,
            "F0_mean": 100.0,
            "F2_plus": 0.0039,
            "F2_minus": 0.0041,
            "F2_mean": 0.004,
            "energy": 1.5,
        }
        original = deepcopy(candidate)

        table = _candidate_table(candidate, "energy", self.t).data

        self.assertEqual(len(table), 3)
        self.assertEqual(table.columns[-1], self.t("split_energy_with_unit"))
        self.assertNotIn(self.t("split_pair"), table.columns)
        self.assertEqual(table.iloc[2][self.t("split_auto_high_run")], "-")
        self.assertEqual(candidate, original)
        self.assertIn(
            "background-color: rgba(209,255,189,0.18)",
            _candidate_table(candidate, "energy", self.t).to_html(),
        )

    def test_fixed_candidate_table_displays_missing_wind_as_dash(self):
        candidate = {
            "high_plus_run": 1, "low_plus_run": 2,
            "high_minus_run": 3, "low_minus_run": 4,
            "temp_plus_used": 20.0, "temp_minus_used": 20.0,
            "press_plus_used": 101.325, "press_minus_used": 101.325,
            "weather_summary": {
                "mode": "fixed", "status": "fixed",
                "temperature_c_mean": 20.0,
                "pressure_kpa_mean": 101.325,
                "wind_speed_mps_max": None,
                "warnings": [],
            },
        }

        table = _candidate_table(candidate, "energy", self.t).data
        self.assertTrue(all(value == "-" for value in table[self.t("split_auto_wind")]))

    def test_replace_dialog_state_requires_live_actionable_request(self):
        pending = {
            "candidates": [{"id": "candidate"}],
            "merge_metadata": None,
            "pool_strategy": "balanced_v2",
        }
        request = {"index": 0}

        self.assertTrue(
            _replace_dialog_state_is_valid(pending, request, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(None, request, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(pending, request, False)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(pending, None, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(
                {**pending, "merge_metadata": {}},
                request,
                True,
            )
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(
                {**pending, "pool_strategy": "legacy"},
                request,
                True,
            )
        )

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

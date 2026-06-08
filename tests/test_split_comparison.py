# coding: utf-8
"""Tests for Split comparison-pair helpers."""

import unittest

from core.split_comparison import (
    add_split_comparison_pair,
    build_split_comparison_pair,
    clear_split_comparison_pairs,
    remove_split_comparison_pair,
)


class SplitComparisonTest(unittest.TestCase):
    def _result(self):
        return {
            "f0_prime": 139.4,
            "f2_prime": 0.646,
            "effective_mass": 1545.0,
            "v1_reference_kmh": 40.0,
            "v2_reference_kmh": 80.0,
            "delta_v1_kmh": 10.0,
            "delta_v2_kmh": 20.0,
            "high_record": {
                "filename": "high.csv",
                "run_id": 1,
                "heading": "+",
                "delta_t_s": 18.72,
                "start_time_str": "18:47:00",
            },
            "low_record": {
                "filename": "low.csv",
                "run_id": 2,
                "heading": "-",
                "delta_t_s": 19.58,
                "start_time_str": "18:55:00",
            },
            "warnings": ["trace warning"],
        }

    def test_build_split_comparison_pair_stores_traceability_and_weather(self):
        pair = build_split_comparison_pair(
            self._result(),
            high_weather={"temp_c": 25.0, "baro_kpa": 101.0, "wind_ms": 1.0},
            low_weather={"temp_c": 27.0, "baro_kpa": 103.0, "wind_ms": 3.0},
            pair_id="pair-1",
        )

        self.assertEqual(pair["id"], "pair-1")
        self.assertEqual(pair["high_file"], "high.csv")
        self.assertEqual(pair["low_file"], "low.csv")
        self.assertEqual(pair["high_run"], 1)
        self.assertEqual(pair["low_run"], 2)
        self.assertEqual(pair["effective_mass"], 1545.0)
        self.assertEqual(pair["temp_c"], 26.0)
        self.assertEqual(pair["baro_kpa"], 102.0)
        self.assertEqual(pair["wind_ms"], 2.0)
        self.assertIsNone(pair["energy"])
        self.assertIn("N/A", pair["energy_status"])
        self.assertEqual(pair["warnings"], ["trace warning"])

    def test_add_remove_and_clear_split_comparison_pairs(self):
        first = build_split_comparison_pair(self._result(), pair_id="pair-1")
        second = build_split_comparison_pair(self._result(), pair_id="pair-2")

        pairs = add_split_comparison_pair([], first)
        pairs = add_split_comparison_pair(pairs, second)
        self.assertEqual([pair["id"] for pair in pairs], ["pair-1", "pair-2"])

        pairs = remove_split_comparison_pair(pairs, "pair-1")
        self.assertEqual([pair["id"] for pair in pairs], ["pair-2"])

        self.assertEqual(clear_split_comparison_pairs(), [])


if __name__ == "__main__":
    unittest.main()

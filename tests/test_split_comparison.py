# coding: utf-8
"""Tests for Split comparison-pair helpers."""

import unittest

from core.split_comparison import (
    add_split_comparison_pair,
    build_split_comparison_pair,
    calculate_complete_split_pair,
    clear_split_comparison_pairs,
    coefficient_variation_percent,
    group_split_records_by_direction,
    remove_split_comparison_pair,
    validate_complete_split_pair_selection,
)
from core.split_corrections import apply_split_pair_correction, fixed_ambient_conditions
from data.split_parser import default_split_interval_config
from pages.page_split_coefficient_calculation import _comparison_rows
from pages.page_split_results import _result_rows


class SplitComparisonTest(unittest.TestCase):
    def _record(self, filename, run_id, heading, delta_t_s):
        return {
            "filename": filename,
            "run_id": run_id,
            "heading": heading,
            "delta_t_s": delta_t_s,
            "delta_v_kmh": 20.0 if filename.startswith("high") else 10.0,
            "start_time_str": f"18:{run_id:02d}:00",
            "subintervals": ["90-85"] if filename.startswith("high") else ["45-40"],
        }

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

    def test_group_split_records_by_direction_uses_explicit_heading_only(self):
        high_plus = self._record("high.csv", 1, "+", 18.72)
        high_minus = self._record("high.csv", 2, "-", 18.90)
        low_plus = self._record("low.csv", 3, "+", 19.58)
        low_minus = self._record("low.csv", 4, "-", 19.70)
        invalid = self._record("high.csv", 5, "ida", 18.80)

        grouped = group_split_records_by_direction(
            [high_plus, high_minus, invalid],
            [low_plus, low_minus],
        )

        self.assertEqual(grouped["high_plus"], [high_plus])
        self.assertEqual(grouped["high_minus"], [high_minus])
        self.assertEqual(grouped["low_plus"], [low_plus])
        self.assertEqual(grouped["low_minus"], [low_minus])
        self.assertEqual(grouped["invalid"], [invalid])

    def test_validate_complete_split_pair_blocks_each_missing_component(self):
        selection = {
            "high_plus": self._record("high.csv", 1, "+", 18.72),
            "low_plus": self._record("low.csv", 2, "+", 19.58),
            "high_minus": self._record("high.csv", 3, "-", 18.90),
            "low_minus": self._record("low.csv", 4, "-", 19.70),
        }

        for missing_key in ("high_plus", "low_plus", "high_minus", "low_minus"):
            with self.subTest(missing_key=missing_key):
                incomplete = dict(selection)
                incomplete[missing_key] = None
                errors = validate_complete_split_pair_selection(incomplete, 1545.0)
                self.assertTrue(errors)
                self.assertIn("is required", errors[0])

    def test_calculate_complete_split_pair_averages_plus_and_minus_results(self):
        result = calculate_complete_split_pair(
            high_plus=self._record("high.csv", 1, "+", 18.72),
            low_plus=self._record("low.csv", 2, "+", 19.58),
            high_minus=self._record("high.csv", 3, "-", 19.00),
            low_minus=self._record("low.csv", 4, "-", 20.00),
            effective_mass=1545.0,
            config=default_split_interval_config(),
        )

        expected_f0 = (
            result["result_plus"]["f0_prime"] + result["result_minus"]["f0_prime"]
        ) / 2.0
        expected_f2 = (
            result["result_plus"]["f2_prime"] + result["result_minus"]["f2_prime"]
        ) / 2.0

        self.assertEqual(result["schema"], "complete_ida_volta_pair_v1")
        self.assertAlmostEqual(result["f0_prime"], expected_f0)
        self.assertAlmostEqual(result["f2_prime"], expected_f2)
        self.assertEqual(result["high_plus"]["heading"], "+")
        self.assertEqual(result["low_minus"]["heading"], "-")

    def test_build_split_comparison_pair_stores_complete_pair_components(self):
        result = calculate_complete_split_pair(
            high_plus=self._record("high.csv", 1, "+", 18.72),
            low_plus=self._record("low.csv", 2, "+", 19.58),
            high_minus=self._record("high.csv", 3, "-", 19.00),
            low_minus=self._record("low.csv", 4, "-", 20.00),
            effective_mass=1545.0,
            config=default_split_interval_config(),
        )
        result = apply_split_pair_correction(
            result,
            fixed_ambient_conditions(20.0, 101.325),
        )

        pair = build_split_comparison_pair(
            result,
            weather_sync={
                "high_plus": {"matched": True, "temperature": 24.0, "pressure": 101.0, "wind_speed": 1.0},
                "low_plus": {"matched": True, "temperature": 26.0, "pressure": 102.0, "wind_speed": 2.0},
                "high_minus": {"matched": True, "temperature": 28.0, "pressure": 103.0, "wind_speed": 3.0},
                "low_minus": {"matched": True, "temperature": 30.0, "pressure": 104.0, "wind_speed": 4.0},
            },
            pair_id="pair-complete",
        )

        self.assertEqual(pair["id"], "pair-complete")
        self.assertEqual(pair["high_plus_run"], 1)
        self.assertEqual(pair["low_plus_run"], 2)
        self.assertEqual(pair["high_minus_run"], 3)
        self.assertEqual(pair["low_minus_run"], 4)
        self.assertEqual(pair["temp_c"], 27.0)
        self.assertEqual(pair["baro_kpa"], 102.5)
        self.assertEqual(pair["wind_ms"], 2.5)
        self.assertEqual(pair["weather_match_count"], 4)
        self.assertEqual(len(pair["weather_sync"]), 4)
        self.assertTrue(pair["correction_available"])
        self.assertEqual(pair["ambient_source"], "manual_fixed")
        self.assertAlmostEqual(pair["F0"], result["corrected_pair_mean"]["F0"])
        self.assertAlmostEqual(pair["F2"], result["corrected_pair_mean"]["F2"])
        self.assertAlmostEqual(pair["F0_mean"], result["F0_mean"])
        self.assertAlmostEqual(pair["F2_mean"], result["F2_mean"])
        self.assertAlmostEqual(
            pair["f0_prime_mean"],
            result["f0_prime_mean"],
        )
        self.assertAlmostEqual(
            pair["f2_prime_mean"],
            result["f2_prime_mean"],
        )
        self.assertAlmostEqual(pair["f0_prime"], result["result_pair_mean"]["f0_prime"])
        self.assertIsNotNone(pair["cv_F0_percent"])
        self.assertIsNotNone(pair["cv_F2_percent"])
        self.assertEqual(pair["F0_unit"], "N")
        self.assertEqual(pair["F2_unit"], "N/(km/h)^2")
        self.assertEqual(pair["wind_plus_ms"], 1.5)
        self.assertEqual(pair["wind_minus_ms"], 3.5)
        self.assertIsNone(pair["energy"])
        self.assertIn("explicit corrected F0/F2", pair["energy_status"])

        translate = lambda key, **kwargs: key.format(**kwargs) if kwargs else key
        comparison_row = _comparison_rows([pair], translate)[0]
        result_row = _result_rows([result])[0]
        self.assertEqual(comparison_row["F0 avg (N)"], pair["F0_mean"])
        self.assertEqual(
            comparison_row["F2 avg (N/(km/h)^2)"],
            pair["F2_mean"],
        )
        self.assertEqual(comparison_row["Energy (MJ/km)"], "N/A")
        self.assertEqual(result_row["F0 (N)"], result["F0_mean"])
        self.assertEqual(
            result_row["F2 (N/(km/h)^2)"],
            result["F2_mean"],
        )

    def test_coefficient_variation_uses_ida_and_volta_results(self):
        cv = coefficient_variation_percent(100.0, 110.0)

        self.assertAlmostEqual(cv, 6.734350297014738)
        self.assertIsNone(coefficient_variation_percent(None, 110.0))
        self.assertIsNone(coefficient_variation_percent(-10.0, 10.0))

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

# coding: utf-8
"""Tests for the pure Split selected-pair deviation diagnostics."""

import inspect
import statistics
import unittest

from core.split_deviation_analysis import analyze_split_selected_deviations


def _pair(pair_id, f0, f2, offset=0.0, temperature=25.0, wind=1.0, pressure=101.0):
    return {
        "id": pair_id,
        "selected": True,
        "F0_mean": f0,
        "F2_mean": f2,
        "energy": 0.2 + offset,
        "high_plus_delta_t_s": 20.0 + offset,
        "high_minus_delta_t_s": 20.4 + offset,
        "low_plus_delta_t_s": 10.0 + offset,
        "low_minus_delta_t_s": 10.3 + offset,
        "ambient_by_component": {
            "high_plus": {
                "temperature_c": temperature,
                "pressure_kpa": pressure,
                "wind_speed_ms": wind,
            }
        },
    }


class SplitDeviationAnalysisTest(unittest.TestCase):
    def test_empty_selection_is_insufficient(self):
        result = analyze_split_selected_deviations([])
        self.assertEqual(result["pair_count"], 0)
        self.assertEqual(result["status"], "insufficient_data")

    def test_unselected_pairs_are_not_analyzed(self):
        pair = _pair("ignored", 100.0, 0.004)
        pair["selected"] = False
        self.assertEqual(analyze_split_selected_deviations([pair])["pair_count"], 0)

    def test_single_pair_cvs_are_not_evaluable(self):
        result = analyze_split_selected_deviations([_pair("a", 100.0, 0.004)])
        summary = result["coefficient_summary"]
        self.assertIsNone(summary["cv_f0_pct"])
        self.assertIsNone(summary["cv_f2_pct"])
        self.assertEqual(summary["status"], "insufficient_data")
        self.assertEqual(result["leave_one_out"], [])

    def test_multiple_pairs_use_sample_cv_and_relative_deviation(self):
        pairs = [_pair("a", 100.0, 0.004), _pair("b", 110.0, 0.006, 0.1)]
        result = analyze_split_selected_deviations(pairs)
        summary = result["coefficient_summary"]
        self.assertAlmostEqual(summary["cv_f0_pct"], statistics.stdev([100.0, 110.0]) / 105.0 * 100)
        self.assertAlmostEqual(summary["cv_f2_pct"], statistics.stdev([0.004, 0.006]) / 0.005 * 100)
        self.assertAlmostEqual(result["pair_deviations"][0]["f0_deviation_pct"], -5.0 / 105.0 * 100)

    def test_largest_coefficient_deviations_are_identified(self):
        result = analyze_split_selected_deviations([
            _pair("a", 80.0, 0.004),
            _pair("b", 100.0, 0.005, 0.1),
            _pair("c", 110.0, 0.008, 0.2),
        ])
        f0_largest = [row["pair_id"] for row in result["pair_deviations"] if row["largest_f0_deviation"]]
        f2_largest = [row["pair_id"] for row in result["pair_deviations"] if row["largest_f2_deviation"]]
        self.assertEqual(f0_largest, ["a"])
        self.assertEqual(f2_largest, ["c"])

    def test_times_are_grouped_and_opposite_means_are_compared(self):
        result = analyze_split_selected_deviations([
            _pair("a", 100.0, 0.004),
            _pair("b", 101.0, 0.0041, 0.1),
        ])
        times = result["time_summary"]
        self.assertEqual(times["groups"]["high_plus"]["count"], 2)
        self.assertAlmostEqual(times["groups"]["high_plus"]["mean"], 20.05)
        self.assertAlmostEqual(times["groups"]["high_plus"]["stdev"], statistics.stdev([20.0, 20.1]))
        self.assertIsNotNone(times["groups"]["high_plus"]["cv_pct"])
        expected = abs(20.05 - 20.45) / ((20.05 + 20.45) / 2) * 100
        self.assertAlmostEqual(times["opposite_direction"]["high"]["diff_pct"], expected)

    def test_weather_flags_wind_and_temperature_but_not_pressure(self):
        result = analyze_split_selected_deviations([
            _pair("hot", 100.0, 0.004, temperature=36.0, wind=3.1, pressure=150.0)
        ])
        weather = result["weather_summary"]["pairs"][0]
        self.assertEqual(weather["status"], "failed")
        self.assertTrue(any("vento" in alert.lower() for alert in weather["alerts"]))
        self.assertTrue(any("temperatura" in alert.lower() for alert in weather["alerts"]))
        self.assertFalse(any("Press" in alert for alert in weather["alerts"]))

    def test_leave_one_out_recalculates_cvs_and_marks_best_improvement(self):
        result = analyze_split_selected_deviations([
            _pair("a", 100.0, 0.004),
            _pair("b", 101.0, 0.0041, 0.1),
            _pair("outlier", 140.0, 0.009, 0.2),
        ])
        rows = result["leave_one_out"]
        self.assertEqual(len(rows), 3)
        outlier = next(row for row in rows if row["pair_id"] == "outlier")
        self.assertLess(outlier["new_cv_f0_pct"], outlier["current_cv_f0_pct"])
        self.assertTrue(outlier["largest_f0_improvement"])
        self.assertTrue(outlier["largest_f2_improvement"])

    def test_module_does_not_import_streamlit(self):
        import core.split_deviation_analysis as module
        source = inspect.getsource(module).lower()
        self.assertNotIn("import streamlit", source)
        self.assertNotIn("from streamlit", source)
        self.assertFalse(hasattr(module, "st"))


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for pure Split normative time diagnostics."""

import inspect
import statistics
import unittest

from core.split_time_validation import (
    coefficient_of_variation_percent,
    extract_split_candidate_times,
    opposite_mean_difference_percent,
    validate_split_selected_times,
)


def _candidate(
    candidate_id,
    high_plus,
    high_minus,
    low_plus,
    low_minus,
):
    return {
        "id": candidate_id,
        "high_plus_delta_t_s": high_plus,
        "high_minus_delta_t_s": high_minus,
        "low_plus_delta_t_s": low_plus,
        "low_minus_delta_t_s": low_minus,
    }


class SplitTimeValidationTest(unittest.TestCase):
    def test_cv_returns_none_with_less_than_two_values(self):
        self.assertIsNone(coefficient_of_variation_percent([10.0]))
        self.assertIsNone(coefficient_of_variation_percent([]))

    def test_cv_uses_sample_standard_deviation(self):
        values = [10.0, 11.0, 12.0]
        expected = statistics.stdev(values) / statistics.mean(values) * 100.0

        self.assertAlmostEqual(
            coefficient_of_variation_percent(values),
            expected,
        )

    def test_cv_ignores_invalid_values(self):
        self.assertAlmostEqual(
            coefficient_of_variation_percent([10.0, None, float("nan"), 10.2]),
            coefficient_of_variation_percent([10.0, 10.2]),
        )

    def test_opposite_mean_difference_calculates_percent(self):
        self.assertAlmostEqual(
            opposite_mean_difference_percent(10.0, 11.0),
            abs(10.0 - 11.0) / 10.5 * 100.0,
        )

    def test_opposite_mean_difference_returns_none_for_invalid_mean(self):
        self.assertIsNone(opposite_mean_difference_percent(None, 11.0))
        self.assertIsNone(opposite_mean_difference_percent(float("nan"), 11.0))

    def test_extract_times_separates_components(self):
        times = extract_split_candidate_times(
            [
                _candidate("a", 20.0, 20.5, 10.0, 10.5),
                _candidate("b", 20.1, 20.6, 10.1, 10.6),
            ]
        )

        self.assertEqual(times["high_plus"], [20.0, 20.1])
        self.assertEqual(times["high_minus"], [20.5, 20.6])
        self.assertEqual(times["low_plus"], [10.0, 10.1])
        self.assertEqual(times["low_minus"], [10.5, 10.6])

    def test_extract_times_can_use_nested_component_records(self):
        times = extract_split_candidate_times(
            [
                {
                    "high_plus": {"delta_t_s": 20.0},
                    "high_minus": {"delta_t_s": 20.5},
                    "low_plus": {"delta_t_s": 10.0},
                    "low_minus": {"delta_t_s": 10.5},
                }
            ]
        )

        self.assertEqual(times["high_plus"], [20.0])
        self.assertEqual(times["low_minus"], [10.5])

    def test_validation_passes_when_cv_and_opposite_limits_pass(self):
        result = validate_split_selected_times(
            [
                _candidate("a", 20.0, 20.8, 10.0, 10.7),
                _candidate("b", 20.1, 20.9, 10.1, 10.8),
                _candidate("c", 20.2, 21.0, 10.2, 10.9),
            ]
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["cv_limit_pct"], 2.5)
        self.assertEqual(result["opposite_mean_limit_pct"], 10.0)
        self.assertTrue(all(
            result["groups"][component]["passed"]
            for component in ("high_plus", "high_minus", "low_plus", "low_minus")
        ))
        self.assertTrue(all(
            result["opposite_direction"][interval]["passed"]
            for interval in ("high", "low")
        ))

    def test_validation_fails_when_cv_exceeds_limit(self):
        result = validate_split_selected_times(
            [
                _candidate("a", 20.0, 20.0, 10.0, 10.0),
                _candidate("b", 23.0, 20.1, 10.1, 10.1),
            ]
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["groups"]["high_plus"]["passed"])

    def test_validation_fails_when_high_opposite_difference_exceeds_limit(self):
        result = validate_split_selected_times(
            [
                _candidate("a", 20.0, 25.0, 10.0, 10.1),
                _candidate("b", 20.1, 25.1, 10.1, 10.2),
            ]
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["opposite_direction"]["high"]["passed"])

    def test_validation_fails_when_low_opposite_difference_exceeds_limit(self):
        result = validate_split_selected_times(
            [
                _candidate("a", 20.0, 20.1, 10.0, 12.0),
                _candidate("b", 20.1, 20.2, 10.1, 12.1),
            ]
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["opposite_direction"]["low"]["passed"])

    def test_validation_returns_none_when_sample_is_insufficient(self):
        result = validate_split_selected_times(
            [_candidate("a", 20.0, 20.5, 10.0, 10.5)]
        )

        self.assertIsNone(result["passed"])
        self.assertIsNone(result["groups"]["high_plus"]["cv_pct"])
        self.assertIsNone(result["groups"]["high_plus"]["passed"])
        self.assertNotEqual(result["passed"], False)
        self.assertTrue(result["warnings"])

    def test_validation_warns_when_times_are_missing(self):
        result = validate_split_selected_times(
            [
                {
                    "id": "missing",
                    "high_plus_delta_t_s": 20.0,
                    "high_minus_delta_t_s": 20.5,
                }
            ]
        )

        self.assertTrue(
            any("low_plus" in warning for warning in result["warnings"])
        )
        self.assertTrue(
            any("low_minus" in warning for warning in result["warnings"])
        )

    def test_module_does_not_import_streamlit(self):
        import core.split_time_validation as module

        source = inspect.getsource(module)

        self.assertNotIn("import streamlit", source.lower())
        self.assertNotIn("from streamlit", source.lower())
        self.assertFalse(hasattr(module, "st"))


if __name__ == "__main__":
    unittest.main()

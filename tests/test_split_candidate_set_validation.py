# coding: utf-8
"""Tests for normative time-only automatic Split set validation."""

import unittest

from core.split_candidate_set_validation import (
    evaluate_split_constraint_satisfaction,
    normalize_split_time_constraints,
    validate_split_candidate_set,
)


def _candidate(identifier, *, f0, f2, high_plus=20.0, high_minus=20.2):
    return {
        "id": identifier,
        "F0_mean": f0,
        "F2_mean": f2,
        "high_plus_delta_t_s": high_plus,
        "high_minus_delta_t_s": high_minus,
        "low_plus_delta_t_s": 10.0,
        "low_minus_delta_t_s": 10.2,
    }


class SplitCandidateSetValidationTest(unittest.TestCase):
    def test_missing_coefficients_are_reported_but_not_normative(self):
        result = validate_split_candidate_set(
            [
                _candidate("a", f0=None, f2=None),
                _candidate("b", f0=None, f2=None),
            ]
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["coefficient_status"], "insufficient_data")
        self.assertTrue(result["coefficient_diagnostic_only"])
        self.assertEqual(result["failed_checks"], [])
        self.assertIn(
            "One or more candidates are missing corrected F0_mean/F0.",
            result["coefficient_warnings"],
        )
        self.assertIn(
            "One or more candidates are missing corrected F2_mean/F2.",
            result["coefficient_warnings"],
        )
        self.assertTrue(
            evaluate_split_constraint_satisfaction(
                result,
                {
                    "time_cv": True,
                    "opposite_time_difference": True,
                    "coefficient_cv": True,
                },
            )
        )

    def test_high_coefficient_cv_is_diagnostic_when_times_pass(self):
        result = validate_split_candidate_set(
            [
                _candidate("a", f0=100.0, f2=0.004),
                _candidate("b", f0=150.0, f2=0.008),
            ]
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["time_status"], "approved")
        self.assertEqual(result["coefficient_status"], "failed")
        self.assertTrue(result["coefficient_diagnostic_only"])
        self.assertEqual(result["failed_checks"], [])

    def test_time_group_cv_remains_normative_failure(self):
        result = validate_split_candidate_set(
            [
                _candidate("a", f0=100.0, f2=0.004, high_plus=20.0),
                _candidate("b", f0=100.1, f2=0.00401, high_plus=22.0),
            ]
        )

        self.assertFalse(result["passed"])
        self.assertIn("time.group.high_plus", result["failed_checks"])

    def test_legacy_coefficient_constraint_is_ignored(self):
        validation = validate_split_candidate_set(
            [
                _candidate("a", f0=100.0, f2=0.004),
                _candidate("b", f0=150.0, f2=0.008),
            ]
        )
        legacy = {
            "coefficient_cv": True,
            "time_cv": True,
            "opposite_time_difference": True,
        }

        self.assertEqual(
            normalize_split_time_constraints(legacy),
            {"time_cv": True, "opposite_time_difference": True},
        )
        self.assertTrue(
            evaluate_split_constraint_satisfaction(validation, legacy)
        )

if __name__ == "__main__":
    unittest.main()

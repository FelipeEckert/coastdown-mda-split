# coding: utf-8
"""Tests for automatic Split pair candidate helpers."""

import inspect
import unittest

from core.split_comparison import (
    build_split_comparison_pair,
    calculate_complete_split_pair,
)
from core.split_corrections import (
    apply_split_pair_correction,
    fixed_ambient_conditions,
)
from core.split_pair_candidate import (
    MISSING_IDENTITY_VALUE,
    build_algorithm_split_pair_candidate,
    build_split_run_usage,
    split_candidate_signature,
)


class SplitPairCandidateTest(unittest.TestCase):
    def _record(self, filename, run_id, heading, delta_t_s, source_role):
        return {
            "filename": filename,
            "run_id": run_id,
            "heading": heading,
            "source_role": source_role,
            "delta_t_s": delta_t_s,
            "delta_v_kmh": 20.0 if source_role == "high" else 10.0,
            "start_time_str": f"18:{int(run_id):02d}:00",
            "subintervals": ["90-85"] if source_role == "high" else ["45-40"],
            "source_columns": ["col"],
            "content_sha256": f"hash-{filename}",
            "warnings": [],
        }

    def _runs(self):
        return {
            "high_plus_run": self._record("high.csv", 5, "+", 18.72, "high"),
            "low_plus_run": self._record("low.csv", 5, "+", 19.58, "low"),
            "high_minus_run": self._record("high.csv", 6, "-", 19.00, "high"),
            "low_minus_run": self._record("low.csv", 6, "-", 20.00, "low"),
        }

    def _context(self):
        return {
            "temperature_c": 20.0,
            "pressure_kpa": 101.325,
        }

    def test_run_usage_distinguishes_high_and_low_with_same_run_id(self):
        usage = build_split_run_usage(**self._runs())

        self.assertEqual(usage[0][0], "high")
        self.assertEqual(usage[1][0], "low")
        self.assertEqual(usage[0][2], usage[1][2])
        self.assertNotEqual(usage[0], usage[1])

    def test_run_usage_distinguishes_plus_and_minus_direction(self):
        usage = build_split_run_usage(**self._runs())

        self.assertEqual(usage[0][1], "+")
        self.assertEqual(usage[2][1], "-")
        self.assertNotEqual(usage[0], usage[2])

    def test_candidate_signature_is_stable_for_same_candidate(self):
        candidate = {
            "run_usage": build_split_run_usage(**self._runs()),
        }

        self.assertEqual(
            split_candidate_signature(candidate),
            split_candidate_signature(dict(candidate)),
        )

    def test_candidate_signature_changes_when_one_run_changes(self):
        first_runs = self._runs()
        second_runs = self._runs()
        second_runs["low_minus_run"] = self._record(
            "low.csv",
            7,
            "-",
            20.20,
            "low",
        )

        self.assertNotEqual(
            build_split_run_usage(**first_runs),
            build_split_run_usage(**second_runs),
        )

    def test_algorithm_candidate_forces_not_selected_and_algorithm_source(self):
        candidate = build_algorithm_split_pair_candidate(
            **self._runs(),
            vehicle_data={"effective_mass": 1545.0},
            correction_context=self._context(),
        )

        self.assertFalse(candidate["selected"])
        self.assertEqual(candidate["selection_source"], "algorithm")
        self.assertEqual(candidate["candidate_signature"], candidate["run_usage"])
        self.assertEqual(
            candidate["pair_label"],
            "[+]: Run 5 / Run 5 | [-]: Run 6 / Run 6",
        )

    def test_candidate_reuses_manual_calculation_path(self):
        runs = self._runs()
        ambient_conditions = fixed_ambient_conditions(20.0, 101.325)
        manual_result = calculate_complete_split_pair(
            high_plus=runs["high_plus_run"],
            low_plus=runs["low_plus_run"],
            high_minus=runs["high_minus_run"],
            low_minus=runs["low_minus_run"],
            effective_mass=1545.0,
            config={
                "step_kmh": 5.0,
                "high": {"start": 90.0, "end": 70.0, "reference": 80.0},
                "low": {"start": 45.0, "end": 35.0, "reference": 40.0},
            },
        )
        manual_result = apply_split_pair_correction(
            manual_result,
            ambient_conditions,
        )
        manual_pair = build_split_comparison_pair(
            manual_result,
            selection_source="algorithm",
        )

        candidate = build_algorithm_split_pair_candidate(
            **runs,
            vehicle_data={"effective_mass": 1545.0},
            correction_context={"ambient_conditions": ambient_conditions},
        )

        self.assertAlmostEqual(candidate["f0_prime_mean"], manual_pair["f0_prime_mean"])
        self.assertAlmostEqual(candidate["f2_prime_mean"], manual_pair["f2_prime_mean"])
        self.assertAlmostEqual(candidate["F0_mean"], manual_pair["F0_mean"])
        self.assertAlmostEqual(candidate["F2_mean"], manual_pair["F2_mean"])
        self.assertAlmostEqual(candidate["energy"], manual_pair["energy"])

    def test_module_does_not_depend_on_streamlit(self):
        import core.split_pair_candidate as module

        source = inspect.getsource(module)

        self.assertNotIn("import streamlit", source.lower())
        self.assertNotIn("from streamlit", source.lower())
        self.assertFalse(hasattr(module, "st"))

    def test_missing_identity_values_are_controlled(self):
        runs = self._runs()
        runs["low_plus_run"] = {
            "heading": "+",
            "delta_t_s": 19.58,
            "source_role": "low",
        }

        usage = build_split_run_usage(**runs)

        self.assertEqual(usage[1][2], MISSING_IDENTITY_VALUE)
        self.assertEqual(usage[1][3], MISSING_IDENTITY_VALUE)


if __name__ == "__main__":
    unittest.main()

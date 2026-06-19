# coding: utf-8
"""Tests for exact automatic Split selection orchestration."""

import inspect
import unittest

from core.split_auto_selection import run_split_auto_selection_exact


def _run(role, heading, run_id, delta_t_s=10.0):
    return {
        "interval_name": role,
        "source_role": role,
        "heading": heading,
        "run_id": run_id,
        "filename": f"{role}.csv",
        "delta_t_s": delta_t_s,
    }


def _parsed():
    return {
        "high": [
            _run("high", "+", 1, 20.0),
            _run("high", "+", 2, 20.1),
            _run("high", "-", 3, 20.5),
            _run("high", "-", 4, 20.6),
        ],
        "low": [
            _run("low", "+", 5, 10.0),
            _run("low", "+", 6, 10.1),
            _run("low", "-", 7, 10.5),
            _run("low", "-", 8, 10.6),
        ],
    }


def _usage(kind, direction, run_id):
    return (kind, direction, run_id, f"{kind}.csv", kind, f"hash-{kind}-{run_id}")


def _fake_builder(
    *,
    high_plus_run,
    low_plus_run,
    high_minus_run,
    low_minus_run,
    vehicle_data,
    correction_context=None,
):
    high_plus = high_plus_run["run_id"]
    low_plus = low_plus_run["run_id"]
    high_minus = high_minus_run["run_id"]
    low_minus = low_minus_run["run_id"]
    identifier = f"{high_plus}/{low_plus}/{high_minus}/{low_minus}"
    energy = high_plus + low_plus + high_minus + low_minus
    return {
        "id": identifier,
        "energy": float(energy),
        "F0_mean": 100.0 + high_plus,
        "F2_mean": 0.004 + low_plus / 100000.0,
        "run_usage": (
            _usage("high", "+", high_plus),
            _usage("low", "+", low_plus),
            _usage("high", "-", high_minus),
            _usage("low", "-", low_minus),
        ),
        "high_plus_delta_t_s": high_plus_run["delta_t_s"],
        "low_plus_delta_t_s": low_plus_run["delta_t_s"],
        "high_minus_delta_t_s": high_minus_run["delta_t_s"],
        "low_minus_delta_t_s": low_minus_run["delta_t_s"],
    }


class SplitAutoSelectionTest(unittest.TestCase):
    def test_invalid_algorithm_raises_value_error(self):
        with self.assertRaises(ValueError):
            run_split_auto_selection_exact(
                _parsed(),
                vehicle_data={"effective_mass": 1.0},
                algorithm="bad",
                k=1,
                candidate_builder=_fake_builder,
            )

    def test_non_positive_k_raises_value_error(self):
        with self.assertRaises(ValueError):
            run_split_auto_selection_exact(
                _parsed(),
                vehicle_data={"effective_mass": 1.0},
                algorithm="energy",
                k=0,
                candidate_builder=_fake_builder,
            )

    def test_energy_mode_generates_ranks_and_returns_top_k(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=2,
            avoid_repeated_runs=False,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]["id"], "1/5/3/7")
        self.assertEqual(metadata["generated_count"], 16)
        self.assertEqual(metadata["ranked_count"], 16)
        self.assertEqual(metadata["selected_count"], 2)

    def test_target_mode_requires_targets(self):
        with self.assertRaises(ValueError):
            run_split_auto_selection_exact(
                _parsed(),
                vehicle_data={"effective_mass": 1.0},
                algorithm="target",
                k=1,
                candidate_builder=_fake_builder,
            )

    def test_target_mode_returns_target_scores(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="target",
            k=1,
            target_f0=102.0,
            target_f2=0.00405,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(selected), 1)
        self.assertIn("target_score", selected[0])
        self.assertEqual(metadata["algorithm"], "target")

    def test_candidates_are_not_selected_and_have_algorithm_origin(self):
        selected, _ = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=1,
            candidate_builder=_fake_builder,
        )

        self.assertFalse(selected[0]["selected"])
        self.assertEqual(selected[0]["selection_source"], "algorithm")
        self.assertEqual(selected[0]["algorithm_source"], "energy")

    def test_target_candidates_have_target_origin(self):
        selected, _ = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="target",
            k=1,
            target_f0=101.0,
            target_f2=0.00405,
            candidate_builder=_fake_builder,
        )

        self.assertFalse(selected[0]["selected"])
        self.assertEqual(selected[0]["selection_source"], "algorithm")
        self.assertEqual(selected[0]["algorithm_source"], "target")

    def test_avoid_repeated_runs_blocks_reused_usage(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=3,
            avoid_repeated_runs=True,
            candidate_builder=_fake_builder,
        )

        self.assertLess(len(selected), 3)
        self.assertGreater(metadata["selection"]["skipped_repeated_count"], 0)
        self.assertTrue(metadata["warnings"])

    def test_no_generated_candidates_returns_empty_with_warning(self):
        selected, metadata = run_split_auto_selection_exact(
            {"high": [], "low": []},
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=1,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(selected, [])
        self.assertEqual(metadata["ranked_count"], 0)
        self.assertTrue(metadata["warnings"])

    def test_max_combinations_warning_is_preserved(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=1,
            max_combinations=1,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(selected, [])
        self.assertTrue(
            any("max_combinations" in warning for warning in metadata["warnings"])
        )
        self.assertTrue(
            any(
                "max_combinations" in warning
                for warning in metadata["generation"]["warnings"]
            )
        )

    def test_metadata_contains_generation_selection_and_time_validation(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=2,
            avoid_repeated_runs=False,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(selected), 2)
        self.assertIn("generation", metadata)
        self.assertIn("selection", metadata)
        self.assertIn("time_validation", metadata)
        self.assertEqual(metadata["time_validation"]["groups"]["high_plus"]["count"], 2)

    def test_time_diagnostic_is_included(self):
        _, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=1,
            candidate_builder=_fake_builder,
        )

        self.assertIsNotNone(metadata["time_validation"])
        self.assertIn("passed", metadata["time_validation"])

    def test_module_does_not_import_streamlit(self):
        import core.split_auto_selection as module

        source = inspect.getsource(module)

        self.assertNotIn("import streamlit", source.lower())
        self.assertNotIn("from streamlit", source.lower())
        self.assertFalse(hasattr(module, "st"))


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for exact automatic Split selection orchestration."""

import inspect
import unittest
from copy import deepcopy

from core.split_auto_selection import (
    find_replacement_candidate,
    replace_pending_candidate,
    run_split_auto_selection_exact,
)
from core.split_pair_candidate import split_candidate_signature


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


def _candidate(identifier, *run_ids):
    return {
        "id": identifier,
        "run_usage": tuple(
            _usage("high", "+", run_id) for run_id in run_ids
        ),
        "selected": False,
    }


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
    def test_find_replacement_previews_without_mutating_inputs(self):
        current = [_candidate("old", 1, 9), _candidate("remaining", 2)]
        replacement = _candidate("replacement", 1, 3)
        pool = current + [replacement]
        original_current = deepcopy(current)
        original_pool = deepcopy(pool)

        preview, metadata = find_replacement_candidate(current, pool, 0)

        self.assertEqual(preview["id"], "replacement")
        self.assertTrue(metadata["found"])
        self.assertEqual(metadata["pool_size"], 3)
        self.assertEqual(metadata["checked_pool_count"], 3)
        self.assertEqual(metadata["skipped_old_candidate_count"], 1)
        self.assertEqual(metadata["skipped_existing_count"], 1)
        self.assertEqual(metadata["skipped_repeated_count"], 0)
        self.assertEqual(current, original_current)
        self.assertEqual(pool, original_pool)

    def test_replace_uses_same_candidate_returned_by_preview(self):
        current = [_candidate("old", 1), _candidate("remaining", 2)]
        pool = current + [_candidate("replacement", 3)]

        preview, _ = find_replacement_candidate(current, pool, 0)
        replaced, metadata = replace_pending_candidate(current, pool, 0)

        self.assertTrue(metadata["replaced"])
        self.assertEqual(
            split_candidate_signature(replaced[0]),
            split_candidate_signature(preview),
        )

    def test_find_replacement_exhaustion_reports_real_filters_without_cv(self):
        current = [_candidate("old", 1), _candidate("remaining", 2)]

        preview, metadata = find_replacement_candidate(current, current, 0)

        self.assertIsNone(preview)
        self.assertFalse(metadata["found"])
        self.assertEqual(metadata["pool_size"], 2)
        self.assertEqual(metadata["checked_pool_count"], 2)
        self.assertEqual(metadata["skipped_old_candidate_count"], 1)
        self.assertEqual(metadata["skipped_existing_count"], 1)
        self.assertNotIn("skipped_cv_count", metadata)
        self.assertFalse(any("cv" in warning.lower() for warning in metadata["warnings"]))

    def test_replace_pending_candidate_uses_next_available_pool_item(self):
        current = [_candidate("a", 1), _candidate("b", 2)]
        pool = current + [_candidate("c", 3)]

        replaced, metadata = replace_pending_candidate(
            current,
            pool,
            0,
            avoid_repeated_runs=True,
        )

        self.assertEqual([item["id"] for item in replaced], ["c", "b"])
        self.assertTrue(metadata["replaced"])
        self.assertEqual(metadata["old_identifier"], "a")
        self.assertEqual(metadata["new_identifier"], "c")
        self.assertEqual(metadata["skipped_old_candidate_count"], 1)
        self.assertEqual(metadata["skipped_existing_count"], 1)

    def test_replacement_accepts_conflict_only_with_removed_candidate(self):
        old = _candidate("old", 1, 9)
        remaining = _candidate("remaining", 2)
        replacement = _candidate("replacement", 1, 3)

        replaced, metadata = replace_pending_candidate(
            [old, remaining],
            [old, replacement],
            0,
            avoid_repeated_runs=True,
        )

        self.assertEqual(len(replaced), 2)
        self.assertEqual(replaced[0]["id"], "replacement")
        self.assertEqual(replaced[1]["id"], "remaining")
        self.assertTrue(metadata["replaced"])
        self.assertEqual(metadata["skipped_repeated_count"], 0)

    def test_replacement_distinguishes_existing_and_remaining_run_conflicts(self):
        old = _candidate("old", 1)
        remaining = _candidate("remaining", 2)
        repeated = _candidate("repeated", 2, 3)
        valid = _candidate("valid", 4)

        replaced, metadata = replace_pending_candidate(
            [old, remaining],
            [old, remaining, repeated, valid],
            0,
            avoid_repeated_runs=True,
        )

        self.assertEqual(replaced[0]["id"], "valid")
        self.assertEqual(metadata["skipped_old_candidate_count"], 1)
        self.assertEqual(metadata["skipped_existing_count"], 1)
        self.assertEqual(metadata["skipped_repeated_count"], 1)

    def test_replacement_finds_valid_candidate_after_visible_k(self):
        current = [_candidate(f"visible-{index}", index) for index in range(1, 6)]
        old = current[2]
        replacement = _candidate("reserve", 3, 99)
        pool = current + [replacement]

        replaced, metadata = replace_pending_candidate(current, pool, 2)

        self.assertEqual(len(replaced), 5)
        self.assertEqual(replaced[2]["id"], "reserve")
        self.assertEqual(metadata["pool_size"], 6)
        self.assertEqual(metadata["checked_pool_count"], 6)
        self.assertEqual(metadata["skipped_old_candidate_count"], 1)
        self.assertEqual(metadata["skipped_existing_count"], 4)

    def test_replace_pending_candidate_skips_repeated_run_usage(self):
        current = [_candidate("a", 1), _candidate("b", 2)]
        pool = [
            _candidate("a", 1),
            _candidate("b", 2),
            _candidate("conflict", 2, 3),
            _candidate("valid", 4),
        ]

        replaced, metadata = replace_pending_candidate(current, pool, 0)

        self.assertEqual(replaced[0]["id"], "valid")
        self.assertEqual(metadata["skipped_repeated_count"], 1)

    def test_replace_pending_candidate_allows_repetition_when_disabled(self):
        current = [_candidate("a", 1), _candidate("b", 2)]
        conflict = _candidate("conflict", 2, 3)

        replaced, metadata = replace_pending_candidate(
            current,
            [conflict],
            0,
            avoid_repeated_runs=False,
        )

        self.assertEqual(replaced[0]["id"], "conflict")
        self.assertTrue(metadata["replaced"])

    def test_replace_pending_candidate_warns_without_valid_replacement(self):
        current = [_candidate("a", 1), _candidate("b", 2)]

        replaced, metadata = replace_pending_candidate(current, current, 0)

        self.assertEqual(replaced, current)
        self.assertFalse(metadata["replaced"])
        self.assertTrue(metadata["warnings"])

    def test_replace_pending_candidate_does_not_mutate_inputs(self):
        current = [_candidate("a", 1), _candidate("b", 2)]
        pool = current + [_candidate("c", 3)]
        original_current = deepcopy(current)
        original_pool = deepcopy(pool)

        replace_pending_candidate(current, pool, 0)

        self.assertEqual(current, original_current)
        self.assertEqual(pool, original_pool)

    def test_replace_pending_candidate_rejects_invalid_index(self):
        with self.assertRaises(IndexError):
            replace_pending_candidate([_candidate("a", 1)], [], 2)
        with self.assertRaises(ValueError):
            replace_pending_candidate([_candidate("a", 1)], [], "0")

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

    def test_energy_replacement_pool_preserves_ranking_and_origin(self):
        _, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=2,
            avoid_repeated_runs=False,
            replacement_pool_size=4,
            candidate_builder=_fake_builder,
        )

        pool = metadata["replacement_pool"]
        self.assertEqual(len(pool), 4)
        self.assertEqual(
            [item["energy"] for item in pool],
            sorted(item["energy"] for item in pool),
        )
        self.assertTrue(all(item["algorithm_source"] == "energy" for item in pool))
        self.assertTrue(all(item["selected"] is False for item in pool))

    def test_replacement_pool_can_be_larger_than_visible_candidates(self):
        selected, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="energy",
            k=2,
            avoid_repeated_runs=False,
            replacement_pool_size=10,
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(selected), 2)
        self.assertGreater(len(metadata["replacement_pool"]), len(selected))
        self.assertLessEqual(len(metadata["replacement_pool"]), 10)

    def test_target_replacement_pool_preserves_target_ranking(self):
        _, metadata = run_split_auto_selection_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            algorithm="target",
            k=1,
            target_f0=102.0,
            target_f2=0.00405,
            replacement_pool_size=5,
            candidate_builder=_fake_builder,
        )

        scores = [item["target_score"] for item in metadata["replacement_pool"]]
        self.assertEqual(scores, sorted(scores))
        self.assertTrue(
            all(
                item["selected"] is False
                for item in metadata["replacement_pool"]
            )
        )

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

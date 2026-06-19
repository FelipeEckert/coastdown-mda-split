# coding: utf-8
"""Tests for pure Split comparison merge helpers."""

import inspect
import unittest

from core.split_comparison_merge import (
    comparison_pair_signature,
    merge_algorithm_candidates_into_comparison_pairs,
)


def _usage(kind, direction, run_id, filename, role, source_hash):
    return (kind, direction, run_id, filename, role, source_hash)


def _run_usage(seed):
    return (
        _usage("high", "+", f"h{seed}", "high.csv", "high", "hash-high"),
        _usage("low", "+", f"l{seed}", "low.csv", "low", "hash-low"),
        _usage("high", "-", f"hm{seed}", "high.csv", "high", "hash-high"),
        _usage("low", "-", f"lm{seed}", "low.csv", "low", "hash-low"),
    )


def _candidate(seed="1", **overrides):
    candidate = {
        "id": f"candidate-{seed}",
        "run_usage": _run_usage(seed),
        "selected": False,
        "selection_source": "algorithm",
        "algorithm_source": "energy",
        "F0_mean": 100.0 + int(seed),
        "F2_mean": 0.004,
        "energy": 1.2 + int(seed),
        "warnings": [f"candidate-warning-{seed}"],
    }
    candidate.update(overrides)
    return candidate


def _manual_pair(seed="1", **overrides):
    pair = {
        "id": f"manual-{seed}",
        "run_usage": _run_usage(seed),
        "selected": True,
        "selection_source": "manual",
        "F0_mean": 999.0,
        "F2_mean": 0.999,
        "energy": 999.0,
        "warnings": ["manual-warning"],
    }
    pair.update(overrides)
    return pair


class SplitComparisonMergeTest(unittest.TestCase):
    def test_adds_new_candidate_to_comparison(self):
        updated, metadata = merge_algorithm_candidates_into_comparison_pairs(
            [],
            [_candidate("1")],
            algorithm_source="energy",
        )

        self.assertEqual(len(updated), 1)
        self.assertEqual(metadata["added_count"], 1)

    def test_new_candidate_enters_unselected(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [],
            [_candidate("1", selected=True)],
            algorithm_source="energy",
        )

        self.assertFalse(updated[0]["selected"])

    def test_new_candidate_enters_with_algorithm_selection_source(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [],
            [_candidate("1", selection_source="manual")],
            algorithm_source="energy",
        )

        self.assertEqual(updated[0]["selection_source"], "algorithm")

    def test_new_candidate_registers_energy_algorithm_source(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [],
            [_candidate("1")],
            algorithm_source="energy",
        )

        self.assertEqual(updated[0]["algorithm_source"], "energy")
        self.assertEqual(updated[0]["algorithm_sources"], ["energy"])
        self.assertTrue(updated[0]["selected_by_energy_algo"])
        self.assertFalse(updated[0]["selected_by_target_algo"])

    def test_new_candidate_registers_target_algorithm_source(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [],
            [_candidate("1", algorithm_source="target")],
            algorithm_source="target",
        )

        self.assertEqual(updated[0]["algorithm_source"], "target")
        self.assertEqual(updated[0]["algorithm_sources"], ["target"])
        self.assertFalse(updated[0]["selected_by_energy_algo"])
        self.assertTrue(updated[0]["selected_by_target_algo"])

    def test_does_not_duplicate_same_signature(self):
        existing = [_manual_pair("1")]
        updated, metadata = merge_algorithm_candidates_into_comparison_pairs(
            existing,
            [_candidate("1")],
            algorithm_source="energy",
        )

        self.assertEqual(len(updated), 1)
        self.assertEqual(metadata["duplicate_count"], 1)

    def test_duplicate_preserves_existing_selected_true(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [_manual_pair("1", selected=True)],
            [_candidate("1", selected=False)],
            algorithm_source="energy",
        )

        self.assertTrue(updated[0]["selected"])

    def test_duplicate_preserves_existing_coefficients_and_energy(self):
        updated, _ = merge_algorithm_candidates_into_comparison_pairs(
            [_manual_pair("1", F0_mean=321.0, F2_mean=0.123, energy=4.56)],
            [_candidate("1", F0_mean=111.0, F2_mean=0.004, energy=1.23)],
            algorithm_source="energy",
        )

        self.assertEqual(updated[0]["F0_mean"], 321.0)
        self.assertEqual(updated[0]["F2_mean"], 0.123)
        self.assertEqual(updated[0]["energy"], 4.56)

    def test_duplicate_updates_algorithm_origin(self):
        updated, metadata = merge_algorithm_candidates_into_comparison_pairs(
            [_manual_pair("1")],
            [_candidate("1")],
            algorithm_source="energy",
        )

        self.assertEqual(updated[0]["algorithm_source"], "energy")
        self.assertEqual(updated[0]["algorithm_sources"], ["energy"])
        self.assertTrue(updated[0]["selected_by_energy_algo"])
        self.assertEqual(metadata["updated_existing_count"], 1)

    def test_supports_multiple_algorithm_origins_on_same_pair(self):
        first, _ = merge_algorithm_candidates_into_comparison_pairs(
            [_manual_pair("1")],
            [_candidate("1")],
            algorithm_source="energy",
        )
        second, _ = merge_algorithm_candidates_into_comparison_pairs(
            first,
            [_candidate("1")],
            algorithm_source="target",
        )

        self.assertEqual(second[0]["algorithm_sources"], ["energy", "target"])
        self.assertTrue(second[0]["selected_by_energy_algo"])
        self.assertTrue(second[0]["selected_by_target_algo"])

    def test_metadata_counts_added_and_duplicates(self):
        updated, metadata = merge_algorithm_candidates_into_comparison_pairs(
            [_manual_pair("1")],
            [_candidate("1"), _candidate("2")],
            algorithm_source="energy",
        )

        self.assertEqual(len(updated), 2)
        self.assertEqual(metadata["input_existing_count"], 1)
        self.assertEqual(metadata["input_candidate_count"], 2)
        self.assertEqual(metadata["added_count"], 1)
        self.assertEqual(metadata["duplicate_count"], 1)
        self.assertEqual(metadata["preserved_selected_count"], 1)
        self.assertEqual(metadata["output_count"], 2)

    def test_invalid_algorithm_source_raises_value_error(self):
        with self.assertRaises(ValueError):
            merge_algorithm_candidates_into_comparison_pairs(
                [],
                [_candidate("1")],
                algorithm_source="bad",
            )

    def test_does_not_mutate_inputs(self):
        existing = [_manual_pair("1")]
        candidate = _candidate("2", selected=True)

        merge_algorithm_candidates_into_comparison_pairs(
            existing,
            [candidate],
            algorithm_source="energy",
        )

        self.assertTrue(existing[0]["selected"])
        self.assertNotIn("algorithm_sources", existing[0])
        self.assertTrue(candidate["selected"])

    def test_signature_uses_flattened_fields_when_run_usage_is_absent(self):
        first = {
            "high_plus_run": 1,
            "high_plus_file": "high.csv",
            "low_plus_run": 2,
            "low_plus_file": "low.csv",
            "high_minus_run": 3,
            "high_minus_file": "high.csv",
            "low_minus_run": 4,
            "low_minus_file": "low.csv",
        }
        second = dict(first)

        self.assertEqual(
            comparison_pair_signature(first),
            comparison_pair_signature(second),
        )

    def test_module_does_not_import_streamlit(self):
        import core.split_comparison_merge as module

        source = inspect.getsource(module)

        self.assertNotIn("import streamlit", source.lower())
        self.assertNotIn("from streamlit", source.lower())
        self.assertFalse(hasattr(module, "st"))


if __name__ == "__main__":
    unittest.main()

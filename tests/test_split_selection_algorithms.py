# coding: utf-8
"""Tests for pure Split automatic selection ranking helpers."""

import inspect
import math
import unittest

from core.split_selection_algorithms import (
    mark_algorithm_source,
    rank_candidates_by_energy,
    rank_candidates_by_target,
    select_top_k_candidates,
    select_top_k_candidates_with_constraints,
)


def _usage(kind, direction, run_id, filename, role, source_hash):
    return (kind, direction, run_id, filename, role, source_hash)


def _candidate(
    candidate_id,
    *,
    energy=None,
    f0=100.0,
    f2=0.004,
    run_usage=None,
):
    return {
        "id": candidate_id,
        "energy": energy,
        "F0_mean": f0,
        "F2_mean": f2,
        "run_usage": run_usage
        if run_usage is not None
        else (
            _usage("high", "+", candidate_id, "high.csv", "high", "hash-high"),
            _usage("low", "+", candidate_id, "low.csv", "low", "hash-low"),
            _usage("high", "-", f"{candidate_id}-m", "high.csv", "high", "hash-high"),
            _usage("low", "-", f"{candidate_id}-m", "low.csv", "low", "hash-low"),
        ),
    }


def _constrained_candidate(
    candidate_id,
    *,
    high_plus=20.0,
    high_minus=20.2,
    low_plus=10.0,
    low_minus=10.2,
    run_usage=None,
):
    candidate = _candidate(
        candidate_id,
        energy=float(ord(candidate_id[0])),
        run_usage=run_usage,
    )
    candidate.update(
        {
            "high_plus_delta_t_s": high_plus,
            "high_minus_delta_t_s": high_minus,
            "low_plus_delta_t_s": low_plus,
            "low_minus_delta_t_s": low_minus,
        }
    )
    return candidate


class SplitSelectionAlgorithmsTest(unittest.TestCase):
    def test_constrained_selector_can_skip_top_k_for_approved_set(self):
        ranked = [
            _constrained_candidate("a"),
            _constrained_candidate("b", high_minus=25.0),
            _constrained_candidate(
                "c", high_plus=20.1, high_minus=20.3,
                low_plus=10.05, low_minus=10.25,
            ),
        ]

        selected, metadata = select_top_k_candidates_with_constraints(ranked, 2)

        self.assertEqual([item["id"] for item in selected], ["a", "c"])
        self.assertTrue(metadata["constraints_satisfied"])
        self.assertEqual(metadata["evaluated_sets_count"], 2)

    def test_constrained_selector_respects_repeated_runs(self):
        shared = (_usage("high", "+", 1, "h.csv", "high", "hash"),)
        ranked = [
            _constrained_candidate("a", run_usage=shared),
            _constrained_candidate("b", run_usage=shared),
            _constrained_candidate("c"),
        ]

        selected, _ = select_top_k_candidates_with_constraints(ranked, 2)

        self.assertEqual([item["id"] for item in selected], ["a", "c"])

    def test_constrained_selector_returns_unapplied_fallback(self):
        shared_b = _usage("high", "+", 1, "h.csv", "high", "hash-b")
        shared_c = _usage("high", "+", 2, "h.csv", "high", "hash-c")
        ranked = [
            _constrained_candidate(
                "a", high_minus=25.0, run_usage=(shared_b, shared_c)
            ),
            _constrained_candidate("b", high_minus=25.1, run_usage=(shared_b,)),
            _constrained_candidate("c", high_minus=25.2, run_usage=(shared_c,)),
        ]

        selected, metadata = select_top_k_candidates_with_constraints(ranked, 2)

        self.assertEqual(selected, [])
        self.assertFalse(metadata["constraints_satisfied"])
        self.assertFalse(metadata["fallback_used"])
        self.assertEqual(
            [item["id"] for item in metadata["fallback_candidates"]],
            ["b", "c"],
        )
        self.assertIsNotNone(metadata["best_failed_validation"])

    def test_constrained_selector_respects_max_set_evaluations(self):
        ranked = [
            _constrained_candidate("a", high_minus=25.0),
            _constrained_candidate("b", high_minus=25.1),
            _constrained_candidate("c"),
        ]

        selected, metadata = select_top_k_candidates_with_constraints(
            ranked,
            2,
            max_set_evaluations=1,
        )

        self.assertEqual(selected, [])
        self.assertEqual(metadata["evaluated_sets_count"], 1)
        self.assertTrue(any("max_set_evaluations" in warning for warning in metadata["warnings"]))

    def test_constrained_selector_accepts_inconclusive_single_pair(self):
        selected, metadata = select_top_k_candidates_with_constraints(
            [_constrained_candidate("a")],
            1,
        )

        self.assertEqual([item["id"] for item in selected], ["a"])
        self.assertIsNone(metadata["constraints_satisfied"])
        self.assertFalse(metadata["fallback_used"])

    def test_energy_ranking_orders_candidates(self):
        ranked = rank_candidates_by_energy(
            [
                _candidate("c", energy=3.0),
                _candidate("a", energy=1.0),
                _candidate("b", energy=2.0),
            ]
        )

        self.assertEqual([candidate["id"] for candidate in ranked], ["a", "b", "c"])

    def test_energy_ranking_prefers_explicit_corrected_value(self):
        corrected = _candidate("corrected", energy=9.0)
        corrected["energy_corrected"] = 1.0
        other = _candidate("other", energy=2.0)
        self.assertEqual(rank_candidates_by_energy([other, corrected])[0]["id"], "corrected")

    def test_energy_ranking_ignores_missing_none_and_nan(self):
        ranked = rank_candidates_by_energy(
            [
                _candidate("missing"),
                _candidate("none", energy=None),
                _candidate("nan", energy=float("nan")),
                _candidate("valid", energy=1.5),
            ]
        )

        self.assertEqual([candidate["id"] for candidate in ranked], ["valid"])

    def test_energy_ranking_uses_stable_signature_tiebreaker(self):
        usage_a = (
            _usage("high", "+", 1, "a.csv", "high", "ha"),
            _usage("low", "+", 1, "a.csv", "low", "la"),
        )
        usage_b = (
            _usage("high", "+", 2, "b.csv", "high", "hb"),
            _usage("low", "+", 2, "b.csv", "low", "lb"),
        )

        ranked = rank_candidates_by_energy(
            [
                _candidate("b", energy=1.0, run_usage=usage_b),
                _candidate("a", energy=1.0, run_usage=usage_a),
            ]
        )

        self.assertEqual([candidate["id"] for candidate in ranked], ["a", "b"])

    def test_target_ranking_calculates_score(self):
        ranked = rank_candidates_by_target(
            [
                _candidate("far", f0=120.0, f2=0.006),
                _candidate("near", f0=101.0, f2=0.0041),
            ],
            target_f0=100.0,
            target_f2=0.004,
        )

        self.assertEqual(ranked[0]["id"], "near")
        expected_score = math.hypot(0.01, 0.025)
        self.assertAlmostEqual(ranked[0]["target_score"], expected_score)

    def test_target_ranking_prefers_explicit_corrected_coefficients(self):
        candidate = _candidate("candidate", f0=500.0, f2=0.02)
        candidate.update({"F0_corrected": 100.0, "F2_corrected": 0.004})
        ranked = rank_candidates_by_target([candidate], 100.0, 0.004)
        self.assertEqual(ranked[0]["target_score"], 0.0)

    def test_target_ranking_adds_error_percentages(self):
        ranked = rank_candidates_by_target(
            [_candidate("c", f0=110.0, f2=0.0044)],
            target_f0=100.0,
            target_f2=0.004,
        )

        self.assertAlmostEqual(ranked[0]["target_error_f0_pct"], 10.0)
        self.assertAlmostEqual(ranked[0]["target_error_f2_pct"], 10.0)

    def test_target_ranking_rejects_zero_target(self):
        with self.assertRaises(ValueError):
            rank_candidates_by_target(
                [_candidate("c")],
                target_f0=0.0,
                target_f2=0.004,
            )

    def test_target_ranking_ignores_candidate_without_valid_f0_f2(self):
        ranked = rank_candidates_by_target(
            [
                _candidate("bad-f0", f0=None, f2=0.004),
                _candidate("bad-f2", f0=100.0, f2=float("nan")),
                _candidate("valid", f0=100.0, f2=0.004),
            ],
            target_f0=100.0,
            target_f2=0.004,
        )

        self.assertEqual([candidate["id"] for candidate in ranked], ["valid"])

    def test_top_k_blocks_exact_repeated_run_usage_item(self):
        shared = _usage("low", "+", 5, "low.csv", "low", "hash-low")
        first_usage = (
            _usage("high", "+", 1, "high.csv", "high", "hash-high"),
            shared,
        )
        second_usage = (
            _usage("high", "+", 2, "high.csv", "high", "hash-high"),
            shared,
        )

        selected, metadata = select_top_k_candidates(
            [
                _candidate("first", energy=1.0, run_usage=first_usage),
                _candidate("second", energy=2.0, run_usage=second_usage),
            ],
            2,
        )

        self.assertEqual([candidate["id"] for candidate in selected], ["first"])
        self.assertEqual(metadata["skipped_repeated_count"], 1)
        self.assertTrue(metadata["warnings"])

    def test_top_k_allows_same_run_id_when_usage_item_differs(self):
        selected, metadata = select_top_k_candidates(
            [
                _candidate(
                    "high",
                    run_usage=(
                        _usage("high", "+", 5, "high.csv", "high", "hash-high"),
                    ),
                ),
                _candidate(
                    "low",
                    run_usage=(
                        _usage("low", "+", 5, "low.csv", "low", "hash-low"),
                    ),
                ),
            ],
            2,
        )

        self.assertEqual([candidate["id"] for candidate in selected], ["high", "low"])
        self.assertEqual(metadata["skipped_repeated_count"], 0)

    def test_top_k_warns_when_requested_count_is_not_reached(self):
        selected, metadata = select_top_k_candidates([_candidate("one")], 2)

        self.assertEqual(len(selected), 1)
        self.assertEqual(metadata["requested_k"], 2)
        self.assertEqual(metadata["selected_count"], 1)
        self.assertTrue(metadata["warnings"])

    def test_top_k_without_repetition_check_allows_repeated_usage(self):
        shared_usage = (
            _usage("high", "+", 5, "high.csv", "high", "hash-high"),
        )

        selected, metadata = select_top_k_candidates(
            [
                _candidate("first", run_usage=shared_usage),
                _candidate("second", run_usage=shared_usage),
            ],
            2,
            avoid_repeated_runs=False,
        )

        self.assertEqual([candidate["id"] for candidate in selected], ["first", "second"])
        self.assertFalse(metadata["avoid_repeated_runs"])
        self.assertEqual(metadata["skipped_repeated_count"], 0)

    def test_top_k_skips_invalid_usage(self):
        selected, metadata = select_top_k_candidates(
            [
                _candidate("invalid", run_usage=()),
                _candidate("valid"),
            ],
            1,
        )

        self.assertEqual([candidate["id"] for candidate in selected], ["valid"])
        self.assertEqual(metadata["skipped_invalid_usage_count"], 1)

    def test_mark_algorithm_source_energy(self):
        marked = mark_algorithm_source([_candidate("c", energy=1.0)], "energy")

        self.assertFalse(marked[0]["selected"])
        self.assertEqual(marked[0]["selection_source"], "algorithm")
        self.assertEqual(marked[0]["algorithm_source"], "energy")
        self.assertTrue(marked[0]["selected_by_energy_algo"])
        self.assertFalse(marked[0]["selected_by_target_algo"])

    def test_mark_algorithm_source_target(self):
        marked = mark_algorithm_source([_candidate("c", energy=1.0)], "target")

        self.assertFalse(marked[0]["selected"])
        self.assertEqual(marked[0]["selection_source"], "algorithm")
        self.assertEqual(marked[0]["algorithm_source"], "target")
        self.assertFalse(marked[0]["selected_by_energy_algo"])
        self.assertTrue(marked[0]["selected_by_target_algo"])

    def test_module_does_not_import_streamlit(self):
        import core.split_selection_algorithms as module

        source = inspect.getsource(module)

        self.assertNotIn("import streamlit", source.lower())
        self.assertNotIn("from streamlit", source.lower())
        self.assertFalse(hasattr(module, "st"))


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for pure Split automatic selection ranking helpers."""

from copy import deepcopy
import math
import unittest
from unittest.mock import patch

from core.split_selection_algorithms import (
    mark_algorithm_source,
    rank_candidates_by_energy,
    rank_candidates_by_target,
    select_top_k_candidates,
    select_top_k_candidates_with_constraints,
    select_top_k_candidates_with_constraints_v2,
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
        self.assertEqual(metadata["evaluated_sets_count"], 3)
        self.assertEqual(metadata["strategy"], "constraint_first_v2")
        self.assertEqual(metadata["valid_sets_found"], 1)

    def test_v2_uses_expanded_default_search_pool(self):
        selected, metadata = select_top_k_candidates_with_constraints_v2(
            [_constrained_candidate("a")],
            1,
        )

        self.assertEqual([item["id"] for item in selected], ["a"])
        self.assertEqual(metadata["requested_pool_size"], 120)
        self.assertEqual(metadata["max_search_seconds"], 30.0)

    def test_v2_finds_valid_set_outside_previous_top_100_pool(self):
        ranked = [
            _constrained_candidate(f"bad-{index}", high_minus=30.0)
            for index in range(100)
        ] + [
            _constrained_candidate(
                "good-1",
                high_plus=20.0,
                high_minus=20.2,
                low_plus=10.0,
                low_minus=10.2,
            ),
            _constrained_candidate(
                "good-2",
                high_plus=20.1,
                high_minus=20.3,
                low_plus=10.05,
                low_minus=10.25,
            ),
        ]

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            2,
            search_pool_size=102,
            max_set_evaluations=6000,
        )

        self.assertEqual([item["id"] for item in selected], ["good-1", "good-2"])
        self.assertTrue(metadata["constraints_satisfied"])
        self.assertEqual(metadata["search_pool_size"], 102)
        self.assertEqual(metadata["valid_sets_found"], 1)
        self.assertFalse(metadata["max_set_evaluations_reached"])

    def test_v2_stops_on_wall_clock_timeout_with_fallback(self):
        ranked = [
            _constrained_candidate("a", high_minus=30.0),
            _constrained_candidate("b", high_minus=30.1),
            _constrained_candidate("c", high_minus=30.2),
        ]

        clock_calls = 0

        def fake_clock():
            nonlocal clock_calls
            clock_calls += 1
            return 0.0 if clock_calls <= 7 else 31.0

        with patch(
            "core.split_selection_algorithms.time.perf_counter",
            side_effect=fake_clock,
        ):
            selected, metadata = select_top_k_candidates_with_constraints_v2(
                ranked,
                2,
                max_set_evaluations=100,
                max_search_seconds=30.0,
            )

        self.assertEqual(selected, [])
        self.assertEqual(metadata["evaluated_sets_count"], 1)
        self.assertTrue(metadata["timeout_reached"])
        self.assertFalse(metadata["max_set_evaluations_reached"])
        self.assertEqual(metadata["elapsed_seconds"], 31.0)
        self.assertEqual(metadata["max_search_seconds"], 30.0)
        self.assertEqual(
            [item["id"] for item in metadata["fallback_candidates"]],
            ["a", "b"],
        )
        self.assertTrue(any("max_search_seconds" in item for item in metadata["warnings"]))

    def test_v2_rejects_invalid_wall_clock_limit(self):
        with self.assertRaises(ValueError):
            select_top_k_candidates_with_constraints_v2(
                [_constrained_candidate("a")],
                1,
                max_search_seconds=0,
            )

    def test_v2_chooses_lowest_aggregate_rank_score_after_validation(self):
        ranked = [_constrained_candidate(identifier) for identifier in "abcdef"]
        valid_ids = {("a", "f"), ("b", "c")}

        def fake_validation(candidates, **_kwargs):
            ids = tuple(candidate["id"] for candidate in candidates)
            approved = ids in valid_ids
            return {
                "passed": approved,
                "coefficient_status": "failed",
                "time_status": "approved" if approved else "failed",
                "cv_f0_pct": 1.0,
                "cv_f2_pct": 1.0,
                "time_group_results": {
                    component: {
                        "passed": approved if component == "high_plus" else True
                    }
                    for component in (
                        "high_plus", "high_minus", "low_plus", "low_minus"
                    )
                },
                "opposite_time_results": {
                    interval: {"passed": True}
                    for interval in ("high", "low")
                },
                "failed_checks": [] if approved else ["time.group.high_plus"],
                "warnings": [],
            }

        with patch(
            "core.split_selection_algorithms.validate_split_candidate_set",
            side_effect=fake_validation,
        ):
            selected, metadata = select_top_k_candidates_with_constraints_v2(
                ranked,
                2,
            )

        self.assertEqual([item["id"] for item in selected], ["b", "c"])
        self.assertEqual(metadata["valid_sets_found"], 2)
        self.assertEqual(metadata["best_valid_score"], 3)
        self.assertEqual(metadata["evaluated_sets_count"], 15)

    def test_v2_accepts_high_coefficient_cv_when_times_pass(self):
        ranked = [
            {
                **_constrained_candidate("a"),
                "F0_mean": 100.0,
                "F2_mean": 0.004,
            },
            {
                **_constrained_candidate(
                    "b",
                    high_plus=20.1,
                    high_minus=20.3,
                    low_plus=10.05,
                    low_minus=10.25,
                ),
                "F0_mean": 150.0,
                "F2_mean": 0.008,
            },
        ]

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            2,
        )

        self.assertEqual([item["id"] for item in selected], ["a", "b"])
        self.assertTrue(metadata["constraints_satisfied"])
        self.assertEqual(
            metadata["constraints_enabled"],
            {"time_cv": True, "opposite_time_difference": True},
        )
        self.assertEqual(metadata["validation"]["coefficient_status"], "failed")
        self.assertEqual(metadata["validation"]["failed_checks"], [])

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
        self.assertEqual(metadata["strategy"], "constraint_first_v2")
        self.assertEqual(metadata["valid_sets_found"], 0)
        self.assertIsNotNone(metadata["best_failed_score"])
        self.assertEqual(
            [item["id"] for item in metadata["fallback_candidates"]],
            ["b", "c"],
        )
        self.assertIsNotNone(metadata["best_failed_validation"])

    def test_v2_fallback_is_best_complete_set_by_original_ranking(self):
        ranked = [
            _constrained_candidate("a", high_minus=30.0),
            _constrained_candidate("b", high_minus=30.1),
            _constrained_candidate("c", high_minus=30.2),
        ]

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            2,
        )

        self.assertEqual(selected, [])
        self.assertEqual(
            [item["id"] for item in metadata["fallback_candidates"]],
            ["a", "b"],
        )
        self.assertEqual(metadata["best_failed_score"], 1)
        self.assertTrue(metadata["best_failed_validation"]["failed_checks"])

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
        self.assertTrue(metadata["max_set_evaluations_reached"])
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

    def test_target_ranking_preserves_results_and_input_candidates(self):
        usage_a = (_usage("high", "+", 1, "a.csv", "high", "ha"),)
        usage_b = (_usage("high", "+", 2, "b.csv", "high", "hb"),)
        candidates = [
            _candidate("far", f0=120.0, f2=0.006),
            _candidate("b", f0=101.0, f2=0.0041, run_usage=usage_b),
            _candidate("a", f0=101.0, f2=0.0041, run_usage=usage_a),
        ]
        original = deepcopy(candidates)

        ranked = rank_candidates_by_target(candidates, 100.0, 0.004)

        expected = {candidate["id"]: candidate for candidate in deepcopy(original)}
        for expected_candidate in expected.values():
            error_f0 = abs(expected_candidate["F0_mean"] - 100.0) / 100.0
            error_f2 = abs(expected_candidate["F2_mean"] - 0.004) / 0.004
            expected_candidate.update({
                "target_score": math.hypot(error_f0, error_f2),
                "target_error_f0_pct": error_f0 * 100.0,
                "target_error_f2_pct": error_f2 * 100.0,
            })

        self.assertEqual(ranked, [expected["a"], expected["b"], expected["far"]])
        self.assertEqual(candidates, original)
        self.assertTrue(all(
            ranked_candidate is not input_candidate
            for ranked_candidate in ranked
            for input_candidate in candidates
        ))

    def test_target_ranking_does_not_copy_or_mutate_nested_data(self):
        nested = {
            "subintervals": ["90-85", "85-80"],
            "traceability": {"source_columns": ["time_90_85", "time_85_80"]},
        }
        candidate = _candidate("candidate", f0=101.0, f2=0.0041)
        candidate["high_plus"] = nested
        original_nested = deepcopy(nested)

        ranked = rank_candidates_by_target([candidate], 100.0, 0.004)

        self.assertIs(ranked[0]["high_plus"], nested)
        self.assertEqual(nested, original_nested)

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

def _cartesian_pool_candidates(n=12, seed=42, use_mad_prefilter=False):
    """Build a realistic high+/low+/high-/low- cartesian candidate pool.

    Mirrors the production shape: n runs per group, each candidate's
    run_usage built from the real `build_split_run_usage` identity, ranked
    by a synthetic energy. Different candidates legitimately share physical
    runs (it's a cartesian product), only the final K-set may not.
    """
    import random as _random

    from core.split_candidate_generation import generate_full_split_candidates_exact
    from core.split_pair_candidate import build_split_run_usage

    rng = _random.Random(seed)

    def make_run(role, heading, run_id, base_delta_t):
        return {
            "interval_name": role,
            "source_role": role,
            "heading": heading,
            "run_id": run_id,
            "filename": f"{role}.csv",
            "delta_t_s": base_delta_t + rng.uniform(-0.3, 0.3),
        }

    parsed = {
        "high": (
            [make_run("high", "+", index, 20.0) for index in range(n)]
            + [make_run("high", "-", 100 + index, 20.5) for index in range(n)]
        ),
        "low": (
            [make_run("low", "+", 200 + index, 10.0) for index in range(n)]
            + [make_run("low", "-", 300 + index, 10.5) for index in range(n)]
        ),
    }

    def builder(*, high_plus_run, low_plus_run, high_minus_run, low_minus_run, **_):
        energy = (
            high_plus_run["delta_t_s"]
            + low_plus_run["delta_t_s"]
            + high_minus_run["delta_t_s"]
            + low_minus_run["delta_t_s"]
        )
        identifier = (
            f"{high_plus_run['run_id']}/{low_plus_run['run_id']}/"
            f"{high_minus_run['run_id']}/{low_minus_run['run_id']}"
        )
        return {
            "id": identifier,
            "energy": energy,
            "run_usage": build_split_run_usage(
                high_plus_run=high_plus_run,
                low_plus_run=low_plus_run,
                high_minus_run=high_minus_run,
                low_minus_run=low_minus_run,
            ),
            "high_plus_delta_t_s": high_plus_run["delta_t_s"],
            "low_plus_delta_t_s": low_plus_run["delta_t_s"],
            "high_minus_delta_t_s": high_minus_run["delta_t_s"],
            "low_minus_delta_t_s": low_minus_run["delta_t_s"],
            "F0_mean": 100.0,
            "F2_mean": 0.004,
        }

    candidates, generation_metadata = generate_full_split_candidates_exact(
        parsed,
        vehicle_data={"effective_mass": 1.0},
        candidate_builder=builder,
        use_mad_prefilter=use_mad_prefilter,
    )
    return candidates, generation_metadata


class SplitSelectionAlgorithmsRealisticPoolTest(unittest.TestCase):
    """Regression coverage for the run-uniqueness scope fix (K=5, ~12 runs/group)."""

    def test_constrained_search_finds_disjoint_sets_in_realistic_cartesian_pool(self):
        candidates, _ = _cartesian_pool_candidates(n=12)
        ranked = rank_candidates_by_energy(candidates)

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            5,
            avoid_repeated_runs=True,
            require_time_cv=True,
            require_opposite_time_difference=True,
            search_pool_size=300,
            max_set_evaluations=3000,
            max_search_seconds=10.0,
        )

        self.assertEqual(len(selected), 5)
        self.assertGreater(metadata["evaluated_sets_count"], 0)
        self.assertTrue(metadata["constraints_satisfied"])

    def test_final_set_never_repeats_a_physical_run(self):
        candidates, _ = _cartesian_pool_candidates(n=12)
        ranked = rank_candidates_by_energy(candidates)

        selected, _ = select_top_k_candidates_with_constraints_v2(
            ranked,
            5,
            avoid_repeated_runs=True,
            require_time_cv=True,
            require_opposite_time_difference=True,
            search_pool_size=300,
            max_set_evaluations=3000,
            max_search_seconds=10.0,
        )

        seen_runs = set()
        for candidate in selected:
            usage = set(candidate["run_usage"])
            self.assertFalse(seen_runs.intersection(usage))
            seen_runs.update(usage)

    def test_avoid_repeated_runs_false_bypasses_uniqueness_in_realistic_pool(self):
        candidates, _ = _cartesian_pool_candidates(n=12)
        ranked = rank_candidates_by_energy(candidates)

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            5,
            avoid_repeated_runs=False,
            require_time_cv=False,
            require_opposite_time_difference=False,
            search_pool_size=300,
            max_set_evaluations=3000,
            max_search_seconds=10.0,
        )

        self.assertEqual(len(selected), 5)
        self.assertEqual(
            [candidate["id"] for candidate in selected],
            [candidate["id"] for candidate in ranked[:5]],
        )
        self.assertGreater(metadata["evaluated_sets_count"], 0)

    def test_mad_prefilter_pipeline_still_finds_disjoint_sets(self):
        candidates, generation_metadata = _cartesian_pool_candidates(
            n=10, use_mad_prefilter=True,
        )
        self.assertTrue(generation_metadata["prefilter_applied"])
        ranked = rank_candidates_by_energy(candidates)

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            5,
            avoid_repeated_runs=True,
            require_time_cv=True,
            require_opposite_time_difference=True,
            search_pool_size=300,
            max_set_evaluations=3000,
            max_search_seconds=10.0,
        )

        self.assertEqual(len(selected), 5)
        self.assertGreater(metadata["evaluated_sets_count"], 0)

    def test_rescue_recovers_a_valid_set_when_search_times_out_immediately(self):
        candidates, _ = _cartesian_pool_candidates(n=12)
        ranked = rank_candidates_by_energy(candidates)

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            5,
            avoid_repeated_runs=True,
            require_time_cv=False,
            require_opposite_time_difference=False,
            search_pool_size=2000,
            max_set_evaluations=3000,
            max_search_seconds=1e-9,
        )

        self.assertTrue(metadata["rescue"]["attempted"])
        self.assertTrue(metadata["rescue"]["found_valid_set"])
        self.assertEqual(len(selected), 5)
        seen_runs = set()
        for candidate in selected:
            usage = set(candidate["run_usage"])
            self.assertFalse(seen_runs.intersection(usage))
            seen_runs.update(usage)

    def test_rescue_does_not_attempt_when_dfs_already_evaluated_sets(self):
        ranked = [
            _constrained_candidate("a", high_minus=30.0),
            _constrained_candidate("b", high_minus=30.1),
            _constrained_candidate("c", high_minus=30.2),
        ]

        selected, metadata = select_top_k_candidates_with_constraints_v2(
            ranked,
            2,
            max_set_evaluations=1,
        )

        self.assertEqual(selected, [])
        self.assertEqual(metadata["evaluated_sets_count"], 1)
        self.assertFalse(metadata["rescue"]["attempted"])


if __name__ == "__main__":
    unittest.main()

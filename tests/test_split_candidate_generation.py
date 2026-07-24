# coding: utf-8
"""Tests for exact Split candidate generation helpers."""

import unittest

from core.split_candidate_generation import (
    estimate_full_candidate_count,
    filter_group_by_mad,
    generate_full_split_candidates_exact,
    iter_full_candidate_run_groups,
    split_runs_by_role_and_heading,
)


def _run(role, heading, run_id, filename=None, delta_t_s=10.0):
    return {
        "interval_name": role,
        "source_role": role,
        "heading": heading,
        "run_id": run_id,
        "filename": filename or f"{role}.csv",
        "delta_t_s": delta_t_s,
    }


def _parsed():
    return {
        "high": [
            _run("high", "+", 2, delta_t_s=20.2),
            _run("high", "-", 4, delta_t_s=21.4),
            _run("high", "+", 1, delta_t_s=20.1),
            _run("high", "-", 3, delta_t_s=21.3),
        ],
        "low": [
            _run("low", "+", 6, delta_t_s=10.6),
            _run("low", "-", 8, delta_t_s=11.8),
            _run("low", "+", 5, delta_t_s=10.5),
            _run("low", "-", 7, delta_t_s=11.7),
        ],
        "warnings": ["source warning"],
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
    return {
        "id": (
            f"{high_plus_run['run_id']}/"
            f"{low_plus_run['run_id']}/"
            f"{high_minus_run['run_id']}/"
            f"{low_minus_run['run_id']}"
        ),
        "vehicle_data": vehicle_data,
        "correction_context": correction_context,
    }


class SplitCandidateGenerationTest(unittest.TestCase):
    def test_groups_runs_by_role_and_heading(self):
        grouped = split_runs_by_role_and_heading(_parsed())

        self.assertEqual([run["run_id"] for run in grouped["high_plus"]], [1, 2])
        self.assertEqual([run["run_id"] for run in grouped["high_minus"]], [3, 4])
        self.assertEqual([run["run_id"] for run in grouped["low_plus"]], [5, 6])
        self.assertEqual([run["run_id"] for run in grouped["low_minus"]], [7, 8])
        self.assertEqual(grouped["warnings"], ["source warning"])

    def test_invalid_heading_is_ignored_with_warning(self):
        parsed = {
            "high": [_run("high", "ida", 1)],
            "low": [_run("low", "+", 2), _run("low", "-", 3)],
        }

        grouped = split_runs_by_role_and_heading(parsed)

        self.assertEqual(grouped["high_plus"], [])
        self.assertTrue(any("invalid heading" in warning for warning in grouped["warnings"]))

    def test_estimate_full_candidate_count_multiplies_groups(self):
        grouped = split_runs_by_role_and_heading(_parsed())

        self.assertEqual(estimate_full_candidate_count(grouped), 16)

    def test_estimate_full_candidate_count_returns_zero_for_missing_group(self):
        self.assertEqual(estimate_full_candidate_count({"high_plus": [1]}), 0)

    def test_iter_full_candidate_run_groups_yields_expected_combinations(self):
        grouped = split_runs_by_role_and_heading(_parsed())
        combinations = list(iter_full_candidate_run_groups(grouped))

        self.assertEqual(len(combinations), 16)
        self.assertEqual(
            combinations[0]["high_plus_run"]["run_id"],
            1,
        )
        self.assertEqual(
            combinations[0]["low_plus_run"]["run_id"],
            5,
        )
        self.assertEqual(
            combinations[0]["high_minus_run"]["run_id"],
            3,
        )
        self.assertEqual(
            combinations[0]["low_minus_run"]["run_id"],
            7,
        )

    def test_generate_exact_uses_injected_candidate_builder(self):
        candidates, metadata = generate_full_split_candidates_exact(
            {
                "high": [_run("high", "+", 1), _run("high", "-", 2)],
                "low": [_run("low", "+", 3), _run("low", "-", 4)],
            },
            vehicle_data={"effective_mass": 1.0},
            correction_context={"ambient": "fixed"},
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["id"], "1/3/2/4")
        self.assertEqual(candidates[0]["vehicle_data"], {"effective_mass": 1.0})
        self.assertEqual(metadata["generated_count"], 1)

    def test_generate_exact_returns_expected_quantity_for_small_fixture(self):
        candidates, metadata = generate_full_split_candidates_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=_fake_builder,
        )

        self.assertEqual(len(candidates), 16)
        self.assertEqual(metadata["estimated_total"], 16)
        self.assertEqual(metadata["attempted_count"], 16)
        self.assertEqual(metadata["failed_count"], 0)

    def test_candidate_error_does_not_abort_generation(self):
        def flaky_builder(**kwargs):
            if kwargs["high_plus_run"]["run_id"] == 1:
                raise ValueError("bad candidate")
            return _fake_builder(**kwargs)

        candidates, metadata = generate_full_split_candidates_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=flaky_builder,
        )

        self.assertEqual(len(candidates), 8)
        self.assertEqual(metadata["failed_count"], 8)
        self.assertTrue(any("bad candidate" in warning for warning in metadata["warnings"]))

    def test_max_combinations_blocks_generation(self):
        candidates, metadata = generate_full_split_candidates_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=_fake_builder,
            max_combinations=4,
        )

        self.assertEqual(candidates, [])
        self.assertEqual(metadata["estimated_total"], 16)
        self.assertEqual(metadata["attempted_count"], 0)
        self.assertEqual(metadata["skipped_count"], 16)
        self.assertTrue(
            any("max_combinations" in warning for warning in metadata["warnings"])
        )

    def test_progress_callback_is_called(self):
        progress = []

        generate_full_split_candidates_exact(
            {
                "high": [_run("high", "+", 1), _run("high", "-", 2)],
                "low": [_run("low", "+", 3), _run("low", "-", 4)],
            },
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=_fake_builder,
            progress_callback=progress.append,
        )

        self.assertEqual(progress, [1.0])

    def test_large_generation_preserves_candidates_and_throttles_progress(self):
        parsed = {
            "high": (
                [_run("high", "+", index) for index in range(10)]
                + [_run("high", "-", 100 + index) for index in range(10)]
            ),
            "low": (
                [_run("low", "+", 200 + index) for index in range(10)]
                + [_run("low", "-", 300 + index) for index in range(10)]
            ),
        }
        vehicle_data = {"effective_mass": 1.0}
        grouped = split_runs_by_role_and_heading(parsed)
        expected = [
            _fake_builder(
                **run_group,
                vehicle_data=vehicle_data,
            )
            for run_group in iter_full_candidate_run_groups(grouped)
        ]
        progress = []

        candidates, metadata = generate_full_split_candidates_exact(
            parsed,
            vehicle_data=vehicle_data,
            candidate_builder=_fake_builder,
            progress_callback=progress.append,
            use_mad_prefilter=False,
        )

        self.assertEqual(candidates, expected)
        self.assertEqual(metadata["generated_count"], 10_000)
        self.assertTrue(
            all(first < second for first, second in zip(progress, progress[1:]))
        )
        self.assertEqual(progress[-1], 1.0)
        self.assertLessEqual(len(progress), 101)

    def test_metadata_contains_expected_counters(self):
        _, metadata = generate_full_split_candidates_exact(
            _parsed(),
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=_fake_builder,
        )

        self.assertEqual(metadata["mode"], "exact")
        self.assertEqual(
            metadata["group_counts"],
            {
                "high_plus": 2,
                "low_plus": 2,
                "high_minus": 2,
                "low_minus": 2,
            },
        )
        self.assertEqual(metadata["generated_count"], 16)
        self.assertIn("source warning", metadata["warnings"])

    def test_zero_candidates_returns_warning(self):
        candidates, metadata = generate_full_split_candidates_exact(
            {"high": [], "low": []},
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=_fake_builder,
        )

        self.assertEqual(candidates, [])
        self.assertEqual(metadata["estimated_total"], 0)
        self.assertTrue(metadata["warnings"])


class FilterGroupByMadTest(unittest.TestCase):
    def test_normal_filter_removes_single_outlier(self):
        records = [
            _run("high", "+", 1, delta_t_s=10.0),
            _run("high", "+", 2, delta_t_s=10.1),
            _run("high", "+", 3, delta_t_s=10.1),
            _run("high", "+", 4, delta_t_s=10.2),
            _run("high", "+", 5, delta_t_s=10.3),
            _run("high", "+", 6, delta_t_s=20.0),
        ]

        filtered, metadata = filter_group_by_mad(records, min_pool_size=4)

        self.assertEqual(metadata["input_count"], 6)
        self.assertEqual(metadata["output_count"], 5)
        self.assertEqual(metadata["filtered_count"], 1)
        self.assertIsNone(metadata["skipped_reason"])
        self.assertNotIn(6, [run["run_id"] for run in filtered])

    def test_too_few_records_is_skipped(self):
        records = [
            _run("high", "+", 1, delta_t_s=10.0),
            _run("high", "+", 2, delta_t_s=99.0),
        ]

        filtered, metadata = filter_group_by_mad(records, min_pool_size=4)

        self.assertEqual(metadata["skipped_reason"], "too_few_records")
        self.assertEqual(filtered, records)

    def test_mad_is_zero_is_skipped(self):
        records = [
            _run("high", "+", 1, delta_t_s=10.0),
            _run("high", "+", 2, delta_t_s=10.0),
            _run("high", "+", 3, delta_t_s=10.0),
        ]

        filtered, metadata = filter_group_by_mad(records, min_pool_size=2)

        self.assertEqual(metadata["skipped_reason"], "mad_is_zero")
        self.assertEqual(filtered, records)

    def test_min_pool_size_is_preserved_when_filter_is_too_aggressive(self):
        records = [
            _run("high", "+", 1, delta_t_s=10.0),
            _run("high", "+", 2, delta_t_s=10.1),
            _run("high", "+", 3, delta_t_s=10.2),
            _run("high", "+", 4, delta_t_s=30.0),
            _run("high", "+", 5, delta_t_s=40.0),
        ]

        filtered, metadata = filter_group_by_mad(records, min_pool_size=4)

        self.assertEqual(metadata["skipped_reason"], "min_pool_preserved")
        self.assertEqual(metadata["output_count"], 4)
        self.assertEqual(len(filtered), 4)

    def test_disabled_prefilter_keeps_full_cartesian_product(self):
        def builder(*, high_plus_run, low_plus_run, high_minus_run, low_minus_run, **_):
            return {
                "id": (
                    f"{high_plus_run['run_id']}/{low_plus_run['run_id']}/"
                    f"{high_minus_run['run_id']}/{low_minus_run['run_id']}"
                )
            }

        parsed = {
            "high": [
                _run("high", "+", 1, delta_t_s=10.0),
                _run("high", "+", 2, delta_t_s=10.1),
                _run("high", "+", 3, delta_t_s=99.0),
                _run("high", "-", 4, delta_t_s=20.0),
                _run("high", "-", 5, delta_t_s=20.1),
                _run("high", "-", 6, delta_t_s=21.0),
            ],
            "low": [
                _run("low", "+", 7, delta_t_s=10.0),
                _run("low", "+", 8, delta_t_s=10.1),
                _run("low", "+", 9, delta_t_s=10.2),
                _run("low", "-", 10, delta_t_s=11.0),
                _run("low", "-", 11, delta_t_s=11.1),
                _run("low", "-", 12, delta_t_s=11.2),
            ],
        }

        candidates, metadata = generate_full_split_candidates_exact(
            parsed,
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=builder,
            use_mad_prefilter=False,
        )

        self.assertFalse(metadata["prefilter_applied"])
        self.assertEqual(metadata["prefilter"], {})
        self.assertEqual(metadata["estimated_total"], 3 * 3 * 3 * 3)
        self.assertEqual(len(candidates), 3 * 3 * 3 * 3)

    def test_mad_prefilter_reduces_cartesian_product_below_unfiltered_total(self):
        def builder(*, high_plus_run, low_plus_run, high_minus_run, low_minus_run, **_):
            return {
                "id": (
                    f"{high_plus_run['run_id']}/{low_plus_run['run_id']}/"
                    f"{high_minus_run['run_id']}/{low_minus_run['run_id']}"
                )
            }

        def _group(role, heading, base_id, base_delta_t):
            runs = [
                _run(role, heading, base_id + index, delta_t_s=base_delta_t + index * 0.01)
                for index in range(11)
            ]
            runs.append(
                _run(role, heading, base_id + 100, delta_t_s=base_delta_t * 2.0)
            )
            return runs

        parsed = {
            "high": _group("high", "+", 1, 20.0) + _group("high", "-", 200, 20.5),
            "low": _group("low", "+", 400, 10.0) + _group("low", "-", 600, 10.5),
        }

        candidates, metadata = generate_full_split_candidates_exact(
            parsed,
            vehicle_data={"effective_mass": 1.0},
            candidate_builder=builder,
            use_mad_prefilter=True,
            mad_min_pool_size=4,
        )

        self.assertTrue(metadata["prefilter_applied"])
        self.assertEqual(metadata["estimated_total"], 11 ** 4)
        self.assertLess(metadata["estimated_total"], 12 ** 4)
        self.assertEqual(len(candidates), 11 ** 4)
        for key in ("high_plus", "high_minus", "low_plus", "low_minus"):
            self.assertEqual(metadata["prefilter"][key]["filtered_count"], 1)


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Focused tests for Split run-level statistical candidate grouping."""

import unittest
from copy import deepcopy
from unittest.mock import patch

from core.split_statistical_analysis import (
    _compatibility_sort_key,
    analyze_split_statistical_candidates,
)
from core.split_time_validation import validate_split_selected_times


def _run(run_id, values, *, interval="high", heading="+"):
    labels = [f"bin-{index}" for index in range(len(values))]
    return {
        "run_id": run_id,
        "filename": f"{interval}.csv",
        "source_role": interval,
        "heading": heading,
        "subintervals": labels,
        "subinterval_times_s": values,
        "delta_t_s": sum(values),
    }


def _population(records):
    result = analyze_split_statistical_candidates({"high": records})
    return result["populations"]["high_plus"]


class SplitStatisticalAnalysisTests(unittest.TestCase):
    def test_separated_groups_and_parent_are_enumerated_with_metadata(self):
        records = [
            *[_run(index, [1.0, 1.0]) for index in range(1, 6)],
            *[_run(index, [10.0, 10.0]) for index in range(6, 11)],
        ]

        groups = _population(records)["candidate_groups"]

        self.assertEqual(
            [group["run_ids"] for group in groups],
            [
                (1, 2, 3, 4, 5),
                (6, 7, 8, 9, 10),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            ],
        )
        self.assertEqual(
            [group["cohesion_distance"] for group in groups],
            [0.0, 0.0, 2.0],
        )
        self.assertEqual(groups[0]["population"], "high_plus")
        self.assertEqual(groups[0]["size"], 5)
        self.assertEqual(groups[0]["mean_delta_t_s"], 2.0)
        self.assertEqual(groups[0]["sample_stdev_s"], 0.0)
        self.assertEqual(groups[0]["cv_pct"], 0.0)
        self.assertIs(groups[0]["cv_conforming"], True)
        self.assertIs(groups[-1]["cv_conforming"], False)

    def test_four_populations_are_analyzed_independently(self):
        parsed = {
            "high": [
                *[_run(index, [1.0, 1.0]) for index in range(1, 6)],
                *[_run(index, [100.0, 100.0], heading="-") for index in range(6, 11)],
            ],
            "low": [
                *[_run(index, [10.0, 20.0], interval="low") for index in range(11, 16)],
                *[
                    _run(index, [1000.0, 2000.0], interval="low", heading="-")
                    for index in range(16, 21)
                ],
            ],
        }

        result = analyze_split_statistical_candidates(parsed)

        self.assertEqual(
            {
                component: len(population["candidate_groups"])
                for component, population in result["populations"].items()
            },
            {"high_plus": 1, "high_minus": 1, "low_plus": 1, "low_minus": 1},
        )
        self.assertEqual(
            {
                interval: len(combinations)
                for interval, combinations in result[
                    "opposite_direction_combinations"
                ].items()
            },
            {"high": 1, "low": 1},
        )

    def test_opposite_compatibility_reuses_normative_validator(self):
        parsed = {
            "high": [
                *[_run(index, [5.0, 5.0]) for index in range(1, 6)],
                *[
                    _run(index, [5.5, 5.5], heading="-")
                    for index in range(6, 11)
                ],
            ]
        }

        with patch(
            "core.split_statistical_analysis.validate_split_selected_times",
            wraps=validate_split_selected_times,
        ) as validator:
            result = analyze_split_statistical_candidates(parsed)

        combinations = result["opposite_direction_combinations"]["high"]
        self.assertEqual(validator.call_count, 3)
        self.assertEqual(len(combinations), 1)
        combination = combinations[0]
        self.assertEqual(combination["rank"], 1)
        self.assertEqual(combination["plus_candidate_id"], "high_plus_1")
        self.assertEqual(combination["plus_run_ids"], (1, 2, 3, 4, 5))
        self.assertEqual(combination["minus_candidate_id"], "high_minus_1")
        self.assertEqual(combination["minus_run_ids"], (6, 7, 8, 9, 10))
        self.assertEqual(
            (combination["plus_size"], combination["minus_size"]),
            (5, 5),
        )
        self.assertEqual(
            (
                combination["plus_mean_delta_t_s"],
                combination["minus_mean_delta_t_s"],
            ),
            (10.0, 11.0),
        )
        self.assertEqual(
            (combination["plus_cv_pct"], combination["minus_cv_pct"]),
            (0.0, 0.0),
        )
        self.assertIs(combination["plus_cv_conforming"], True)
        self.assertIs(combination["minus_cv_conforming"], True)
        self.assertAlmostEqual(
            combination["opposite_difference_pct"],
            100 / 10.5,
        )
        self.assertIs(combination["opposite_conforming"], True)
        self.assertEqual(combination["opposite_limit_pct"], 10.0)

    def test_compatibility_ranking_uses_the_required_priority_order(self):
        base = {
            "opposite_conforming": True,
            "both_directional_cvs_conforming": True,
            "opposite_difference_pct": 1.0,
            "usable_run_count": 12,
            "cohesion_distance": 1.0,
            "plus_cohesion_distance": 0.5,
            "minus_cohesion_distance": 0.5,
            "minus_candidate_id": "minus",
        }

        def combination(identifier, **changes):
            return base | {"plus_candidate_id": identifier} | changes

        combinations = [
            combination("none", opposite_conforming=None),
            combination("failed", opposite_conforming=False),
            combination("cv", both_directional_cvs_conforming=False),
            combination("difference", opposite_difference_pct=2.0),
            combination("small", usable_run_count=10, cohesion_distance=0.1),
            combination(
                "coarse",
                cohesion_distance=2.0,
                plus_cohesion_distance=1.0,
                minus_cohesion_distance=1.0,
            ),
            combination("best"),
        ]

        ranked = sorted(combinations, key=_compatibility_sort_key)

        self.assertEqual(
            [item["plus_candidate_id"] for item in ranked],
            ["best", "coarse", "small", "difference", "cv", "failed", "none"],
        )

    def test_distance_is_normalized_by_feature_count(self):
        two_features = [
            _run(index, [float(index), 2.0 * index])
            for index in range(1, 6)
        ]
        four_features = [
            _run(index, [float(index), 2.0 * index] * 2)
            for index in range(1, 6)
        ]

        two_distance = _population(two_features)["candidate_groups"][0][
            "cohesion_distance"
        ]
        four_distance = _population(four_features)["candidate_groups"][0][
            "cohesion_distance"
        ]

        self.assertAlmostEqual(two_distance, four_distance)

    def test_homogeneous_data_forms_one_candidate_group(self):
        records = [
            _run(index, [1.0 + index / 100, 2.0 - index / 100])
            for index in range(1, 7)
        ]

        groups = _population(records)["candidate_groups"]

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["size"], 6)

    def test_isolated_runs_appear_only_in_coarser_parent_groups(self):
        records = [
            *[_run(index, [1.0, 1.0]) for index in range(1, 6)],
            _run(6, [10.0, 1.0]),
            _run(7, [1.0, 10.0]),
        ]

        groups = _population(records)["candidate_groups"]

        self.assertEqual([group["size"] for group in groups], [5, 6, 7])
        self.assertEqual(groups[0]["run_ids"], (1, 2, 3, 4, 5))
        self.assertNotIn(6, groups[0]["run_ids"])
        self.assertNotIn(7, groups[0]["run_ids"])

    def test_fewer_than_five_runs_exposes_no_candidate_group(self):
        population = _population(
            [_run(index, [1.0, 1.0]) for index in range(1, 5)]
        )

        self.assertEqual(population["usable_run_count"], 4)
        self.assertEqual(population["candidate_groups"], tuple())

    def test_identical_groups_are_deduplicated_deterministically(self):
        records = [_run(index, [3.0, 4.0, 5.0]) for index in range(1, 7)]
        original = deepcopy(records)

        first = _population(records)
        second = _population(records)

        self.assertEqual(first, second)
        self.assertEqual(records, original)
        self.assertEqual(len(first["candidate_groups"]), 1)
        self.assertEqual(
            first["candidate_groups"][0]["run_ids"],
            (1, 2, 3, 4, 5, 6),
        )
        self.assertEqual(first["candidate_groups"][0]["cohesion_distance"], 0.0)
        self.assertTrue(
            all(
                run["normalized_features"] == (0.0, 0.0, 0.0)
                for run in first["runs"]
            )
        )


if __name__ == "__main__":
    unittest.main()

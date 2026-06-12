# coding: utf-8
"""Tests for pure Split graph data preparation."""

import unittest

from data.split_parser import default_split_interval_config, parse_split_sources
from utils.split_graphs import (
    apply_split_run_selection_action,
    build_split_run_plot_series,
    collect_split_run_options,
    filter_split_run_options,
    reconcile_split_run_selection,
    split_pair_component_records,
)


class SplitGraphsTest(unittest.TestCase):
    def test_collects_and_filters_processed_split_runs(self):
        parsed = {
            "high": [
                {"run_id": 1, "heading": "+"},
                {"run_id": 2, "heading": "-"},
            ],
            "low": [
                {"run_id": 3, "heading": "+"},
                {"run_id": 4, "heading": "N/A"},
            ],
        }

        options = collect_split_run_options(parsed)

        self.assertEqual([item["option_id"] for item in options], [
            "high:0",
            "high:1",
            "low:0",
            "low:1",
        ])
        self.assertEqual(
            [item["record"]["run_id"] for item in filter_split_run_options(
                options,
                interval_name="high",
                direction="+",
            )],
            [1],
        )
        self.assertEqual(
            [item["record"]["run_id"] for item in filter_split_run_options(options)],
            [1, 2, 3],
        )

    def test_filters_high_and_low_directions_independently(self):
        options = collect_split_run_options(
            {
                "high": [
                    {"run_id": 1, "heading": "+"},
                    {"run_id": 2, "heading": "-"},
                ],
                "low": [
                    {"run_id": 3, "heading": "+"},
                    {"run_id": 4, "heading": "-"},
                ],
            }
        )

        high_plus = filter_split_run_options(
            options,
            interval_name="high",
            direction="+",
        )
        low_minus = filter_split_run_options(
            options,
            interval_name="low",
            direction="-",
        )

        self.assertEqual([item["option_id"] for item in high_plus], ["high:0"])
        self.assertEqual([item["option_id"] for item in low_minus], ["low:1"])

    def test_reconciles_high_selection_without_changing_low_selection(self):
        high_selected = ["high:0", "high:1"]
        low_selected = ["low:0", "low:1"]

        reconciled_high = apply_split_run_selection_action(
            high_selected,
            ["high:0"],
        )

        self.assertEqual(reconciled_high, ["high:0"])
        self.assertEqual(low_selected, ["low:0", "low:1"])

    def test_reconciles_low_selection_without_changing_high_selection(self):
        high_selected = ["high:0", "high:1"]
        low_selected = ["low:0", "low:1"]

        reconciled_low = apply_split_run_selection_action(
            low_selected,
            ["low:1"],
        )

        self.assertEqual(reconciled_low, ["low:1"])
        self.assertEqual(high_selected, ["high:0", "high:1"])

    def test_empty_options_and_selection_do_not_raise(self):
        self.assertEqual(filter_split_run_options([], "high", "+"), [])
        self.assertEqual(reconcile_split_run_selection([], []), [])
        self.assertEqual(reconcile_split_run_selection(None, None), [])

    def test_add_all_and_clear_actions_are_section_local(self):
        high_selected = apply_split_run_selection_action(
            [],
            ["high:0", "high:1"],
            action="add_all",
        )
        low_selected = ["low:0"]

        self.assertEqual(high_selected, ["high:0", "high:1"])
        self.assertEqual(low_selected, ["low:0"])

        low_selected = apply_split_run_selection_action(
            low_selected,
            ["low:0", "low:1"],
            action="clear",
        )

        self.assertEqual(high_selected, ["high:0", "high:1"])
        self.assertEqual(low_selected, [])

    def test_builds_interval_curve_from_real_source_bins(self):
        run_data = {
            "times": [0.0, 4.0, 9.0, 15.0, 22.0],
            "velocities": [90.0, 85.0, 80.0, 75.0, 70.0],
            "heading": "+",
        }
        sources = [
            {
                "filename": "high.csv",
                "role": "high",
                "all_run_data": {1: run_data},
            }
        ]
        parsed = parse_split_sources(sources, default_split_interval_config())

        series = build_split_run_plot_series(parsed["high"][0], sources)

        self.assertEqual(series["data_mode"], "interval_curve")
        self.assertEqual(series["times_s"], [0.0, 4.0, 9.0, 15.0, 22.0])
        self.assertEqual(series["speeds_kmh"], [90.0, 85.0, 80.0, 75.0, 70.0])
        self.assertEqual(len(series["interval_rows"]), 4)

    def test_builds_interval_curve_from_labeled_aggregate_columns(self):
        run_data = {
            "interval_measurements": [
                {"column": "90-85", "label": "90-85", "time_s": 4.0},
                {"column": "85-80", "label": "85-80", "time_s": 5.0},
                {"column": "80-75", "label": "80-75", "time_s": 6.0},
                {"column": "75-70", "label": "75-70", "time_s": 7.0},
            ],
            "heading": "-",
        }
        sources = [
            {
                "filename": "combined.csv",
                "role": "full_or_combined",
                "all_run_data": {"1": run_data},
            }
        ]
        parsed = parse_split_sources(sources, default_split_interval_config())

        series = build_split_run_plot_series(parsed["high"][0], sources)

        self.assertEqual(series["data_mode"], "interval_curve")
        self.assertEqual(series["times_s"], [0.0, 4.0, 9.0, 15.0, 22.0])
        self.assertEqual(series["direction"], "-")

    def test_falls_back_to_aggregate_segment_when_source_is_unavailable(self):
        record = {
            "interval_name": "low",
            "run_id": 3,
            "heading": "+",
            "start_kmh": 45.0,
            "end_kmh": 35.0,
            "delta_t_s": 19.58,
        }

        series = build_split_run_plot_series(record, [])

        self.assertEqual(series["data_mode"], "aggregate")
        self.assertEqual(series["times_s"], [0.0, 19.58])
        self.assertEqual(series["speeds_kmh"], [45.0, 35.0])

    def test_reads_only_nested_split_pair_components(self):
        pair = {
            "id": "split_pair_technical",
            "high_plus": {"run_id": 2},
            "low_plus": {"run_id": 1},
            "high_minus": {"run_id": 1},
            "low_minus": {"run_id": 4},
        }

        components = split_pair_component_records(pair)

        self.assertEqual(
            [item["component"] for item in components],
            ["high_plus", "low_plus", "high_minus", "low_minus"],
        )
        self.assertNotIn("id", components[0])


if __name__ == "__main__":
    unittest.main()

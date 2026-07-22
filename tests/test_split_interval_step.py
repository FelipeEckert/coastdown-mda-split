# coding: utf-8
"""Tests for configurable Split coastdown interval steps."""

from pathlib import Path
import tempfile
import unittest

from core.split_state import (
    get_processed_split_review_state,
    record_split_parse_failure,
    should_show_split_parse_details,
    split_parse_is_current,
    store_processed_split_intervals,
    update_split_interval_config,
    update_split_interval_draft,
)
from data.loaders import carregar_dados_csv_robusto
from data.split_parser import (
    default_split_interval_config,
    parse_speed_bin_label,
    parse_split_sources,
    required_subintervals,
    validate_split_interval_config,
)


class SplitIntervalStepTest(unittest.TestCase):
    def _load_labeled_vbox(self, labels, times):
        metadata = [
            "Test Date: 22/04/2024 15:49",
            "Time zone,E. South America Standard Time",
            "Test Date,",
            "Trigger",
            "Requires Trigger,Off",
            "Trigger Channel,",
            "Deceleration",
            "Ignore runs that exceed (g),0.20",
            "Smooth Level,4",
            "Speed Quality",
            "Check,Off",
            "Speed threshold (km/h),0.10",
            "In (s),0.05",
            "",
        ]
        header = ",".join(
            [
                "Run-Use",
                "Heading",
                "Run",
                "Time (s)",
                "Distance (m)",
                "Start Time",
                "Max Decel (g)",
                *labels,
                "Notes",
            ]
        )
        row = ",".join(
            [
                "On",
                "+",
                "1",
                str(sum(times)),
                "500",
                "18:47:17.147",
                "0.10",
                *(str(value) for value in times),
                "",
            ]
        )
        content = "\n".join([*metadata, header, row])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "labeled_vbox.csv"
            path.write_text(content, encoding="utf-8")
            _, runs, _ = carregar_dados_csv_robusto(
                str(path),
                using_split_method=True,
                is_alta=True,
            )
        return runs

    def test_default_interval_step_is_five_kmh(self):
        self.assertEqual(default_split_interval_config()["step_kmh"], 5.0)

    def test_speed_bin_labels_are_parsed_from_real_interval_text(self):
        self.assertEqual(parse_speed_bin_label("100-90"), (100.0, 90.0))
        self.assertEqual(parse_speed_bin_label("95 -> 90 km/h"), (95.0, 90.0))
        self.assertEqual(parse_speed_bin_label("60–50"), (60.0, 50.0))
        self.assertIsNone(parse_speed_bin_label("unnamed_col_0"))

    def test_required_subintervals_follow_configured_step(self):
        self.assertEqual(
            required_subintervals(90.0, 70.0, 5.0),
            [(90.0, 85.0), (85.0, 80.0), (80.0, 75.0), (75.0, 70.0)],
        )
        self.assertEqual(
            required_subintervals(100.0, 80.0, 10.0),
            [(100.0, 90.0), (90.0, 80.0)],
        )

    def test_parser_extracts_exact_bins_with_ten_kmh_step(self):
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }
        run_data = {
            "times": [0.0, 4.0, 9.0, 15.0, 22.0, 30.0, 39.0],
            "velocities": [100.0, 90.0, 80.0, 70.0, 60.0, 50.0, 40.0],
            "heading": "+",
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "combined_10_kmh.csv",
                    "role": "full_or_combined",
                    "all_run_data": {1: run_data},
                }
            ],
            config,
        )

        self.assertEqual(parsed["warnings"], [])
        self.assertEqual(parsed["high"][0]["subintervals"], ["100-90", "90-80"])
        self.assertEqual(parsed["high"][0]["delta_t_s"], 9.0)
        self.assertEqual(parsed["high"][0]["step_kmh"], 10.0)
        self.assertEqual(parsed["low"][0]["subintervals"], ["60-50", "50-40"])
        self.assertEqual(parsed["low"][0]["delta_t_s"], 17.0)

    def test_labeled_vbox_loader_and_parser_support_speed_above_ninety(self):
        runs = self._load_labeled_vbox(["100-90", "90-80"], [4.0, 5.0])
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [{"filename": "high_100.csv", "role": "high", "all_run_data": runs}],
            config,
        )

        self.assertEqual(len(parsed["high"]), 1)
        self.assertEqual(parsed["high"][0]["subintervals"], ["100-90", "90-80"])
        self.assertEqual(parsed["high"][0]["delta_t_s"], 9.0)
        self.assertEqual(parsed["low"], [])

    def test_parser_supports_high_ninety_five_to_seventy_five(self):
        runs = self._load_labeled_vbox(
            ["95-90", "90-85", "85-80", "80-75"],
            [1.0, 2.0, 3.0, 4.0],
        )
        config = {
            "step_kmh": 5.0,
            "high": {"start": 95.0, "end": 75.0, "reference": 85.0},
            "low": {"start": 45.0, "end": 35.0, "reference": 40.0},
        }

        parsed = parse_split_sources(
            [{"filename": "high_95.csv", "role": "high", "all_run_data": runs}],
            config,
        )

        self.assertEqual(parsed["high"][0]["subintervals"], [
            "95-90",
            "90-85",
            "85-80",
            "80-75",
        ])
        self.assertEqual(parsed["high"][0]["delta_t_s"], 10.0)

    def test_parser_supports_low_sixty_to_forty(self):
        runs = self._load_labeled_vbox(["60-50", "50-40"], [7.0, 8.0])
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [{"filename": "low_60.csv", "role": "low", "all_run_data": runs}],
            config,
        )

        self.assertEqual(parsed["high"], [])
        self.assertEqual(parsed["low"][0]["subintervals"], ["60-50", "50-40"])
        self.assertEqual(parsed["low"][0]["delta_t_s"], 15.0)

    def test_unlabeled_separate_file_uses_role_and_current_configuration(self):
        run_data = {
            "interval_measurements": [
                {"column": "unnamed_col_0", "label": "", "time_s": 4.0},
                {"column": "unnamed_col_1", "label": "", "time_s": 5.0},
                {"column": "unnamed_col_2", "label": "", "time_s": 6.0},
            ],
            "heading": "+",
        }
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "unlabeled_high.csv",
                    "role": "high",
                    "all_run_data": {1: run_data},
                }
            ],
            config,
        )

        self.assertEqual(parsed["high"][0]["subintervals"], ["100-90", "90-80"])
        self.assertEqual(parsed["high"][0]["delta_t_s"], 9.0)
        self.assertEqual(parsed["low"], [])

    def test_combined_labeled_file_extracts_high_and_low(self):
        runs = self._load_labeled_vbox(
            ["100-90", "90-80", "60-50", "50-40"],
            [4.0, 5.0, 7.0, 8.0],
        )
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "combined.csv",
                    "role": "full_or_combined",
                    "all_run_data": runs,
                }
            ],
            config,
        )

        self.assertEqual(parsed["high"][0]["subintervals"], ["100-90", "90-80"])
        self.assertEqual(parsed["low"][0]["subintervals"], ["60-50", "50-40"])

    def test_combined_unlabeled_file_is_blocked_without_positional_guess(self):
        run_data = {
            "interval_measurements": [
                {"column": "unnamed_col_0", "label": "", "time_s": 4.0},
                {"column": "unnamed_col_1", "label": "", "time_s": 5.0},
                {"column": "unnamed_col_2", "label": "", "time_s": 7.0},
                {"column": "unnamed_col_3", "label": "", "time_s": 8.0},
            ],
            "heading": "+",
        }
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "combined_unlabeled.csv",
                    "role": "full_or_combined",
                    "all_run_data": {1: run_data},
                }
            ],
            config,
        )

        self.assertEqual(parsed["high"], [])
        self.assertEqual(parsed["low"], [])
        self.assertTrue(
            any(
                "Combined input has no identifiable speed-bin labels."
                in warning
                for warning in parsed["warnings"]
            )
        )

    def test_missing_bin_warning_lists_expected_found_and_missing(self):
        runs = self._load_labeled_vbox(["100-90"], [4.0])
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [{"filename": "missing.csv", "role": "high", "all_run_data": runs}],
            config,
        )

        detail = next(
            warning
            for warning in parsed["warnings"]
            if warning.startswith("missing.csv run 1 high:")
        )
        self.assertIn("expected bins [100-90, 90-80]", detail)
        self.assertIn("found [100-90]", detail)
        self.assertIn("missing [90-80]", detail)

    def test_high_only_arbitrary_interval_does_not_create_false_low(self):
        runs = self._load_labeled_vbox(["100-90", "90-80"], [4.0, 5.0])
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        parsed = parse_split_sources(
            [{"filename": "high_only.csv", "role": "high", "all_run_data": runs}],
            config,
        )

        self.assertEqual(len(parsed["high"]), 1)
        self.assertEqual(parsed["low"], [])

    def test_parser_rejects_contiguous_bins_with_wrong_step(self):
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 80.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }
        five_kmh_run = {
            "times": [0.0, 1.0, 2.0, 3.0, 4.0],
            "velocities": [100.0, 95.0, 90.0, 85.0, 80.0],
            "heading": "+",
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "high_5_kmh.csv",
                    "role": "high",
                    "all_run_data": {1: five_kmh_run},
                }
            ],
            config,
        )

        self.assertEqual(parsed["high"], [])
        self.assertIn("No high-speed Split interval was found.", parsed["warnings"])

    def test_incompatible_interval_span_blocks_parsing(self):
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "end": 85.0, "reference": 90.0},
            "low": {"start": 60.0, "end": 40.0, "reference": 50.0},
        }

        issues = validate_split_interval_config(config)
        parsed = parse_split_sources(
            [{"filename": "unused.csv", "role": "high", "all_run_data": {}}],
            config,
        )

        self.assertEqual([issue["code"] for issue in issues], ["incompatible_step"])
        self.assertEqual(parsed["high"], [])
        self.assertEqual(parsed["low"], [])
        self.assertIn("must be an exact multiple", parsed["warnings"][0])

    def test_non_positive_step_blocks_parsing(self):
        config = default_split_interval_config()
        config["step_kmh"] = 0.0

        issues = validate_split_interval_config(config)
        parsed = parse_split_sources([], config)

        self.assertEqual([issue["code"] for issue in issues], ["invalid_step"])
        self.assertEqual(
            parsed["warnings"],
            ["Coastdown interval step must be greater than zero."],
        )

    def test_config_change_invalidates_all_dependent_state(self):
        old_config = default_split_interval_config()
        new_config = default_split_interval_config()
        new_config["step_kmh"] = 10.0
        test_data = {
            "split_interval_config": old_config,
            "split_parsed_runs": {"high": [{"run_id": 1}]},
            "split_results": [{"F0_mean": 100.0}],
            "split_last_calculated_result": {"F0_mean": 100.0},
            "split_comparison_pairs": [{"id": "pair-1"}],
            "split_final_results": {"num_results": 1},
            "excel_buffer": b"old",
            "split_input_version": 3,
        }

        changed = update_split_interval_config(test_data, new_config)

        self.assertTrue(changed)
        self.assertEqual(test_data["split_interval_config"]["step_kmh"], 10.0)
        self.assertEqual(test_data["split_parsed_runs"], {})
        self.assertEqual(test_data["split_results"], [])
        self.assertIsNone(test_data["split_last_calculated_result"])
        self.assertEqual(test_data["split_comparison_pairs"], [])
        self.assertNotIn("split_final_results", test_data)
        self.assertIsNone(test_data["excel_buffer"])
        self.assertEqual(test_data["split_input_version"], 4)

    def test_unchanged_config_does_not_invalidate_state(self):
        config = default_split_interval_config()
        test_data = {
            "split_interval_config": config,
            "split_results": [{"F0_mean": 100.0}],
            "split_input_version": 3,
        }

        changed = update_split_interval_config(test_data, config)

        self.assertFalse(changed)
        self.assertEqual(test_data["split_results"], [{"F0_mean": 100.0}])
        self.assertEqual(test_data["split_input_version"], 3)

    def test_editing_interval_config_marks_parse_dirty_without_parsing(self):
        processed_config = default_split_interval_config()
        draft_config = default_split_interval_config()
        draft_config["high"]["start"] = 95.0
        test_data = {
            "split_interval_config": processed_config,
            "split_interval_draft_config": processed_config,
            "split_parsed_runs": {"high": [{"run_id": 1}], "low": [{"run_id": 2}]},
            "split_results": [{"F0_mean": 100.0}],
            "split_parse_dirty": False,
            "split_parse_feedback_current": True,
            "split_parse_validation_issues": [{"code": "old"}],
            "split_input_version": 3,
        }

        changed = update_split_interval_draft(test_data, draft_config)

        self.assertTrue(changed)
        self.assertTrue(test_data["split_parse_dirty"])
        self.assertFalse(should_show_split_parse_details(test_data))
        self.assertFalse(split_parse_is_current(test_data))
        self.assertEqual(
            test_data["split_interval_config"],
            processed_config,
        )
        self.assertEqual(test_data["split_parsed_runs"]["high"][0]["run_id"], 1)
        self.assertEqual(test_data["split_results"], [{"F0_mean": 100.0}])
        self.assertEqual(test_data["split_input_version"], 3)
        self.assertEqual(test_data["split_parse_validation_issues"], [])

    def test_parser_review_uses_only_processed_config_and_runs(self):
        processed_config = default_split_interval_config()
        parsed_runs = {
            "high": [
                {
                    "run_id": 1,
                    "start_kmh": 90.0,
                    "end_kmh": 70.0,
                }
            ],
            "low": [],
        }
        test_data = {
            "split_interval_config": processed_config,
            "split_interval_draft_config": processed_config,
            "split_parsed_runs": parsed_runs,
            "split_processed_at": "2026-06-10T12:00:00+00:00",
            "split_parse_dirty": False,
        }
        edited_draft = default_split_interval_config()
        edited_draft["high"]["start"] = 100.0

        update_split_interval_draft(test_data, edited_draft)
        review = get_processed_split_review_state(test_data)

        self.assertEqual(review["config"]["high"]["start"], 90.0)
        self.assertEqual(review["parsed_runs"]["high"][0]["start_kmh"], 90.0)
        self.assertEqual(
            review["processed_at"],
            "2026-06-10T12:00:00+00:00",
        )
        self.assertTrue(test_data["split_parse_dirty"])

    def test_explicit_processing_commits_config_and_clears_dirty_state(self):
        config = default_split_interval_config()
        config["high"]["start"] = 100.0
        config["high"]["reference"] = 90.0
        config["high"]["end"] = 80.0
        parsed_runs = {
            "high": [{"run_id": 10}],
            "low": [{"run_id": 20}],
            "warnings": [],
        }
        test_data = {
            "split_interval_config": default_split_interval_config(),
            "split_interval_draft_config": config,
            "split_parsed_runs": {"high": [{"run_id": 1}]},
            "split_results": [{"F0_mean": 100.0}],
            "split_last_calculated_result": {"F0_mean": 100.0},
            "split_comparison_pairs": [{"id": "pair-1"}],
            "split_final_results": {"num_results": 1},
            "excel_buffer": b"old",
            "split_parse_dirty": True,
            "split_input_version": 3,
        }

        store_processed_split_intervals(
            test_data,
            config,
            parsed_runs,
            processed_at="2026-06-10T13:00:00+00:00",
        )

        self.assertFalse(test_data["split_parse_dirty"])
        self.assertTrue(split_parse_is_current(test_data))
        self.assertTrue(should_show_split_parse_details(test_data))
        self.assertEqual(test_data["split_interval_config"], config)
        self.assertEqual(test_data["split_interval_draft_config"], config)
        self.assertEqual(test_data["split_parsed_runs"], parsed_runs)
        self.assertEqual(
            test_data["split_processed_at"],
            "2026-06-10T13:00:00+00:00",
        )
        self.assertEqual(test_data["split_results"], [])
        self.assertIsNone(test_data["split_last_calculated_result"])
        self.assertEqual(test_data["split_comparison_pairs"], [])
        self.assertNotIn("split_final_results", test_data)
        self.assertIsNone(test_data["excel_buffer"])
        self.assertEqual(test_data["split_input_version"], 4)

    def test_detailed_validation_feedback_only_appears_after_processing(self):
        config = default_split_interval_config()
        test_data = {
            "split_interval_config": config,
            "split_interval_draft_config": config,
            "split_parse_dirty": False,
            "split_parse_feedback_current": True,
        }
        edited_config = default_split_interval_config()
        edited_config["step_kmh"] = 0.0

        update_split_interval_draft(test_data, edited_config)

        self.assertFalse(should_show_split_parse_details(test_data))
        record_split_parse_failure(
            test_data,
            [{"code": "invalid_step"}],
        )
        self.assertTrue(test_data["split_parse_dirty"])
        self.assertTrue(should_show_split_parse_details(test_data))
        self.assertEqual(
            test_data["split_parse_validation_issues"],
            [{"code": "invalid_step"}],
        )

    def test_calculation_guard_rejects_dirty_parse(self):
        self.assertFalse(split_parse_is_current({"split_parse_dirty": True}))
        self.assertTrue(split_parse_is_current({"split_parse_dirty": False}))


if __name__ == "__main__":
    unittest.main()

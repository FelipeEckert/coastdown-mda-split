# coding: utf-8
"""Tests for UI-neutral formatting helpers used by Split auto-selection."""

import inspect
import unittest
from copy import deepcopy
from contextlib import nullcontext
from unittest.mock import Mock, patch

from pages.page_split_auto_selection import (
    _candidate_run_time_label,
    _candidate_rows,
    _candidate_table,
    _build_selection_state,
    _default_constraint_search_pool_size,
    _format_candidate_display_value,
    _pending_from_fallback_offer,
    _pending_has_constraint_warning,
    _render_execution_result,
    _render_fallback_offer,
    _render_generation_diagnostics,
    _render_constraint_validation,
    _render_selection_diagnostics,
    _replace_dialog_state_is_valid,
    _replacement_constraint_preview,
    _render_search_diagnostics,
    _search_diagnostic_values,
    _time_status_label,
    render,
)
from translations import get_translator


class SplitAutoSelectionPageTest(unittest.TestCase):
    def setUp(self):
        self.t = get_translator("en")

    @staticmethod
    def _norm_candidate(identifier, high_minus=20.2):
        run_base = ord(identifier[0]) * 10
        return {
            "id": identifier,
            "F0_mean": 100.0,
            "F2_mean": 0.004,
            "high_plus_delta_t_s": 20.0,
            "high_minus_delta_t_s": high_minus,
            "low_plus_delta_t_s": 10.0,
            "low_minus_delta_t_s": 10.2,
            "run_usage": (
                ("high", "+", run_base),
                ("low", "+", run_base + 1),
                ("high", "-", run_base + 2),
                ("low", "-", run_base + 3),
            ),
        }

    @staticmethod
    def _selection_metadata(*, satisfied, validation, fallback=None, enabled=True):
        constraints = {
            "time_cv": enabled,
            "opposite_time_difference": enabled,
        }
        return {
            "algorithm": "energy",
            "selected_count": 2 if satisfied else 0,
            "constraints_enabled": constraints,
            "constraints_satisfied": satisfied,
            "constraint_validation": validation,
            "constraint_warnings": validation.get("warnings") or [],
            "selection": {
                "strategy": "constraint_first_v2" if enabled else None,
                "evaluated_sets_count": 12,
                "valid_sets_found": 2 if satisfied else 0,
                "search_pool_size": 250,
                "max_set_evaluations_reached": False,
                "elapsed_seconds": 1.25,
                "max_search_seconds": 30.0,
                "timeout_reached": False,
                "fallback_candidates": fallback or [],
            },
        }

    def test_render_has_only_two_default_enabled_time_constraint_checkboxes(self):
        source = inspect.getsource(render)
        for key in (
            "split_auto_require_time_cv",
            "split_auto_require_opposite_difference",
        ):
            self.assertIn(f'key="{key}"', source)
            key_position = source.index(f'key="{key}"')
            self.assertIn("value=True", source[key_position - 100:key_position])
        self.assertNotIn("split_auto_require_coefficient_cv", source)

    def test_render_exposes_advanced_v2_search_controls(self):
        source = inspect.getsource(render)

        for key in (
            "split_auto_search_pool_size",
            "split_auto_search_max_set_evaluations",
            "split_auto_search_max_seconds",
        ):
            self.assertIn(f'key="{key}"', source)
        self.assertIn("search_pool_size=search_pool_size", source)
        self.assertIn("max_set_evaluations=max_set_evaluations", source)
        self.assertIn("max_search_seconds=max_search_seconds", source)

    def test_v2_search_defaults_follow_k(self):
        self.assertEqual(_default_constraint_search_pool_size(1), 80)
        self.assertEqual(_default_constraint_search_pool_size(4), 80)
        self.assertEqual(_default_constraint_search_pool_size(5), 100)

    def test_search_diagnostic_exposes_v2_strategy_and_counts(self):
        metadata = {
            "selection": {
                "strategy": "constraint_first_v2",
                "evaluated_sets_count": 123,
                "valid_sets_found": 4,
                "search_pool_size": 250,
                "max_set_evaluations_reached": True,
                "elapsed_seconds": 30.4,
                "max_search_seconds": 30.0,
                "timeout_reached": True,
            }
        }
        columns = [Mock() for _ in range(8)]
        with patch("pages.page_split_auto_selection.st") as streamlit:
            streamlit.columns.side_effect = (columns[:4], columns[4:])
            _render_search_diagnostics(metadata, self.t)

        self.assertCountEqual(
            [column.metric.call_args.args for column in columns],
            [
                (self.t("split_auto_search_evaluated_sets"), "123"),
                (self.t("split_auto_search_valid_sets"), "4"),
                (self.t("split_auto_search_pool"), "250"),
                (
                    self.t("split_auto_search_strategy"),
                    self.t("split_auto_search_strategy_constraint_first"),
                ),
                (self.t("split_auto_search_elapsed_seconds"), "30.40"),
                (self.t("split_auto_search_time_limit"), "30.0"),
                (
                    self.t("split_auto_search_timeout_status"),
                    self.t("split_auto_yes"),
                ),
                (
                    self.t("split_auto_search_evaluation_limit_status"),
                    self.t("split_auto_yes"),
                ),
            ],
        )
        streamlit.warning.assert_called_once_with(
            self.t("split_auto_search_limited_warning")
        )

    def test_search_diagnostic_is_absent_for_legacy_top_k(self):
        self.assertIsNone(
            _search_diagnostic_values({"selection": {"requested_k": 2}})
        )

    def test_limited_search_messages_are_not_absolute(self):
        translate = get_translator("pt")
        no_valid = translate("split_auto_constraints_no_valid_set")
        limited = translate("split_auto_search_limited_warning")

        self.assertIn("dentro dos limites de busca configurados", no_valid)
        self.assertIn("pode haver combinações válidas", limited.lower())

    def test_progress_reserves_completion_for_after_constrained_search(self):
        source = inspect.getsource(render)

        self.assertIn("generation_progress * 0.50", source)
        self.assertIn('"searching": (0.65', source)
        self.assertIn('"finalizing": (0.95', source)
        self.assertLess(
            source.index("progress.progress(1.0)"),
            source.index("ranked_pool = list"),
        )

    def test_approved_set_builds_pending_with_constraint_validation(self):
        candidates = [self._norm_candidate("a"), self._norm_candidate("b")]
        from core.split_candidate_set_validation import validate_split_candidate_set
        validation = validate_split_candidate_set(candidates)
        metadata = self._selection_metadata(
            satisfied=True,
            validation=validation,
        )

        pending, offer = _build_selection_state(
            algorithm="energy", candidates=candidates, ranked_pool=[],
            metadata=metadata, avoid_repeated_runs=True,
            target_f0=None, target_f2=None, ambient_mode="fixed",
            weather_metadata=None,
        )

        self.assertIsNone(offer)
        self.assertTrue(pending["constraints_satisfied"])
        self.assertIs(pending["constraint_validation"], validation)
        self.assertFalse(pending["fallback_used"])

    def test_failed_set_creates_offer_without_pending(self):
        fallback = [
            self._norm_candidate("a", high_minus=30.0),
            self._norm_candidate("b", high_minus=30.1),
        ]
        from core.split_candidate_set_validation import validate_split_candidate_set
        validation = validate_split_candidate_set(fallback)
        metadata = self._selection_metadata(
            satisfied=False,
            validation=validation,
            fallback=fallback,
        )

        pending, offer = _build_selection_state(
            algorithm="energy", candidates=[], ranked_pool=[],
            metadata=metadata, avoid_repeated_runs=True,
            target_f0=None, target_f2=None, ambient_mode="fixed",
            weather_metadata=None,
        )

        self.assertIsNone(pending)
        self.assertTrue(offer["awaiting_fallback_confirmation"])
        self.assertFalse(offer["fallback_used"])
        self.assertIs(offer["constraint_validation"], validation)
        self.assertEqual(
            offer["metadata"]["selection"]["strategy"],
            "constraint_first_v2",
        )

    def test_confirmed_fallback_becomes_pending_and_warns_cards(self):
        offer = {
            "candidates": [self._norm_candidate("a")],
            "metadata": {"selected_count": 0},
            "constraints_enabled": {
                "time_cv": True,
                "opposite_time_difference": True,
            },
            "constraints_satisfied": False,
            "fallback_used": False,
            "awaiting_fallback_confirmation": True,
        }

        pending = _pending_from_fallback_offer(offer)

        self.assertTrue(pending["fallback_used"])
        self.assertFalse(pending["constraints_satisfied"])
        self.assertFalse(pending["awaiting_fallback_confirmation"])
        self.assertEqual(pending["metadata"]["selected_count"], 1)
        self.assertTrue(_pending_has_constraint_warning(pending))

    def test_replacement_preview_reports_current_and_next_constraint_status(self):
        candidates = [
            self._norm_candidate("a", high_minus=30.0),
            self._norm_candidate("b", high_minus=30.1),
        ]
        pending = {
            "candidates": candidates,
            "constraints_enabled": {
                "time_cv": True,
                "opposite_time_difference": True,
            },
        }

        preview = _replacement_constraint_preview(
            pending,
            0,
            self._norm_candidate("c", high_minus=20.2),
        )

        self.assertFalse(preview["current_status"])
        self.assertFalse(preview["next_status"])
        self.assertIsInstance(preview["next_validation"], dict)

    def test_pending_strips_legacy_coefficient_constraint(self):
        candidate = self._norm_candidate("a")
        metadata = self._selection_metadata(
            satisfied=True,
            validation={},
        )
        metadata["constraints_enabled"]["coefficient_cv"] = True

        pending, _ = _build_selection_state(
            algorithm="energy", candidates=[candidate], ranked_pool=[],
            metadata=metadata, avoid_repeated_runs=True,
            target_f0=None, target_f2=None, ambient_mode="fixed",
            weather_metadata=None,
        )

        self.assertEqual(
            pending["constraints_enabled"],
            {"time_cv": True, "opposite_time_difference": True},
        )

    def test_normative_constraint_diagnostic_omits_coefficient_cv(self):
        validation = {
            "cv_f0_pct": 97.0,
            "cv_f2_pct": 98.0,
            "time_group_results": {
                "high_plus": {"cv_pct": 1.0},
                "high_minus": {"cv_pct": 2.0},
                "low_plus": {"cv_pct": 3.0},
                "low_minus": {"cv_pct": 4.0},
            },
            "opposite_time_results": {
                "high": {"diff_pct": 5.0},
                "low": {"diff_pct": 6.0},
            },
        }
        with patch("pages.page_split_auto_selection.st") as streamlit:
            streamlit.expander.return_value = nullcontext()
            _render_constraint_validation(validation, self.t)

        table = streamlit.dataframe.call_args.args[0]
        self.assertCountEqual(
            table[self.t("split_auto_time_value")].tolist(),
            ["1.00", "2.00", "3.00", "4.00", "5.00", "6.00"],
        )
        self.assertEqual(len(table), 6)

    def test_disabled_constraints_keep_legacy_pending_flow(self):
        candidate = self._norm_candidate("a")
        metadata = self._selection_metadata(
            satisfied=None,
            validation={},
            enabled=False,
        )

        pending, offer = _build_selection_state(
            algorithm="energy", candidates=[candidate], ranked_pool=[],
            metadata=metadata, avoid_repeated_runs=True,
            target_f0=None, target_f2=None, ambient_mode="fixed",
            weather_metadata=None,
        )

        self.assertIsNone(offer)
        self.assertEqual(pending["candidates"], [candidate])
        self.assertFalse(pending["fallback_used"])

    def test_candidate_rows_use_public_pair_label(self):
        rows = _candidate_rows(
            [
                {
                    "high_plus_run": 1,
                    "low_plus_run": 2,
                    "high_minus_run": 3,
                    "low_minus_run": 4,
                    "F0_mean": 100.0,
                    "F2_mean": 0.004,
                    "energy": 1.5,
                    "F0_plus": 99.0,
                    "F0_minus": 101.0,
                    "F2_plus": 0.0039,
                    "F2_minus": 0.0041,
                }
            ],
            "energy",
            self.t,
        )

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[2][self.t("split_pair")],
            "[+]: Run 1 / Run 2 | [-]: Run 3 / Run 4",
        )
        self.assertEqual(rows[0]["F0 [N]"], 99.0)
        self.assertEqual(rows[2]["F0 [N]"], 100.0)
        self.assertIn(self.t("split_auto_cv_f0_diagnostic"), rows[2])
        self.assertIn(self.t("split_auto_cv_f2_diagnostic"), rows[2])
        self.assertIsNone(rows[2][self.t("split_auto_target_score")])
        self.assertTrue(rows[2]["_is_average"])
        self.assertEqual(
            list(rows[2])[-2:],
            [self.t("split_energy_with_unit"), "_is_average"],
        )

    def test_target_candidate_rows_include_score(self):
        rows = _candidate_rows(
            [
                {
                    "high_plus_run": 1,
                    "low_plus_run": 2,
                    "high_minus_run": 3,
                    "low_minus_run": 4,
                    "target_score": 0.25,
                }
            ],
            "target",
            self.t,
        )

        self.assertEqual(rows[2][self.t("split_auto_target_score")], 0.25)

    def test_candidate_display_value_replaces_visual_missing_values(self):
        for value in (None, float("nan"), "nan", "N/A", "None", ""):
            self.assertEqual(_format_candidate_display_value(value, 2), "-")
        self.assertEqual(_format_candidate_display_value(1.23456, 4), "1.2346")

    def test_candidate_run_time_label_uses_time_fallbacks(self):
        candidate = {
            "high_plus_run": 5,
            "high_plus_delta_t_s": 26.214,
            "low_plus_run": 11,
            "time_components": {"low_plus": {"delta_t_s": 12.3}},
            "high_minus": {"run_id": 7, "delta_t_s": 27.456},
            "low_minus_run": 13,
        }

        self.assertEqual(
            _candidate_run_time_label(candidate, "high_plus"),
            "Run 5 | dt = 26.21 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "low_plus"),
            "Run 11 | dt = 12.30 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "high_minus"),
            "Run 7 | dt = 27.46 s",
        )
        self.assertEqual(
            _candidate_run_time_label(candidate, "low_minus"),
            "Run 13 | dt = -",
        )
        self.assertEqual(
            _candidate_run_time_label({}, "high_plus"),
            "Run - | dt = -",
        )

    def test_candidate_table_has_three_rows_and_energy_as_last_column(self):
        candidate = {
            "high_plus_run": 1,
            "low_plus_run": 2,
            "high_minus_run": 3,
            "low_minus_run": 4,
            "F0_plus": 99.0,
            "F0_minus": 101.0,
            "F0_mean": 100.0,
            "F2_plus": 0.0039,
            "F2_minus": 0.0041,
            "F2_mean": 0.004,
            "energy": 1.5,
        }
        original = deepcopy(candidate)

        table = _candidate_table(candidate, "energy", self.t).data

        self.assertEqual(len(table), 3)
        self.assertEqual(table.columns[-1], self.t("split_energy_with_unit"))
        self.assertNotIn(self.t("split_pair"), table.columns)
        self.assertEqual(table.iloc[2][self.t("split_auto_high_run")], "-")
        self.assertEqual(candidate, original)
        self.assertIn(
            "background-color: rgba(209,255,189,0.18)",
            _candidate_table(candidate, "energy", self.t).to_html(),
        )

    def test_fixed_candidate_table_displays_missing_wind_as_dash(self):
        candidate = {
            "high_plus_run": 1, "low_plus_run": 2,
            "high_minus_run": 3, "low_minus_run": 4,
            "temp_plus_used": 20.0, "temp_minus_used": 20.0,
            "press_plus_used": 101.325, "press_minus_used": 101.325,
            "weather_summary": {
                "mode": "fixed", "status": "fixed",
                "temperature_c_mean": 20.0,
                "pressure_kpa_mean": 101.325,
                "wind_speed_mps_max": None,
                "warnings": [],
            },
        }

        table = _candidate_table(candidate, "energy", self.t).data
        self.assertTrue(all(value == "-" for value in table[self.t("split_auto_wind")]))

    def test_replace_dialog_state_requires_live_actionable_request(self):
        pending = {
            "candidates": [{"id": "candidate"}],
            "merge_metadata": None,
            "pool_strategy": "balanced_v2",
        }
        request = {"index": 0}

        self.assertTrue(
            _replace_dialog_state_is_valid(pending, request, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(None, request, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(pending, request, False)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(pending, None, True)
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(
                {**pending, "merge_metadata": {}},
                request,
                True,
            )
        )
        self.assertFalse(
            _replace_dialog_state_is_valid(
                {**pending, "pool_strategy": "legacy"},
                request,
                True,
            )
        )

    def test_generation_diagnostics_render_counts_and_prefilter_per_group(self):
        metadata = {
            "generated_count": 12,
            "failed_count": 3,
            "prefilter_applied": True,
            "prefilter": {
                "high_plus": {
                    "input_count": 10,
                    "output_count": 8,
                    "filtered_count": 2,
                },
                "low_minus": {
                    "input_count": 9,
                    "output_count": 7,
                    "filtered_count": 2,
                },
            },
        }
        columns = [Mock(), Mock()]
        with patch("pages.page_split_auto_selection.st") as streamlit:
            streamlit.columns.return_value = columns
            _render_generation_diagnostics(metadata, self.t)

        self.assertCountEqual(
            [column.metric.call_args.args for column in columns],
            [
                (self.t("split_auto_generated_count"), "12"),
                (self.t("split_auto_diagnostics_failed_count"), "3"),
            ],
        )
        self.assertIn(
            self.t("split_auto_diagnostics_prefilter_enabled"),
            streamlit.write.call_args.args[0],
        )
        table = streamlit.dataframe.call_args.args[0]
        count_columns = [
            self.t("split_auto_prefilter_input"),
            self.t("split_auto_prefilter_output"),
            self.t("split_auto_prefilter_filtered"),
        ]
        self.assertCountEqual(
            list(table[count_columns].itertuples(index=False, name=None)),
            [(10, 8, 2), (9, 7, 2)],
        )

    def test_generation_diagnostics_render_disabled_prefilter(self):
        columns = [Mock(), Mock()]
        with patch("pages.page_split_auto_selection.st") as streamlit:
            streamlit.columns.return_value = columns
            _render_generation_diagnostics(
                {
                    "generated_count": 12,
                    "failed_count": 3,
                    "prefilter_applied": False,
                },
                self.t,
            )

        self.assertCountEqual(
            [column.metric.call_args.args for column in columns],
            [
                (self.t("split_auto_generated_count"), "12"),
                (self.t("split_auto_diagnostics_failed_count"), "3"),
            ],
        )
        self.assertIn(
            self.t("split_auto_diagnostics_prefilter_disabled"),
            streamlit.write.call_args.args[0],
        )
        streamlit.dataframe.assert_not_called()

    def test_selection_diagnostics_wraps_generation_and_search_in_one_expander(self):
        source = inspect.getsource(_render_selection_diagnostics)

        self.assertIn('st.expander(t("split_auto_diagnostics_title")', source)
        self.assertIn("expanded=False", source)
        self.assertIn("_render_generation_diagnostics", source)
        self.assertIn("_render_search_diagnostics", source)
        self.assertIn("split_auto_diagnostics_search_not_applicable", source)

    def test_execution_result_and_fallback_offer_use_selection_diagnostics(self):
        for func in (_render_execution_result, _render_fallback_offer):
            source = inspect.getsource(func)
            self.assertIn("_render_selection_diagnostics", source)

    def test_time_status_labels_cover_three_states(self):
        self.assertEqual(
            _time_status_label(True, self.t),
            self.t("split_auto_time_status_passed"),
        )
        self.assertEqual(
            _time_status_label(False, self.t),
            self.t("split_auto_time_status_failed"),
        )
        self.assertEqual(
            _time_status_label(None, self.t),
            self.t("split_auto_time_status_inconclusive"),
        )


if __name__ == "__main__":
    unittest.main()

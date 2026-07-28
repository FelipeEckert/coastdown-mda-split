# coding: utf-8
"""Tests for unit formatting and on-demand Split workbook generation."""

import unittest
from unittest.mock import MagicMock, Mock, call, patch

from data.split_exporters import (
    build_split_export_signature,
    get_cached_split_export,
)
from pages.page_split_results import (
    _build_consolidated_results_card_html,
    _conformity_status_from_time_validation,
    _display,
    _pair_rows,
    _render_coefficients,
    _render_deviation_summary,
    _render_selected_pairs,
    _render_summary,
    _split_warnings_by_audience,
    is_meteo_sync_warning,
)
from translations import get_translator


class _State(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class SplitResultsFormattingTest(unittest.TestCase):
    def test_results_time_summary_uses_public_configured_speed_labels(self):
        analysis = {
            "coefficient_summary": {"status": "approved", "cv_f0_pct": 3.1, "cv_f2_pct": 4.2},
            "time_summary": {
                "status": "approved",
                "groups": {
                    "high_plus": {
                        "cv_pct": 1.2, "mean": 20.0, "passed": True,
                    },
                    "low_minus": {
                        "cv_pct": 1.4, "mean": 10.0, "passed": True,
                    },
                },
            },
            "weather_summary": {"status": "approved"},
        }
        fake_st = Mock()
        fake_st.columns.return_value = [Mock(), Mock(), Mock()]
        pairs = [{"v2_reference_kmh": 83.0, "v1_reference_kmh": 41.0}]
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_deviation_summary(analysis, pairs, t)

        frame = fake_st.dataframe.call_args.args[0].data
        metric_key = t("split_results_deviation_metric")
        self.assertEqual(
            frame.iloc[0][metric_key], "C.V. Δt — Vel. ref. alta 83 km/h [+]",
        )
        self.assertEqual(
            frame.iloc[3][metric_key], "C.V. Δt — Vel. ref. baixa 41 km/h [-]",
        )
        self.assertNotIn("high_plus", frame.to_string())
        self.assertNotIn("low_minus", frame.to_string())

    def test_deviation_summary_shows_six_normative_time_metrics(self):
        analysis = {
            "coefficient_summary": {"status": "approved", "cv_f0_pct": 3.1, "cv_f2_pct": 4.2},
            "time_summary": {
                "status": "approved",
                "cv_limit_pct": 2.5,
                "opposite_mean_limit_pct": 10.0,
                "groups": {
                    "high_plus": {"cv_pct": 1.2, "mean": 20.0, "passed": True},
                    "high_minus": {"cv_pct": 1.3, "mean": 20.1, "passed": False},
                    "low_plus": {"cv_pct": 1.1, "mean": 10.0, "passed": None},
                    "low_minus": {"cv_pct": 1.4, "mean": 10.1, "passed": True},
                },
                "opposite_direction": {
                    "high": {"diff_pct": 0.5, "passed": True},
                    "low": {"diff_pct": 0.6, "passed": True},
                },
            },
            "weather_summary": {"status": "approved"},
        }
        fake_st = Mock()
        fake_st.columns.return_value = [Mock(), Mock(), Mock()]
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_deviation_summary(analysis, [], t)

        styled_frame = fake_st.dataframe.call_args.args[0]
        frame = styled_frame.data
        self.assertEqual(len(frame), 6)
        status_key = t("split_results_deviation_status")
        status_column = frame.columns.get_loc(status_key)
        styles = styled_frame._compute().ctx
        self.assertTrue(all(column == status_column for _, column in styles))
        self.assertIn(("background-color", "#2DD36F52"), styles[(0, status_column)])
        self.assertIn(("background-color", "#FF6B6B52"), styles[(1, status_column)])
        self.assertNotIn((2, status_column), styles)
        self.assertEqual(
            frame.iloc[0][status_key], t("split_results_status_conforming"),
        )
        self.assertEqual(
            frame.iloc[1][status_key], t("split_results_status_nonconforming"),
        )
        self.assertEqual(
            frame.iloc[2][status_key], t("split_results_status_not_evaluable"),
        )

    def test_validation_section_keeps_both_tables_under_one_heading(self):
        summary = {
            "mean_f0": 100.0, "mean_f2": 0.004, "mean_energy": 0.2,
            "cv_f0": 2.0, "cv_f2": 3.0, "cv_energy": None, "warnings": [],
        }
        analysis = {
            "coefficient_summary": {"cv_f0_pct": 2.0, "cv_f2_pct": 3.0},
            "time_summary": {
                "status": "approved", "groups": {}, "opposite_direction": {},
            },
            "weather_summary": {"status": "failed"},
        }
        fake_st = Mock()
        fake_st.columns.return_value = [Mock(), Mock()]
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_coefficients(summary, t)
            _render_deviation_summary(analysis, [], t)

        fake_st.subheader.assert_called_once_with(
            f":material/fact_check: {t('split_results_validation')}"
        )
        self.assertEqual(fake_st.dataframe.call_count, 2)
        fake_st.metric.assert_not_called()
        self.assertEqual(
            [call.args[0] for call in fake_st.markdown.call_args_list[-2:]],
            [
                f"**{t('split_results_deviation_time_criteria_title')}**",
                f"**{t('split_results_deviation_coefficients_title')}**",
            ],
        )

    def test_deviation_summary_does_not_use_standard_coefficient_wording(self):
        analysis = {
            "coefficient_summary": {"status": "approved", "cv_f0_pct": 12.0, "cv_f2_pct": 4.2},
            "time_summary": {"status": "approved", "groups": {}, "opposite_direction": {}},
            "weather_summary": {"status": "approved"},
        }
        metrics = Mock()
        fake_st = Mock()
        fake_st.container.return_value = metrics
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_deviation_summary(analysis, [], t)

        rendered_texts = (
            [str(call.args[0]) for call in fake_st.markdown.call_args_list]
            + [str(call.args[0]) for call in fake_st.subheader.call_args_list]
            + [str(call.args[0]) for call in metrics.metric.call_args_list]
        )
        self.assertFalse(
            any("CV F0/F2" in text for text in rendered_texts),
            "Standard-style 'CV F0/F2' wording must not appear in deviation analysis.",
        )
        self.assertTrue(
            any(t("split_results_diagnostic_label") in text for text in rendered_texts)
        )

    def test_unit_bearing_headers_have_unitless_values(self):
        pair = {
            "id": "one", "selected": True, "selection_source": "manual",
            "F0_mean": 130.2186, "F2_mean": 0.046123,
            "cv_F0_percent": 2.31, "cv_F2_percent": 3.42,
        }
        row = _pair_rows([pair], get_translator("pt"))[0]
        self.assertEqual(row["F0 (N)"], "130.2186")
        self.assertEqual(row["F2 (N/(km/h)²)"], "0.046123")
        self.assertEqual(row["CV F0 [%]"], "2.31")
        self.assertNotIn("%", row["CV F0 [%]"])

    def test_selected_pair_card_uses_canonical_directional_energy(self):
        pair = {
            "high_plus_run": "HP", "high_plus_delta_t_s": 11.0,
            "low_plus_run": "LP", "low_plus_delta_t_s": 12.0,
            "high_minus_run": "HM", "high_minus_delta_t_s": 13.0,
            "low_minus_run": "LM", "low_minus_delta_t_s": 14.0,
            "F0_plus": 100.12345, "F2_plus": 0.0043219,
            "temp_plus_used": 20.0, "press_plus_used": 101.325,
            "wind_plus_ms": 0.0,
            "F0_minus": 200.0, "F2_minus": 0.005,
            "temp_minus_used": 40.0, "press_minus_used": 99.0,
            "wind_minus_ms": 2.5,
            "F0_mean": 123.4567, "F2_mean": 0.004444,
            "energy": 0.3333, "temp_c": 25.5,
            "baro_kpa": 100.25, "wind_ms": 0.75,
        }
        original = dict(pair)
        fake_st = Mock()
        fake_st.expander.return_value = MagicMock()
        layout = Mock()
        layout.container.return_value = layout
        fake_st.container.return_value = layout
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st), patch(
            "pages.page_split_results.calculate_split_energy",
            side_effect=[{"energy": 0.11119}, {"energy": 0.22229}],
        ) as calculate_energy:
            _render_selected_pairs([pair], t)

        fake_st.expander.assert_called_once_with(
            "[+]: Run HP / Run LP | [-]: Run HM / Run LM",
            expanded=False,
            icon=":material/compare_arrows:",
        )
        fake_st.columns.assert_not_called()
        self.assertEqual(
            calculate_energy.call_args_list,
            [
                call(100.12345, 0.0043219),
                call(200.0, 0.005),
            ],
        )
        rendered_titles = [call.args[0] for call in layout.markdown.call_args_list]
        self.assertIn("**[+] Run HP / Run LP**", rendered_titles)
        self.assertIn("**[-] Run HM / Run LM**", rendered_titles)
        self.assertIn(f"**{t('split_pair_average')}**", rendered_titles)
        metric_values = [call.args[1] for call in layout.metric.call_args_list]
        self.assertIn("0.1112", metric_values)
        self.assertIn("0.2223", metric_values)
        self.assertIn("0.00", metric_values)
        self.assertIn("123.4567", metric_values)
        self.assertIn("0.3333", metric_values)
        self.assertIn("25.5", metric_values)
        self.assertIn("0.75", metric_values)
        self.assertTrue(
            all(call.kwargs.get("border") is True for call in layout.metric.call_args_list)
        )
        self.assertEqual(calculate_energy.call_count, 2)
        self.assertEqual(pair, original)

    def test_display_does_not_add_unit_unless_explicitly_requested(self):
        self.assertEqual(_display(130.2186, 4), "130.2186")
        self.assertEqual(_display(2.31, 2), "2.31")

    def test_export_cache_reuses_payload_and_invalidates_by_signature(self):
        pair = {"id": "one", "selected": True, "F0_mean": 100.0}
        signature = build_split_export_signature(
            final_results={"mean_f0": 100.0}, selected_pairs=[pair],
            vehicle_data={}, deviation_analysis={},
        )
        builder = Mock(return_value=b"xlsx")
        payload, cache, first_hit = get_cached_split_export(signature, None, builder=builder)
        reused, _, second_hit = get_cached_split_export(signature, cache, builder=builder)
        changed = build_split_export_signature(
            final_results={"mean_f0": 101.0}, selected_pairs=[pair],
            vehicle_data={}, deviation_analysis={},
        )
        get_cached_split_export(changed, cache, builder=builder)
        self.assertEqual(payload, reused)
        self.assertFalse(first_hit)
        self.assertTrue(second_hit)
        self.assertEqual(builder.call_count, 2)

    def test_results_render_hides_traceability_and_does_not_generate_excel_without_button(self):
        pair = {"id": "one", "selected": True, "F0_mean": 100.0, "F2_mean": 0.004}
        summary = {"selected_pairs": [pair], "num_pairs": 1}
        fake_st = Mock()
        fake_st.session_state = _State(split_comparison_pairs=[pair])
        fake_st.button.return_value = False
        fake_st.container.return_value = MagicMock()
        analysis = {"coefficient_summary": {}, "time_summary": {}, "weather_summary": {}}
        with patch("pages.page_split_results.st", fake_st), patch(
            "pages.page_split_results.consolidate_split_final_results", return_value=summary
        ), patch(
            "pages.page_split_results.get_cached_split_deviation_analysis",
            return_value=(analysis, {"signature": (), "analysis": analysis}, False),
        ), patch("pages.page_split_results._render_summary"), patch(
            "pages.page_split_results._render_vehicle"
        ), patch("pages.page_split_results._render_coefficients"), patch(
            "pages.page_split_results._render_selected_pairs"
        ), patch("pages.page_split_results._render_deviation_summary"), patch(
            "pages.page_split_results.export_split_final_results_to_excel"
        ) as exporter:
            from pages.page_split_results import render
            render(lambda key: key)
        exporter.assert_not_called()
        fake_st.expander.assert_not_called()

    def test_conformity_status_maps_time_validation_passed(self):
        self.assertEqual(
            _conformity_status_from_time_validation({"passed": True}), "conforming",
        )
        self.assertEqual(
            _conformity_status_from_time_validation({"passed": False}), "nonconforming",
        )
        self.assertEqual(
            _conformity_status_from_time_validation({"passed": None}), "inconclusive",
        )
        self.assertEqual(_conformity_status_from_time_validation(None), "inconclusive")

    def test_consolidated_card_html_reflects_time_validation_status(self):
        t = get_translator("pt")
        summary = {
            "num_pairs": 3,
            "mean_f0": 130.2186,
            "mean_f2": 0.046123,
            "mean_energy": 0.512,
            "cv_f0": 2.31,
            "cv_f2": 3.42,
        }
        approved_html = _build_consolidated_results_card_html(
            summary, {"passed": True}, t,
        )
        self.assertIn("✅", approved_html)
        self.assertIn(t("split_results_status_conforming"), approved_html)
        self.assertIn('style="color:', approved_html)
        self.assertIn(t("split_results_diagnostic_label"), approved_html)
        self.assertNotIn("CV F0/F2", approved_html)
        self.assertIn("background-color: var(--secondary-background-color)", approved_html)
        self.assertIn("font-size: clamp(1.5rem, 3vw, 2rem)", approved_html)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", approved_html)

        failed_html = _build_consolidated_results_card_html(
            summary, {"passed": False}, t,
        )
        self.assertIn("❌", failed_html)
        self.assertIn(t("split_results_status_nonconforming"), failed_html)
        self.assertIn("#f44336", failed_html)

        inconclusive_html = _build_consolidated_results_card_html(
            summary, None, t,
        )
        self.assertIn("⚠️", inconclusive_html)
        self.assertIn(t("split_results_status_inconclusive"), inconclusive_html)
        self.assertIn("#ff9800", inconclusive_html)

    def test_consolidated_card_html_escapes_untrusted_text(self):
        t = get_translator("pt")
        summary = {"num_pairs": "<script>1</script>", "mean_f0": None}
        rendered = _build_consolidated_results_card_html(summary, {"passed": True}, t)
        self.assertNotIn("<script>", rendered)

    def test_render_summary_uses_native_metrics_and_conformity_badge(self):
        fake_st = Mock()
        layout = Mock()
        layout.container.return_value = layout
        fake_st.container.return_value = layout
        t = get_translator("pt")
        summary = {"num_pairs": 1, "mean_f0": 100.0, "mean_f2": 0.004, "mean_energy": 0.2, "cv_f0": None, "cv_f2": None}
        with patch("pages.page_split_results.st", fake_st):
            _render_summary(summary, {"passed": True}, t)
        fake_st.markdown.assert_not_called()
        layout.badge.assert_called_once_with(
            t("split_results_status_conforming"),
            icon=":material/check_circle:",
            color="green",
        )
        metric_labels = [call.args[0] for call in layout.metric.call_args_list]
        self.assertEqual(
            metric_labels,
            [
                t("split_selected_pairs"),
                t("split_results_final_f0"),
                t("split_results_final_f2"),
                t("split_results_mean_energy"),
                f"{t('split_results_cv_f0')} {t('split_results_diagnostic_label')}",
                f"{t('split_results_cv_f2')} {t('split_results_diagnostic_label')}",
            ],
        )

    def test_is_meteo_sync_warning_classifies_technical_notes(self):
        self.assertTrue(is_meteo_sync_warning(
            "The weather date differs from the run date; synchronization used time of day only."
        ))
        self.assertTrue(is_meteo_sync_warning(
            "Multiple weather records were equally close; the first source was selected."
        ))
        self.assertTrue(is_meteo_sync_warning(
            "Weather timezone is not declared; timestamps were compared as local time."
        ))
        self.assertFalse(is_meteo_sync_warning("Pair excluded due to missing F0."))
        self.assertFalse(is_meteo_sync_warning(None))

    def test_split_warnings_by_audience_separates_groups(self):
        warnings = [
            "Pair excluded due to missing F0.",
            "The weather date differs from the run date; synchronization used time of day only.",
            "",
            None,
        ]
        critical, meteo_sync = _split_warnings_by_audience(warnings)
        self.assertEqual(critical, ["Pair excluded due to missing F0."])
        self.assertEqual(
            meteo_sync,
            ["The weather date differs from the run date; synchronization used time of day only."],
        )

    def test_coefficients_section_omits_duplicate_conformity_banner(self):
        t = get_translator("pt")
        summary = {
            "mean_f0": 100.0, "mean_f2": 0.004, "mean_energy": 0.2,
            "cv_f0": 2.0, "cv_f2": 3.0, "cv_energy": None,
            "conformity_status": "conforming", "warnings": [],
        }
        fake_st = Mock()

        with patch("pages.page_split_results.st", fake_st):
            _render_coefficients(summary, t)

        fake_st.success.assert_not_called()
        fake_st.error.assert_not_called()
        fake_st.warning.assert_not_called()
        frame = fake_st.dataframe.call_args.args[0]
        self.assertEqual(
            list(frame.columns),
            ["Coeficiente", "Valor médio", "CV [%]"],
        )
        self.assertTrue(all(
            t("split_results_diagnostic_label") in value
            for value in frame["Coeficiente"].iloc[:2]
        ))
        self.assertEqual(summary["conformity_status"], "conforming")

    def test_coefficients_section_hides_weather_warnings(self):
        summary = {
            "mean_f0": 100.0, "mean_f2": 0.004, "mean_energy": 0.2,
            "cv_f0": 2.0, "cv_f2": 3.0, "cv_energy": None,
            "conformity_status": "conforming",
            "warnings": [
                "Pair excluded due to missing F0.",
                "The weather date differs from the run date; synchronization used time of day only.",
                "high_plus: Weather timezone is not declared; timestamps were compared as local time.",
            ],
        }
        fake_st = Mock()
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_coefficients(summary, t)

        warning_texts = [str(call.args[0]) for call in fake_st.warning.call_args_list]
        self.assertEqual(warning_texts, ["Pair excluded due to missing F0."])
        fake_st.expander.assert_not_called()

    def test_coefficients_section_skips_expander_without_meteo_sync_warnings(self):
        summary = {
            "mean_f0": 100.0, "mean_f2": 0.004, "mean_energy": 0.2,
            "cv_f0": 2.0, "cv_f2": 3.0, "cv_energy": None,
            "conformity_status": "conforming",
            "warnings": [],
        }
        fake_st = Mock()
        t = get_translator("pt")

        with patch("pages.page_split_results.st", fake_st):
            _render_coefficients(summary, t)

        fake_st.expander.assert_not_called()


if __name__ == "__main__":
    unittest.main()

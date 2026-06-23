# coding: utf-8
"""Tests for unit formatting and on-demand Split workbook generation."""

import unittest
from unittest.mock import Mock, patch

from data.split_exporters import (
    build_split_export_signature,
    get_cached_split_export,
)
from pages.page_split_results import (
    _display,
    _pair_rows,
    _render_deviation_summary,
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
            "coefficient_summary": {"status": "approved"},
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

        with patch("pages.page_split_results.st", fake_st):
            _render_deviation_summary(analysis, pairs, get_translator("pt"))

        frame = fake_st.dataframe.call_args.args[0]
        self.assertEqual(frame.iloc[0]["Grupo"], "C.V. Δt — Vel. ref. alta 83 km/h [+]")
        self.assertEqual(frame.iloc[1]["Grupo"], "C.V. Δt — Vel. ref. baixa 41 km/h [-]")
        self.assertNotIn("high_plus", frame.to_string())
        self.assertNotIn("low_minus", frame.to_string())

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

    def test_results_render_does_not_generate_excel_without_button(self):
        pair = {"id": "one", "selected": True, "F0_mean": 100.0, "F2_mean": 0.004}
        summary = {"selected_pairs": [pair], "num_pairs": 1}
        fake_st = Mock()
        fake_st.session_state = _State(split_comparison_pairs=[pair])
        fake_st.button.return_value = False
        analysis = {"coefficient_summary": {}, "time_summary": {}, "weather_summary": {}}
        with patch("pages.page_split_results.st", fake_st), patch(
            "pages.page_split_results.consolidate_split_final_results", return_value=summary
        ), patch(
            "pages.page_split_results.get_cached_split_deviation_analysis",
            return_value=(analysis, {"signature": (), "analysis": analysis}, False),
        ), patch("pages.page_split_results._render_summary"), patch(
            "pages.page_split_results._render_vehicle"
        ), patch("pages.page_split_results._render_coefficients"), patch(
            "pages.page_split_results._pair_rows", return_value=[]
        ), patch("pages.page_split_results._render_deviation_summary"), patch(
            "pages.page_split_results._render_traceability"
        ), patch("pages.page_split_results.export_split_final_results_to_excel") as exporter:
            from pages.page_split_results import render
            render(lambda key: key)
        exporter.assert_not_called()


if __name__ == "__main__":
    unittest.main()

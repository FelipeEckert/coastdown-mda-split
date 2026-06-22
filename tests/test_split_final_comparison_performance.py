# coding: utf-8
"""Behavioral tests for lazy Final Comparison rendering and caches."""

from copy import deepcopy
import unittest
from unittest.mock import Mock, patch

from core.split_deviation_analysis import (
    build_selected_pairs_signature,
    get_cached_split_deviation_analysis,
)
from core.split_state import reset_split_final_outputs
from pages.page_split_final_comparison import _render_selected_section


def _pair():
    return {
        "id": "pair-1", "selected": True,
        "F0_mean": 100.0, "F2_mean": 0.004, "energy": 1.2,
        "high_plus_delta_t_s": 20.0, "low_plus_delta_t_s": 10.0,
        "high_minus_delta_t_s": 20.5, "low_minus_delta_t_s": 10.5,
        "environmental_conditions": {
            "mode": "fixed", "temperature_c": 20.0,
            "pressure_kpa": 101.325, "wind_speed_mps": None,
        },
        "warnings": [],
    }


class SplitFinalComparisonPerformanceTest(unittest.TestCase):
    def test_table_section_does_not_render_deviation_analysis(self):
        with patch("pages.page_split_final_comparison._render_table_tab") as table, patch(
            "pages.page_split_final_comparison._render_deviation_analysis"
        ) as deviation:
            _render_selected_section("table", [_pair()], lambda key: key)

        table.assert_called_once()
        deviation.assert_not_called()

    def test_deviation_section_does_not_render_table(self):
        with patch("pages.page_split_final_comparison._render_table_tab") as table, patch(
            "pages.page_split_final_comparison._render_deviation_analysis"
        ) as deviation:
            _render_selected_section("deviation", [_pair()], lambda key: key)

        deviation.assert_called_once()
        table.assert_not_called()

    def test_analysis_cache_reuses_unchanged_signature(self):
        analyzer = Mock(return_value={"pair_count": 1})
        first, cache, first_hit = get_cached_split_deviation_analysis(
            [_pair()], None, analyzer=analyzer
        )
        second, _, second_hit = get_cached_split_deviation_analysis(
            [deepcopy(_pair())], cache, analyzer=analyzer
        )

        self.assertFalse(first_hit)
        self.assertTrue(second_hit)
        self.assertEqual(first, second)
        analyzer.assert_called_once()

    def test_signature_and_cache_change_with_analysis_input(self):
        first_pair = _pair()
        changed_pair = deepcopy(first_pair)
        changed_pair["high_plus_delta_t_s"] = 21.0
        self.assertNotEqual(
            build_selected_pairs_signature([first_pair]),
            build_selected_pairs_signature([changed_pair]),
        )
        analyzer = Mock(side_effect=[{"version": 1}, {"version": 2}])
        _, cache, _ = get_cached_split_deviation_analysis([first_pair], None, analyzer=analyzer)
        result, _, hit = get_cached_split_deviation_analysis([changed_pair], cache, analyzer=analyzer)
        self.assertFalse(hit)
        self.assertEqual(result["version"], 2)

    def test_final_output_reset_invalidates_analysis_and_excel_caches(self):
        state = {
            "split_final_results": {"old": True}, "excel_buffer": b"old",
            "split_deviation_analysis_cache": {"old": True},
            "split_results_excel_cache": {"old": True},
        }
        reset_split_final_outputs(state)
        self.assertNotIn("split_deviation_analysis_cache", state)
        self.assertNotIn("split_results_excel_cache", state)


if __name__ == "__main__":
    unittest.main()

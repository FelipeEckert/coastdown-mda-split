# coding: utf-8
"""Tests for Split UI display helpers."""

import unittest
from unittest.mock import patch

from core.split_display import (
    format_run_option_label,
    format_split_opposite_time_label,
    format_split_pair_label,
    format_split_time_group_label,
    get_split_reference_speeds,
)
from pages.page_split_coefficient_calculation import (
    _build_uncorrected_results_html,
    _format_cv_cell_class,
    _format_optional_float,
    _format_wind_cell_class,
    _selected_from_group,
    _split_result_direction_label,
)
from translations import get_translator


class SplitDisplayTest(unittest.TestCase):
    def test_formats_normative_time_labels_with_configured_speeds(self):
        self.assertEqual(
            format_split_time_group_label(
                "high_plus", high_reference_speed_kmh=82.5
            ),
            "C.V. Δt — Vel. ref. alta 82.5 km/h [+]",
        )
        self.assertEqual(
            format_split_time_group_label(
                "low_minus", low_reference_speed_kmh=42
            ),
            "C.V. Δt — Vel. ref. baixa 42 km/h [-]",
        )
        self.assertEqual(
            format_split_opposite_time_label(
                "high", high_reference_speed_kmh=82.5
            ),
            "Dif. médias Δt — Vel. ref. alta 82.5 km/h: [+] vs [-]",
        )

    def test_time_labels_have_safe_fallback_without_hardcoded_speeds(self):
        self.assertEqual(
            format_split_time_group_label("low_plus"),
            "C.V. Δt — Vel. ref. baixa [+]",
        )
        self.assertNotIn("80 km/h", format_split_opposite_time_label("high"))
        self.assertNotIn("40 km/h", format_split_opposite_time_label("low"))

    def test_reference_speeds_use_pair_values_and_config_fallback(self):
        self.assertEqual(
            get_split_reference_speeds(
                [{"v2_reference_kmh": 83, "v1_reference_kmh": 41}]
            ),
            (83.0, 41.0),
        )
        self.assertEqual(
            get_split_reference_speeds({
                "split_interval_config": {
                    "high": {"reference": 81},
                    "low": {"reference": 39},
                }
            }),
            (81.0, 39.0),
        )

    def test_formats_complete_pair_from_nested_components(self):
        pair = {
            "id": "split_pair_e4683df9",
            "high_plus": {"run_id": 2},
            "low_plus": {"run_id": 1},
            "high_minus": {"run_id": 1},
            "low_minus": {"run_id": 4},
        }

        self.assertEqual(
            format_split_pair_label(pair),
            "[+]: Run 2 / Run 1 | [-]: Run 1 / Run 4",
        )
        self.assertEqual(pair["id"], "split_pair_e4683df9")

    def test_formats_complete_pair_from_flattened_comparison_fields(self):
        pair = {
            "high_plus_run": 2,
            "low_plus_run": 1,
            "high_minus_run": 1,
            "low_minus_run": 4,
        }

        self.assertEqual(
            format_split_pair_label(pair),
            "[+]: Run 2 / Run 1 | [-]: Run 1 / Run 4",
        )

    def test_formats_incomplete_pair_without_error(self):
        self.assertEqual(
            format_split_pair_label({"high_plus_run": 2}),
            "[+]: Run 2 / Run — | [-]: Run — / Run —",
        )
        self.assertEqual(
            format_split_pair_label(None),
            "[+]: Run — / Run — | [-]: Run — / Run —",
        )

    def test_formats_run_with_delta_time_and_filename(self):
        record = {
            "run_id": 1,
            "delta_t_s": 18.72,
            "filename": "split eliezer high.csv",
            "heading": "+",
            "start_time_str": "18:47:17.147",
        }

        self.assertEqual(
            format_run_option_label(record),
            "Run 1 | dt=18.720s | split eliezer high.csv",
        )
        label = format_run_option_label(record)
        self.assertNotIn("dir +", label)
        self.assertNotIn("18:47:17.147", label)
        self.assertNotIn("start_time", label)

    def test_formats_run_without_delta_time(self):
        self.assertEqual(
            format_run_option_label(
                {"run_id": 3, "filename": "high.csv"}
            ),
            "Run 3 | dt=— | high.csv",
        )

    def test_formats_run_without_filename_or_optional_fields(self):
        self.assertEqual(
            format_run_option_label({"run_id": 4, "delta_t_s": 9}),
            "Run 4 | dt=9.000s | File —",
        )
        self.assertEqual(
            format_run_option_label(None),
            "Run — | dt=— | File —",
        )

    def test_pair_label_never_exposes_internal_id(self):
        label = format_split_pair_label(
            {
                "id": "split_pair_b5b56a2f",
                "high_plus_run": 2,
                "low_plus_run": 1,
                "high_minus_run": 1,
                "low_minus_run": 4,
            }
        )

        self.assertNotIn("split_pair_", label)
        self.assertIn("[+]: Run 2 / Run 1", label)
        self.assertIn("[-]: Run 1 / Run 4", label)

    def test_coefficient_selector_uses_clean_helper_on_original_record(self):
        record = {
            "run_id": 1,
            "delta_t_s": 18.72,
            "filename": "split eliezer high.csv",
            "heading": "+",
            "start_time_str": "18:47:17.147",
        }
        grouped = {"high_plus": [record]}

        with patch(
            "pages.page_split_coefficient_calculation.st.selectbox",
            return_value=record,
        ) as selectbox:
            selected = _selected_from_group(
                grouped,
                "high_plus",
                "High-speed [+]",
                "test",
            )

        self.assertIs(selected, record)
        kwargs = selectbox.call_args.kwargs
        self.assertEqual(kwargs["options"], [record])
        label = kwargs["format_func"](record)
        self.assertEqual(
            label,
            "Run 1 | dt=18.720s | split eliezer high.csv",
        )
        self.assertNotIn("dir +", label)
        self.assertNotIn("18:47:17.147", label)

    def test_split_result_table_format_helpers_handle_missing_values(self):
        self.assertEqual(_format_optional_float(None, 2), "N/A")
        self.assertEqual(_format_optional_float(float("nan"), 2), "N/A")
        self.assertEqual(_format_optional_float(12.3456, 2), "12.35")

    def test_split_result_warning_classes_follow_thresholds(self):
        self.assertEqual(
            _format_cv_cell_class(10.01),
            "split-cv-cell split-warning-cv",
        )
        self.assertEqual(_format_cv_cell_class(10.0), "split-cv-cell")
        self.assertEqual(_format_wind_cell_class(3.01), "split-warning-wind")
        self.assertEqual(_format_wind_cell_class(3.0), "")

    def test_split_result_direction_labels_do_not_expose_internal_id(self):
        result = {
            "id": "split_pair_b5b56a2f",
            "high_plus": {"run_id": 2},
            "low_plus": {"run_id": 1},
            "high_minus": {"run_id": 1},
            "low_minus": {"run_id": 4},
            "f0_prime_plus": 100.0,
            "f2_prime_plus": 0.2,
            "f0_prime_minus": 110.0,
            "f2_prime_minus": 0.22,
            "f0_prime_mean": 105.0,
            "f2_prime_mean": 0.21,
        }

        self.assertEqual(
            _split_result_direction_label(result, "plus"),
            "[+] High Run 2 / Low Run 1",
        )
        self.assertEqual(
            _split_result_direction_label(result, "minus"),
            "[-] High Run 1 / Low Run 4",
        )
        html = _build_uncorrected_results_html(result, get_translator("en"))
        self.assertNotIn("split_pair_", html)
        self.assertIn("[+] High Run 2 / Low Run 1", html)
        self.assertIn("[-] High Run 1 / Low Run 4", html)


if __name__ == "__main__":
    unittest.main()

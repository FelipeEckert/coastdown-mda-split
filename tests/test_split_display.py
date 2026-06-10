# coding: utf-8
"""Tests for Split UI display helpers."""

import unittest
from unittest.mock import patch

from core.split_display import (
    format_run_option_label,
    format_split_pair_label,
)
from pages.page_split_coefficient_calculation import _selected_from_group


class SplitDisplayTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

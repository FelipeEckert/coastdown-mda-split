# coding: utf-8
"""Integration checks for sample_data/Split imports."""

from pathlib import Path
import math
import unittest

from core.split_calculations import calculate_split_result
from core.split_state import (
    clear_split_final_state,
    invalidate_split_ambient_state,
    invalidate_split_input_state,
)
from core.weather_sync import sync_weather_to_run
from data.loaders import carregar_dados_csv_robusto
from data.split_parser import default_split_interval_config, parse_split_sources
from data.weather_loader import read_weather_file


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "Split"


class SplitSampleDataImportTest(unittest.TestCase):
    def test_two_csv_high_low_eliezer_extracts_expected_deltas_and_coefficients(self):
        high_path = SAMPLE_DIR / "coastdown" / "split eliezer high.csv"
        low_path = SAMPLE_DIR / "coastdown" / "split eliezer low.csv"

        _, high_runs, _ = carregar_dados_csv_robusto(
            str(high_path),
            using_split_method=True,
            is_alta=True,
        )
        _, low_runs, _ = carregar_dados_csv_robusto(
            str(low_path),
            using_split_method=True,
            is_alta=False,
        )

        parsed = parse_split_sources(
            [
                {"filename": high_path.name, "role": "high", "all_run_data": high_runs},
                {"filename": low_path.name, "role": "low", "all_run_data": low_runs},
            ],
            default_split_interval_config(),
        )

        high_record = next(record for record in parsed["high"] if record["run_id"] == 1)
        low_record = next(record for record in parsed["low"] if record["run_id"] == 1)
        self.assertTrue(math.isclose(high_record["delta_t_s"], 18.72, rel_tol=1e-12))
        self.assertTrue(math.isclose(low_record["delta_t_s"], 19.58, rel_tol=1e-12))

        result = calculate_split_result(
            high_record,
            low_record,
            1545.0,
            default_split_interval_config(),
        )
        self.assertTrue(math.isclose(result["f0_prime"], 139.41119395239252, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["f2_prime"], 0.6461779091694823, rel_tol=1e-12))

    def test_separate_mode_high_only_csv_reports_missing_low_interval(self):
        high_path = SAMPLE_DIR / "coastdown" / "split eliezer high.csv"
        _, high_runs, _ = carregar_dados_csv_robusto(
            str(high_path),
            using_split_method=True,
            is_alta=True,
        )

        parsed = parse_split_sources(
            [{"filename": high_path.name, "role": "high", "all_run_data": high_runs}],
            default_split_interval_config(),
        )

        self.assertGreater(len(parsed["high"]), 0)
        self.assertEqual(parsed["low"], [])
        self.assertIn("No low-speed Split interval was found.", parsed["warnings"])

    def test_combined_mode_high_only_source_does_not_create_false_low_interval(self):
        high_only_run = {
            "times": [0, 4.23, 8.79, 13.6, 18.72],
            "velocities": [90, 85, 80, 75, 70],
            "heading": "+",
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "same_name.csv",
                    "role": "full_or_combined",
                    "all_run_data": {1: high_only_run},
                }
            ],
            default_split_interval_config(),
        )

        self.assertEqual(len(parsed["high"]), 1)
        self.assertEqual(parsed["low"], [])
        self.assertIn("No low-speed Split interval was found.", parsed["warnings"])

    def test_low_only_csv_in_low_slot_does_not_create_false_high_interval(self):
        low_path = SAMPLE_DIR / "coastdown" / "split eliezer low.csv"
        _, low_runs, _ = carregar_dados_csv_robusto(
            str(low_path),
            using_split_method=True,
            is_alta=False,
        )

        parsed = parse_split_sources(
            [{"filename": low_path.name, "role": "low", "all_run_data": low_runs}],
            default_split_interval_config(),
        )

        self.assertEqual(parsed["high"], [])
        self.assertGreater(len(parsed["low"]), 0)
        self.assertIn("No high-speed Split interval was found.", parsed["warnings"])

    def test_combined_mode_low_only_source_does_not_create_false_high_interval(self):
        low_only_run = {
            "times": [0, 9.44, 19.58],
            "velocities": [45, 40, 35],
            "heading": "+",
        }

        parsed = parse_split_sources(
            [
                {
                    "filename": "combined_low_only.csv",
                    "role": "full_or_combined",
                    "all_run_data": {1: low_only_run},
                }
            ],
            default_split_interval_config(),
        )

        self.assertEqual(parsed["high"], [])
        self.assertEqual(len(parsed["low"]), 1)
        self.assertIn("No high-speed Split interval was found.", parsed["warnings"])

    def test_single_synthetic_full_csv_source_can_extract_high_and_low(self):
        run_data = {
            "times": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "velocities": [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30],
            "heading": "+",
        }

        parsed = parse_split_sources(
            [{"filename": "synthetic_full.csv", "role": "full_or_combined", "all_run_data": {1: run_data}}],
            default_split_interval_config(),
        )

        self.assertEqual(len(parsed["high"]), 1)
        self.assertEqual(len(parsed["low"]), 1)
        self.assertEqual(parsed["high"][0]["delta_t_s"], 4)
        self.assertEqual(parsed["low"][0]["delta_t_s"], 2)

    def test_same_filename_with_different_content_is_not_reused_by_parser(self):
        first_run = {
            "times": [0, 4, 8, 12, 16],
            "velocities": [90, 85, 80, 75, 70],
            "heading": "+",
        }
        second_run = {
            "times": [0, 5, 10, 15, 20],
            "velocities": [90, 85, 80, 75, 70],
            "heading": "+",
        }

        first = parse_split_sources(
            [
                {
                    "filename": "same_name.csv",
                    "content_sha256": "hash-a",
                    "role": "high",
                    "all_run_data": {1: first_run},
                }
            ],
            default_split_interval_config(),
        )
        second = parse_split_sources(
            [
                {
                    "filename": "same_name.csv",
                    "content_sha256": "hash-b",
                    "role": "high",
                    "all_run_data": {1: second_run},
                }
            ],
            default_split_interval_config(),
        )

        self.assertEqual(first["high"][0]["delta_t_s"], 16)
        self.assertEqual(second["high"][0]["delta_t_s"], 20)

    def test_input_mode_change_invalidates_split_derived_state(self):
        test_data = {
            "split_parsed_runs": {"high": [{"run_id": 1}], "low": [{"run_id": 1}]},
            "split_results": [{"f0_prime": 1.0}],
            "split_comparison_pairs": [{"id": "old"}],
            "split_last_calculated_result": {"f0_prime": 1.0},
            "split_final_results": {"num_results": 1},
            "excel_buffer": b"old",
            "split_input_version": 4,
            "sync_meteo_by_time_only": True,
        }

        invalidate_split_input_state(test_data)

        self.assertEqual(test_data["split_parsed_runs"], {})
        self.assertEqual(test_data["split_results"], [])
        self.assertEqual(test_data["split_comparison_pairs"], [])
        self.assertIsNone(test_data["split_last_calculated_result"])
        self.assertEqual(test_data["split_final_results"], {})
        self.assertIsNone(test_data["excel_buffer"])
        self.assertEqual(test_data["split_input_version"], 5)
        self.assertFalse(test_data["sync_meteo_by_time_only"])

    def test_meteo_change_removes_stale_sync_but_preserves_coefficients(self):
        test_data = {
            "split_results": [
                {
                    "f0_prime": 139.4,
                    "f2_prime": 0.646,
                    "ambient_mode": "weather_sync",
                    "weather_sync": {"high_plus": {"matched": True}},
                    "correction_available": True,
                    "corrected_result_plus": {"F0": 140.0},
                    "corrected_result_minus": {"F0": 141.0},
                    "corrected_pair_mean": {"F0": 140.5},
                    "temp_plus_used": 24.0,
                    "press_plus_used": 95.2,
                    "temp_minus_used": 25.0,
                    "press_minus_used": 95.1,
                }
            ],
            "split_comparison_pairs": [{"id": "old"}],
            "split_last_calculated_result": {"weather_sync": {"high_plus": {"matched": True}}},
            "split_final_results": {"num_results": 1},
            "excel_buffer": b"old",
        }

        clear_split_final_state(test_data)

        self.assertEqual(test_data["split_results"][0]["f0_prime"], 139.4)
        self.assertNotIn("weather_sync", test_data["split_results"][0])
        self.assertFalse(test_data["split_results"][0]["correction_available"])
        self.assertIsNone(test_data["split_results"][0]["corrected_pair_mean"])
        self.assertIsNone(test_data["split_results"][0]["temp_plus_used"])
        self.assertEqual(test_data["split_comparison_pairs"], [])
        self.assertIsNone(test_data["split_last_calculated_result"])
        self.assertEqual(test_data["split_final_results"], {})
        self.assertIsNone(test_data["excel_buffer"])

    def test_ambient_mode_change_invalidates_results_and_comparison_cards(self):
        test_data = {
            "split_results": [{"F0": 140.0}],
            "split_comparison_pairs": [{"id": "old"}],
            "split_last_calculated_result": {"F0": 140.0},
            "split_final_results": {"num_results": 1},
            "excel_buffer": b"old",
            "split_ambient_version": 2,
        }

        invalidate_split_ambient_state(test_data)

        self.assertEqual(test_data["split_results"], [])
        self.assertEqual(test_data["split_comparison_pairs"], [])
        self.assertIsNone(test_data["split_last_calculated_result"])
        self.assertEqual(test_data["split_final_results"], {})
        self.assertIsNone(test_data["excel_buffer"])
        self.assertEqual(test_data["split_ambient_version"], 3)

    def test_split_weather_file_loads_neutral_meteo_fields(self):
        weather_path = SAMPLE_DIR / "meteo" / "AGRICULTR_SPLIT.csv"
        records = read_weather_file(str(weather_path))

        self.assertGreater(len(records), 0)
        first = records[0]
        self.assertIn("timestamp", first)
        self.assertIn("temp_c", first)
        self.assertIn("baro_kpa", first)
        self.assertIn("wind_ms", first)
        self.assertIn("wind_direction", first)

        high_path = SAMPLE_DIR / "coastdown" / "split_MrLee_HighSpd_ctvi.csv"
        _, high_runs, _ = carregar_dados_csv_robusto(
            str(high_path),
            using_split_method=True,
            is_alta=True,
        )
        sync = sync_weather_to_run(high_runs[1], records)

        self.assertTrue(sync["matched"])
        self.assertEqual(sync["sync_method"], "datetime")
        self.assertLess(sync["time_delta_seconds"], 300)


if __name__ == "__main__":
    unittest.main()

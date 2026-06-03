# coding: utf-8
"""Integration checks for sample_data/Split imports."""

from pathlib import Path
import math
import unittest

from core.split_calculations import calculate_split_result
from data.loaders import carregar_dados_csv_robusto, read_weather_station_csv
from data.split_parser import default_split_interval_config, parse_split_sources


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "Split"


class SplitSampleDataImportTest(unittest.TestCase):
    def test_two_csv_high_low_eliezer_extracts_expected_deltas_and_coefficients(self):
        high_path = SAMPLE_DIR / "split eliezer high.csv"
        low_path = SAMPLE_DIR / "split eliezer low.csv"

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

    def test_single_high_only_csv_reports_missing_low_interval(self):
        high_path = SAMPLE_DIR / "split eliezer high.csv"
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

    def test_split_weather_file_loads_neutral_meteo_fields(self):
        weather_path = SAMPLE_DIR / "clima" / "AGRICULTR_SPLIT.csv"
        records = read_weather_station_csv(str(weather_path))

        self.assertGreater(len(records), 0)
        first = records[0]
        self.assertIn("timestamp", first)
        self.assertIn("temp_c", first)
        self.assertIn("baro_kpa", first)
        self.assertIn("wind_ms", first)


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for Split environmental correction helpers."""

from datetime import datetime
import unittest

from core.split_comparison import calculate_complete_split_pair
from core.split_corrections import (
    apply_split_pair_correction,
    correct_split_coefficients,
    fixed_ambient_conditions,
    weather_sync_ambient_conditions,
)
from core.split_energy import calculate_split_energy
from core.weather_sync import sync_weather_to_run
from data.split_parser import default_split_interval_config


class SplitCorrectionsTest(unittest.TestCase):
    def _record(self, filename, run_id, heading, delta_t_s):
        return {
            "filename": filename,
            "run_id": run_id,
            "heading": heading,
            "delta_t_s": delta_t_s,
            "delta_v_kmh": 20.0 if filename.startswith("high") else 10.0,
            "start_timestamp": datetime(2024, 4, 22, 18, run_id),
            "warnings": [],
        }

    def _raw_pair(self):
        return calculate_complete_split_pair(
            high_plus=self._record("high.csv", 1, "+", 18.72),
            low_plus=self._record("low.csv", 2, "+", 19.58),
            high_minus=self._record("high.csv", 3, "-", 19.00),
            low_minus=self._record("low.csv", 4, "-", 20.00),
            effective_mass=1545.0,
            config=default_split_interval_config(),
        )

    def _sync(
        self,
        temperature,
        pressure,
        method="datetime",
        warnings=None,
        wind_speed=1.0,
        wind_direction=180.0,
    ):
        return {
            "matched": True,
            "sync_method": method,
            "run_datetime": datetime(2024, 4, 22, 18, 0),
            "weather_datetime": datetime(2024, 4, 22, 18, 0),
            "time_delta_seconds": 0.0,
            "temperature": temperature,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "source_file": "meteo.xlsx",
            "warnings": list(warnings or []),
        }

    def test_fixed_mode_calculates_corrected_coefficients_without_weather(self):
        raw = self._raw_pair()
        corrected = apply_split_pair_correction(
            raw,
            fixed_ambient_conditions(20.0, 101.325),
        )

        self.assertTrue(corrected["correction_available"])
        self.assertEqual(corrected["ambient_mode"], "fixed")
        self.assertEqual(corrected["ambient_source"], "manual_fixed")
        self.assertEqual(corrected["temp_plus_used"], 20.0)
        self.assertEqual(corrected["press_minus_used"], 101.325)
        self.assertEqual(
            corrected["f0_prime_plus"],
            corrected["result_plus"]["f0_prime"],
        )
        self.assertEqual(
            corrected["f2_prime_minus"],
            corrected["result_minus"]["f2_prime"],
        )
        self.assertEqual(
            corrected["f0_prime_mean"],
            corrected["result_pair_mean"]["f0_prime"],
        )
        self.assertEqual(
            corrected["f2_prime_mean"],
            corrected["result_pair_mean"]["f2_prime"],
        )
        self.assertIn("F0", corrected["corrected_pair_mean"])
        self.assertIn("F2", corrected["corrected_pair_mean"])
        self.assertEqual(
            corrected["F0_plus"],
            corrected["corrected_result_plus"]["F0"],
        )
        self.assertEqual(
            corrected["F2_minus"],
            corrected["corrected_result_minus"]["F2"],
        )
        self.assertEqual(
            corrected["F0_mean"],
            corrected["corrected_pair_mean"]["F0"],
        )
        self.assertEqual(
            corrected["F2_mean"],
            corrected["corrected_pair_mean"]["F2"],
        )
        expected_energy = calculate_split_energy(
            corrected["F0_mean"],
            corrected["F2_mean"],
        )
        self.assertAlmostEqual(corrected["energy"], expected_energy["energy"])
        self.assertEqual(corrected["energy_status"], "calculated")
        self.assertEqual(corrected["energy_unit"], "MJ/km")
        self.assertEqual(
            corrected["energy_details"]["F0_used"],
            corrected["F0_mean"],
        )
        self.assertEqual(
            corrected["energy_details"]["F2_used"],
            corrected["F2_mean"],
        )
        self.assertEqual(corrected["weather_sync"], {})

    def test_weather_mode_averages_four_synchronized_runs(self):
        raw = self._raw_pair()
        sync = {
            "high_plus": self._sync(20.0, 100.0),
            "low_plus": self._sync(22.0, 102.0),
            "high_minus": self._sync(24.0, 104.0),
            "low_minus": self._sync(26.0, 106.0),
        }
        conditions = weather_sync_ambient_conditions(sync)
        corrected = apply_split_pair_correction(raw, conditions)

        self.assertTrue(corrected["correction_available"])
        self.assertEqual(corrected["temp_plus_used"], 21.0)
        self.assertEqual(corrected["press_plus_used"], 101.0)
        self.assertEqual(corrected["temp_minus_used"], 25.0)
        self.assertEqual(corrected["press_minus_used"], 105.0)
        self.assertEqual(corrected["ambient_source"], "weather_file_sync")
        self.assertEqual(
            set(corrected["ambient_by_component"]),
            {"high_plus", "low_plus", "high_minus", "low_minus"},
        )
        self.assertEqual(
            corrected["ambient_by_component"]["high_plus"]["temperature_c"],
            20.0,
        )
        self.assertEqual(corrected["temp_high_plus"], 20.0)
        self.assertEqual(corrected["press_low_plus"], 102.0)
        self.assertEqual(corrected["wind_high_minus"], 1.0)
        self.assertEqual(
            corrected["ambient_by_component"]["low_minus"]["source_file"],
            "meteo.xlsx",
        )

    def test_real_component_values_are_preserved_and_averaged_by_direction(self):
        raw = self._raw_pair()
        sync = {
            "high_plus": self._sync(23.6, 95.17, wind_speed=0.0),
            "low_plus": self._sync(23.5, 95.19, wind_speed=0.0),
            "high_minus": self._sync(23.6, 95.15, wind_speed=0.0),
            "low_minus": self._sync(23.5, 95.19, wind_speed=0.0),
        }

        corrected = apply_split_pair_correction(
            raw,
            weather_sync_ambient_conditions(sync),
        )

        self.assertAlmostEqual(corrected["temp_plus_used"], 23.55)
        self.assertAlmostEqual(corrected["press_plus_used"], 95.18)
        self.assertAlmostEqual(corrected["temp_minus_used"], 23.55)
        self.assertAlmostEqual(corrected["press_minus_used"], 95.17)
        self.assertEqual(corrected["wind_high_plus"], 0.0)
        self.assertEqual(corrected["wind_low_plus"], 0.0)
        self.assertEqual(corrected["wind_high_minus"], 0.0)
        self.assertEqual(corrected["wind_low_minus"], 0.0)

    def test_time_only_fallback_warning_is_preserved(self):
        run_time = datetime(2024, 4, 23, 18, 47, 30)
        weather = [
            {
                "timestamp": datetime(2024, 4, 22, 18, 48),
                "temp_c": 24.0,
                "baro_kpa": 95.2,
                "wind_ms": 1.0,
                "timezone": None,
                "warnings": [],
            }
        ]
        matched = sync_weather_to_run(
            run_time,
            weather,
            max_time_delta_seconds=60,
            allow_time_only_fallback=True,
        )
        sync = {component: dict(matched) for component in (
            "high_plus",
            "low_plus",
            "high_minus",
            "low_minus",
        )}

        conditions = weather_sync_ambient_conditions(sync)

        self.assertTrue(conditions["available"])
        self.assertTrue(any("date differs" in warning for warning in conditions["warnings"]))

    def test_missing_weather_match_does_not_generate_corrected_coefficients(self):
        raw = self._raw_pair()
        sync = {
            "high_plus": self._sync(20.0, 101.0),
            "low_plus": self._sync(20.0, 101.0),
            "high_minus": self._sync(20.0, 101.0),
            "low_minus": {
                "matched": False,
                "sync_method": "not_found",
                "temperature": None,
                "pressure": None,
                "warnings": ["No match within limit."],
            },
        }

        corrected = apply_split_pair_correction(
            raw,
            weather_sync_ambient_conditions(sync),
        )

        self.assertFalse(corrected["correction_available"])
        self.assertIsNotNone(corrected["corrected_result_plus"])
        self.assertIsNone(corrected["corrected_result_minus"])
        self.assertIsNone(corrected["corrected_pair_mean"])
        self.assertIsNone(corrected["F0_mean"])
        self.assertIsNone(corrected["F2_mean"])
        self.assertIsNone(corrected["energy"])
        self.assertIn("unavailable", corrected["energy_status"])
        self.assertIsNotNone(corrected["F0_plus"])
        self.assertIsNone(corrected["F0_minus"])
        self.assertIsNone(corrected["temp_low_minus"])
        self.assertIsNone(corrected["wind_low_minus"])

    def test_missing_weather_value_remains_none_and_blocks_only_its_direction(self):
        raw = self._raw_pair()
        sync = {
            "high_plus": self._sync(20.0, 101.0),
            "low_plus": self._sync(20.0, 101.0),
            "high_minus": self._sync(20.0, 101.0),
            "low_minus": self._sync(
                20.0,
                None,
                wind_speed=None,
                wind_direction=None,
            ),
        }

        corrected = apply_split_pair_correction(
            raw,
            weather_sync_ambient_conditions(sync),
        )

        self.assertIsNotNone(corrected["F0_plus"])
        self.assertIsNone(corrected["F0_minus"])
        self.assertIsNone(corrected["F0_mean"])
        self.assertIsNone(corrected["press_low_minus"])
        self.assertIsNone(corrected["wind_low_minus"])

    def test_uncorrected_and_corrected_coefficients_remain_separate(self):
        raw = self._raw_pair()
        original_f0 = raw["f0_prime"]
        original_f2 = raw["f2_prime"]

        corrected = apply_split_pair_correction(
            raw,
            fixed_ambient_conditions(25.0, 95.0),
        )

        self.assertEqual(corrected["f0_prime"], original_f0)
        self.assertEqual(corrected["f2_prime"], original_f2)
        self.assertEqual(corrected["f0_prime_mean"], original_f0)
        self.assertEqual(corrected["f2_prime_mean"], original_f2)
        self.assertNotIn("F0", corrected["result_pair_mean"])
        self.assertIn("F0", corrected["corrected_pair_mean"])
        self.assertIn("F2", corrected["corrected_pair_mean"])
        corrected_energy = calculate_split_energy(
            corrected["F0_mean"],
            corrected["F2_mean"],
        )["energy"]
        raw_energy = calculate_split_energy(
            corrected["f0_prime_mean"],
            corrected["f2_prime_mean"],
        )["energy"]
        self.assertAlmostEqual(corrected["energy"], corrected_energy)
        self.assertNotAlmostEqual(corrected["energy"], raw_energy)

    def test_reference_conditions_preserve_f0_and_convert_f2_units(self):
        corrected = correct_split_coefficients(139.4, 0.646, 20.0, 101.325)

        self.assertAlmostEqual(corrected["F0"], 139.4)
        self.assertAlmostEqual(corrected["F2"], 0.646 / 12.96)
        self.assertEqual(corrected["F2_unit"], "N/(km/h)^2")


if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for pure per-run Split weather synchronization."""

from copy import deepcopy
from datetime import datetime
import unittest

from core.split_weather_context import (
    build_fixed_split_correction_context,
    split_environmental_values,
    synchronize_weather_for_split_runs,
)


class SplitWeatherContextTest(unittest.TestCase):
    def test_fixed_context_uses_canonical_kpa_fields_without_missing_weather(self):
        context = build_fixed_split_correction_context(22.5, 99.8)

        self.assertEqual(context["mode"], "fixed")
        self.assertEqual(context["temperature_c"], 22.5)
        self.assertEqual(context["pressure_kpa"], 99.8)
        self.assertIsNone(context["wind_speed_mps"])
        self.assertEqual(context["environmental_conditions"]["source"], "user_fixed_inputs")
        self.assertEqual(context["weather_summary"]["status"], "fixed")

    def test_hot_fixed_context_warns_but_remains_fixed(self):
        context = build_fixed_split_correction_context(36.0, 101.325)

        self.assertEqual(context["weather_summary"]["status"], "fixed")
        self.assertTrue(context["warnings"])
        self.assertNotIn("missing", str(context).lower())

    def test_environmental_reader_prefers_canonical_fixed_structure(self):
        values = split_environmental_values({"environmental_conditions": {
            "mode": "fixed", "temperature_c": 24.0,
            "pressure_kpa": 100.2, "wind_speed_mps": None,
        }})

        self.assertEqual(values["mode"], "fixed")
        self.assertEqual(values["temperature_c"], 24.0)
        self.assertEqual(values["pressure_kpa"], 100.2)
        self.assertIsNone(values["wind_speed_mps"])

    def _parsed(self):
        return {
            "high": [{"run_id": 1, "heading": "+", "start_timestamp": datetime(2024, 1, 1, 10, 0)}],
            "low": [{"run_id": 2, "heading": "-", "start_timestamp": datetime(2024, 1, 1, 10, 1)}],
        }

    def _weather(self, **overrides):
        record = {
            "timestamp": datetime(2024, 1, 1, 10, 0),
            "temp_c": 25.0,
            "baro_kpa": 100.0,
            "wind_ms": 2.0,
            "wind_direction": 180.0,
            "timezone": "America/Sao_Paulo",
            "warnings": [],
        }
        record.update(overrides)
        return [record]

    def test_sync_enriches_copy_without_mutating_input(self):
        parsed = self._parsed()
        original = deepcopy(parsed)

        enriched, metadata = synchronize_weather_for_split_runs(parsed, self._weather())

        self.assertEqual(parsed, original)
        sync = enriched["high"][0]["weather_sync"]
        for key in ("temperature_c", "pressure_kpa", "wind_speed_mps", "method", "time_diff_s"):
            self.assertIn(key, sync)
        self.assertEqual(metadata["high_synchronized"], 1)
        self.assertEqual(metadata["low_synchronized"], 1)

    def test_wind_and_temperature_limits_invalidate_but_pressure_does_not(self):
        enriched, metadata = synchronize_weather_for_split_runs(
            self._parsed(), self._weather(temp_c=36.0, wind_ms=3.1, baro_kpa=200.0)
        )

        sync = enriched["high"][0]["weather_sync"]
        self.assertEqual(sync["status"], "invalid")
        self.assertTrue(any("Vento acima" in warning for warning in sync["warnings"]))
        self.assertTrue(any("Temperatura acima" in warning for warning in sync["warnings"]))
        self.assertFalse(any("Press" in warning for warning in sync["invalid_reasons"]))
        self.assertEqual(metadata["wind_above_limit_count"], 2)

if __name__ == "__main__":
    unittest.main()

# coding: utf-8
"""Tests for pure per-run Split weather synchronization."""

from copy import deepcopy
from datetime import datetime
import inspect
import unittest

from core.split_weather_context import synchronize_weather_for_split_runs


class SplitWeatherContextTest(unittest.TestCase):
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

    def test_module_does_not_import_streamlit(self):
        import core.split_weather_context as module
        source = inspect.getsource(module).lower()
        self.assertNotIn("import streamlit", source)
        self.assertNotIn("from streamlit", source)


if __name__ == "__main__":
    unittest.main()

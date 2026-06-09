# coding: utf-8
"""Tests for neutral Split weather loading and synchronization."""

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from core.weather_sync import sync_weather_to_run
from data.weather_loader import read_weather_file


class WeatherSyncTest(unittest.TestCase):
    def _weather(self, timestamp, **overrides):
        record = {
            "timestamp": timestamp,
            "temp_c": 24.0,
            "baro_kpa": 95.2,
            "wind_ms": 1.5,
            "wind_direction": 180.0,
            "timezone": None,
            "warnings": [],
        }
        record.update(overrides)
        return record

    def test_sync_exact_datetime(self):
        target = datetime(2024, 4, 22, 18, 47)
        result = sync_weather_to_run(target, [self._weather(target)])

        self.assertTrue(result["matched"])
        self.assertEqual(result["sync_method"], "datetime")
        self.assertEqual(result["time_delta_seconds"], 0.0)
        self.assertEqual(result["temperature"], 24.0)

    def test_sync_uses_closest_datetime(self):
        target = datetime(2024, 4, 22, 18, 47, 30)
        records = [
            self._weather(datetime(2024, 4, 22, 18, 45)),
            self._weather(datetime(2024, 4, 22, 18, 48)),
        ]

        result = sync_weather_to_run(target, records, max_time_delta_seconds=60)

        self.assertTrue(result["matched"])
        self.assertEqual(result["weather_datetime"], datetime(2024, 4, 22, 18, 48))
        self.assertEqual(result["time_delta_seconds"], 30.0)

    def test_sync_falls_back_to_time_only_with_warning(self):
        target = datetime(2024, 4, 23, 18, 47, 30)
        records = [self._weather(datetime(2024, 4, 22, 18, 48))]

        result = sync_weather_to_run(
            target,
            records,
            max_time_delta_seconds=60,
            allow_time_only_fallback=True,
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["sync_method"], "time_only")
        self.assertEqual(result["time_delta_seconds"], 30.0)
        self.assertTrue(any("date differs" in warning for warning in result["warnings"]))

    def test_sync_rejects_record_outside_limit(self):
        target = datetime(2024, 4, 22, 18, 47)
        records = [self._weather(datetime(2024, 4, 22, 18, 50))]

        result = sync_weather_to_run(
            target,
            records,
            max_time_delta_seconds=60,
            allow_time_only_fallback=False,
        )

        self.assertFalse(result["matched"])
        self.assertEqual(result["sync_method"], "not_found")
        self.assertTrue(any("above" in warning for warning in result["warnings"]))

    def test_sync_reports_ambiguous_run_date(self):
        records = [self._weather(datetime(2024, 5, 4, 10, 0))]

        result = sync_weather_to_run("04/05/2024 10:00", records)

        self.assertTrue(result["matched"])
        self.assertTrue(any("Ambiguous run date" in warning for warning in result["warnings"]))

    def test_csv_loader_accepts_decimal_comma(self):
        content = (
            "Data;Hora;Temperatura;Pressao;Velocidade Vento;Direcao Vento\n"
            "13/05/2024;10:00:00;23,4;951,5;1,2;180\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_decimal_comma.csv"
            path.write_text(content, encoding="utf-8")
            records = read_weather_file(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["timestamp"], datetime(2024, 5, 13, 10, 0))
        self.assertAlmostEqual(records[0]["temp_c"], 23.4)
        self.assertAlmostEqual(records[0]["baro_kpa"], 95.15)
        self.assertAlmostEqual(records[0]["wind_ms"], 1.2)
        self.assertEqual(records[0]["wind_direction"], 180.0)

    def test_xlsx_loader_is_supported(self):
        frame = pd.DataFrame(
            {
                "Time": [datetime(2024, 4, 22, 18, 47)],
                "Temp": [23.6],
                "Baro.": [951.7],
                "Wind Speed": [0.8],
                "True Dir.": [81],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather.xlsx"
            frame.to_excel(path, index=False)
            records = read_weather_file(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["timestamp"], datetime(2024, 4, 22, 18, 47))
        self.assertAlmostEqual(records[0]["baro_kpa"], 95.17)
        self.assertEqual(records[0]["wind_direction"], 81.0)


if __name__ == "__main__":
    unittest.main()

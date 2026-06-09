# coding: utf-8
"""Tests for neutral Split weather loading and synchronization."""

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from core.weather_sync import sync_weather_to_run
from data.weather_loader import read_weather_file
from pages.page_split_coefficient_calculation import (
    _translated_weather_warning,
    _weather_sync_summary,
    _weather_sync_warnings,
)
from translations import get_translator


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

    def test_weather_warning_messages_are_translated_to_pt_and_en(self):
        equally_close = (
            "Multiple weather records were equally close; "
            "the first source record was selected."
        )
        timezone_missing = (
            "Weather timezone is not declared; "
            "timestamps were compared as local time."
        )

        self.assertEqual(
            _translated_weather_warning(equally_close, get_translator("pt")),
            (
                "Foram encontrados registros meteorológicos igualmente próximos; "
                "o primeiro registro foi usado."
            ),
        )
        self.assertEqual(
            _translated_weather_warning(timezone_missing, get_translator("pt")),
            (
                "O arquivo meteorológico não declara fuso horário; "
                "os horários foram comparados como horário local."
            ),
        )
        self.assertEqual(
            _translated_weather_warning(equally_close, get_translator("en")),
            "Multiple weather records were equally close; the first record was used.",
        )
        self.assertEqual(
            _translated_weather_warning(timezone_missing, get_translator("en")),
            timezone_missing,
        )

    def test_weather_summary_is_short_while_warnings_are_preserved(self):
        raw_warning = (
            "Weather timezone is not declared; "
            "timestamps were compared as local time."
        )
        weather_sync = {
            "high_plus": {
                "matched": True,
                "sync_method": "time_only",
                "warnings": [raw_warning],
            }
        }
        t = get_translator("pt")

        self.assertIn("somente horário", _weather_sync_summary(weather_sync, t))
        self.assertEqual(
            _weather_sync_warnings(weather_sync, t),
            [
                (
                    "O arquivo meteorológico não declara fuso horário; "
                    "os horários foram comparados como horário local."
                )
            ],
        )

    def test_csv_loader_accepts_decimal_comma(self):
        content = (
            "Data;Hora;Temperatura;Pressao;Velocidade Vento [m/s];Direcao Vento\n"
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
                "Wind Speed [m/s]": [0.8],
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
        self.assertAlmostEqual(records[0]["wind_ms"], 0.8)
        self.assertEqual(records[0]["wind_direction"], 81.0)

    def test_missing_wind_column_remains_none_with_warning(self):
        content = (
            "Time,Temp,Baro.,True Dir.\n"
            "2024-04-22 18:47:00,23.6,951.7,81\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_without_wind.csv"
            path.write_text(content, encoding="utf-8")
            record = read_weather_file(path)[0]

        self.assertIsNone(record["wind_ms"])
        self.assertTrue(any("column was not found" in item for item in record["warnings"]))

    def test_missing_and_invalid_wind_values_remain_none(self):
        content = (
            "Time,Temp,Baro.,Wind Speed [m/s],True Dir.\n"
            "2024-04-22 18:47:00,23.6,951.7,,81\n"
            "2024-04-22 18:48:00,23.6,951.7,invalid,82\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_bad_wind.csv"
            path.write_text(content, encoding="utf-8")
            records = read_weather_file(path)

        self.assertIsNone(records[0]["wind_ms"])
        self.assertTrue(any("missing" in item for item in records[0]["warnings"]))
        self.assertIsNone(records[1]["wind_ms"])
        self.assertTrue(any("invalid" in item for item in records[1]["warnings"]))

    def test_real_zero_wind_is_preserved_even_with_nonzero_components(self):
        content = (
            "Time,Temp,Baro.,Wind Speed,Crosswind,Headwind,True Dir.\n"
            "yyyy-MM-dd hh:mm:ss,Celsius,mb,m/s,m/s,m/s,Degrees\n"
            "2024-04-22 18:47:00,23.6,951.7,0,3,4,81\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_zero_wind.csv"
            path.write_text(content, encoding="utf-8")
            record = read_weather_file(path)[0]

        self.assertEqual(record["wind_ms"], 0.0)
        self.assertEqual(record["wind_unit"], "m/s")
        self.assertEqual(record["warnings"], [])

    def test_nonzero_ms_wind_is_preserved(self):
        content = (
            "Time,Temp,Baro.,Wind Speed,True Dir.\n"
            "yyyy-MM-dd hh:mm:ss,Celsius,mb,m/s,Degrees\n"
            "2024-04-22 18:47:00,23.6,951.7,2.5,81\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_ms_wind.csv"
            path.write_text(content, encoding="utf-8")
            record = read_weather_file(path)[0]

        self.assertEqual(record["wind_ms"], 2.5)
        self.assertEqual(record["warnings"], [])

    def test_kmh_wind_is_converted_to_ms(self):
        content = (
            "Time,Temp,Baro.,Wind Speed [km/h],True Dir.\n"
            "2024-04-22 18:47:00,23.6,951.7,18,81\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_kmh_wind.csv"
            path.write_text(content, encoding="utf-8")
            record = read_weather_file(path)[0]

        self.assertAlmostEqual(record["wind_ms"], 5.0)
        self.assertEqual(record["wind_unit"], "m/s")
        self.assertTrue(any("converted from km/h" in item for item in record["warnings"]))

    def test_unknown_wind_unit_is_not_assumed(self):
        content = (
            "Time,Temp,Baro.,Wind Speed,True Dir.\n"
            "2024-04-22 18:47:00,23.6,951.7,2.5,81\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather_unknown_wind.csv"
            path.write_text(content, encoding="utf-8")
            record = read_weather_file(path)[0]

        self.assertIsNone(record["wind_ms"])
        self.assertTrue(any("unit" in item and "unknown" in item for item in record["warnings"]))


if __name__ == "__main__":
    unittest.main()

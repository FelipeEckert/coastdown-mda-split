# coding: utf-8
"""Regression coverage for vectorized weather timestamp parsing."""

from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from data import weather_loader


ROOT_DIR = Path(__file__).resolve().parents[1]
WEATHER_FIXTURE = (
    ROOT_DIR / "sample_data" / "Split" / "meteo" / "AGRICULTR_SPLIT.csv"
)


def _scalar_parse(values):
    return [weather_loader._parse_datetime(value) for value in values]


class WeatherLoaderVectorizationTests(unittest.TestCase):
    def test_supported_datetime_formats_match_scalar_parser(self):
        values = [
            pd.Timestamp("2024-04-22 18:47:00"),
            datetime(2024, 4, 22, 18, 47),
            "2024-04-22 18:47:00",
            "13/05/2024 10:00:00",
            "05-04-2024 10:00",
            "May 13, 2024 10:00",
        ]
        expected = _scalar_parse(values)

        with patch.object(
            weather_loader.pd,
            "to_datetime",
            wraps=pd.to_datetime,
        ) as parser:
            actual = weather_loader._parse_datetime_series(values)

        self.assertEqual(actual, expected)
        if int(pd.__version__.split(".", 1)[0]) >= 2:
            self.assertEqual(parser.call_count, 2)

    def test_invalid_values_and_ambiguity_warnings_match_scalar_parser(self):
        values = [None, "", pd.NaT, "not-a-date", "04/05/2024 10:00"]
        actual = weather_loader._parse_datetime_series(values)

        self.assertEqual(actual, _scalar_parse(values))
        self.assertEqual(
            actual[-1][1],
            [
                (
                    "Ambiguous date '04/05/2024 10:00' was interpreted "
                    "using day-first order."
                )
            ],
        )

    def test_record_ordering_and_duplicates_are_preserved(self):
        frame = pd.DataFrame(
            {
                "Time": [
                    "2024-04-22 18:48:00",
                    "22/04/2024 18:47:00",
                    "2024-04-22 18:47:00",
                    "invalid",
                ],
                "Temp": [22.0, 23.0, 24.0, 25.0],
                "Baro.": [951.0, 952.0, 953.0, 954.0],
                "Wind Speed [m/s]": [1.0, 1.1, 1.2, 1.3],
                "True Dir.": [80, 81, 82, 83],
            }
        )

        records = weather_loader._normalize_weather_frame(frame)

        self.assertEqual(
            [record["timestamp"] for record in records],
            [
                datetime(2024, 4, 22, 18, 47),
                datetime(2024, 4, 22, 18, 47),
                datetime(2024, 4, 22, 18, 48),
            ],
        )
        self.assertEqual(
            [record["temp_c"] for record in records],
            [23.0, 24.0, 22.0],
        )

    def test_split_weather_fixture_matches_scalar_records_exactly(self):
        frame = weather_loader._read_csv(WEATHER_FIXTURE)
        with patch.object(
            weather_loader,
            "_parse_datetime_series",
            side_effect=_scalar_parse,
        ):
            expected = weather_loader._normalize_weather_frame(frame)

        actual = weather_loader._normalize_weather_frame(frame)

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()

"""Characterize Split run timestamps and automatic weather synchronization."""

from contextlib import chdir
import csv
from datetime import date, datetime, time
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from core.split_comparison import (
    build_split_comparison_pair,
    calculate_complete_split_pair,
)
from core.split_corrections import (
    apply_split_pair_correction,
    weather_sync_ambient_conditions,
)
from core.split_weather_context import (
    build_split_candidate_weather_context,
    synchronize_weather_for_split_runs,
)
from core.weather_sync import sync_weather_to_run
from data.loaders import _parse_coastdown_start_time, carregar_dados_csv_robusto
from data.split_parser import default_split_interval_config, parse_split_sources
from data.weather_loader import read_weather_file


ROOT_DIR = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT_DIR / "sample_data" / "Split"
COASTDOWN_DIR = SPLIT_DIR / "coastdown"
WEATHER_PATH = SPLIT_DIR / "meteo" / "AGRICULTR_SPLIT.csv"


def _vbox_text(
    *,
    first_line="Test Date: 22/04/2024 15:49",
    date_value="22-Apr-2024",
    start_time="18:47:17.147",
):
    rows = [
        [first_line],
        ["Time zone", "E. South America Standard Time"],
        ["Test Date", date_value],
        ["Trigger"],
        ["Requires Trigger", "Off"],
        ["Trigger Channel", ""],
        ["Deceleration"],
        ["Ignore runs that exceed (g)", "0.20"],
        ["Smooth Level", "4"],
        ["Speed Quality"],
        ["Check", "Off"],
        ["Speed threshold (km/h)", "0.10"],
        ["In (s)", "0.05"],
        [],
        [
            "Run-Use",
            "Heading",
            "Run",
            "Time (s)",
            "Distance (m)",
            "Start Time",
            "Max Decel (g)",
            "90-85",
            "85-80",
            "Notes",
        ],
        ["On", "+", "1", "8.75", "500", start_time, "0.10", "4.25", "4.50", ""],
    ]
    output = StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue()


def _weather(timestamp, **overrides):
    record = {
        "timestamp": timestamp,
        "temp_c": 24.0,
        "baro_kpa": 95.2,
        "wind_ms": 1.5,
        "wind_direction": 180.0,
        "timezone": "local",
        "warnings": [],
    }
    record.update(overrides)
    return record


class TemporalWeatherCharacterizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weather_records = read_weather_file(WEATHER_PATH)

    def _load_real_runs(self, filename):
        return carregar_dados_csv_robusto(
            COASTDOWN_DIR / filename,
            using_split_method=True,
        )[1]

    def _load_synthetic_run(self, **overrides):
        with tempfile.TemporaryDirectory(dir=ROOT_DIR) as directory, chdir(directory):
            path = Path(directory) / "temporal.csv"
            path.write_text(_vbox_text(**overrides), encoding="utf-8")
            return carregar_dados_csv_robusto(
                path,
                using_split_method=True,
            )[1][1]

    def test_real_header_date_layouts_preserve_absolute_milliseconds(self):
        cases = (
            (
                "split_MrLee_HighSpd_ctvi.csv",
                "Test Date,",
                "16:01:48.317",
                datetime(2024, 4, 22, 16, 1, 48, 317000),
            ),
            (
                "altas ioniq_16012026.csv",
                "Test Date,16-Jan-2026",
                "13:29:42.464",
                datetime(2026, 1, 16, 13, 29, 42, 464000),
            ),
        )
        for filename, third_line, raw_time, expected in cases:
            with self.subTest(filename=filename):
                path = COASTDOWN_DIR / filename
                self.assertEqual(path.read_text(encoding="utf-8").splitlines()[2], third_line)
                run = self._load_real_runs(filename)[1]
                self.assertEqual(run["start_time_str"], raw_time)
                self.assertEqual(run["start_timestamp"], expected)
                self.assertEqual(run["start_timestamp"].microsecond, expected.microsecond)

    def test_loader_current_elapsed_and_legacy_time_fallbacks(self):
        cases = (
            ("00:01:02.345", datetime(2024, 4, 22, 15, 50, 2, 345000)),
            ("01:02.345", datetime(2024, 4, 22, 15, 50, 2, 345000)),
            ("6:47:17 PM", datetime(2024, 4, 22, 18, 47, 17)),
            # Current precedence: two fields are MM:SS, not absolute HH:MM.
            ("18:47", datetime(2024, 4, 22, 16, 7, 47)),
        )
        for raw_time, expected in cases:
            with self.subTest(raw_time=raw_time):
                run = self._load_synthetic_run(start_time=raw_time)
                self.assertEqual(run["start_time_str"], raw_time)
                self.assertEqual(run["start_timestamp"], expected)

    def test_start_time_helper_preserves_values_types_and_debug_contract(self):
        test_date = date(2024, 4, 22)
        test_start = datetime(2024, 4, 22, 15, 49)
        cases = (
            (
                "18:47:17.147",
                test_start,
                "18:47:17.147",
                datetime(2024, 4, 22, 18, 47, 17, 147000),
                [
                    "  -> Start Time '18:47:17.147' interpretado como ABSOLUTO -> "
                    "2024-04-22 18:47:17.147000"
                ],
            ),
            (
                "18:47",
                test_start,
                "18:47",
                datetime(2024, 4, 22, 16, 7, 47),
                [
                    "  -> Start Time '18:47' (MM:SS) tratado como ELAPSED "
                    "18m47.000s desde 2024-04-22 15:49:00 -> 2024-04-22 16:07:47"
                ],
            ),
            (
                "not-a-time",
                test_start,
                "not-a-time",
                None,
                [
                    "  -> ERRO: Não foi possível interpretar start_time "
                    "'not-a-time' como elapsed nem absoluto."
                ],
            ),
            (
                float("nan"),
                test_start,
                "nan",
                None,
                [
                    "  -> ERRO: Não foi possível interpretar start_time 'nan' "
                    "como elapsed nem absoluto."
                ],
            ),
            (
                "00:01:02.345",
                None,
                "00:01:02.345",
                None,
                [
                    "  -> Start Time '00:01:02.345' sugere ELAPSED, mas "
                    "'test_start_datetime' não está disponível.",
                    "  -> ERRO: Não foi possível interpretar start_time "
                    "'00:01:02.345' como elapsed nem absoluto.",
                ],
            ),
        )
        for raw_value, origin, expected_text, expected_time, expected_debug in cases:
            with self.subTest(raw_value=raw_value):
                debug_output = []
                retained, parsed = _parse_coastdown_start_time(
                    raw_value,
                    test_date,
                    origin,
                    debug_output,
                )
                self.assertIsInstance(retained, str)
                self.assertEqual(retained, expected_text)
                self.assertEqual(parsed, expected_time)
                self.assertTrue(parsed is None or isinstance(parsed, datetime))
                self.assertEqual(debug_output, expected_debug)

    def test_missing_or_malformed_coastdown_temporal_fields_keep_current_errors(self):
        with tempfile.TemporaryDirectory(dir=ROOT_DIR) as directory, chdir(directory):
            path = Path(directory) / "missing_date.csv"
            path.write_text(
                _vbox_text(first_line="No test date", date_value="invalid"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "Não foi possível encontrar a 'Test Date'",
            ):
                carregar_dados_csv_robusto(path, using_split_method=True)

        for raw_time, retained in (("not-a-time", "not-a-time"), ("", "nan")):
            with self.subTest(raw_time=raw_time):
                run = self._load_synthetic_run(start_time=raw_time)
                self.assertEqual(run["start_time_str"], retained)
                self.assertIsNone(run["start_timestamp"])

    def test_real_runs_select_exact_expected_weather_values_deterministically(self):
        cases = (
            (
                "split_MrLee_HighSpd_ctvi.csv",
                datetime(2024, 4, 22, 16, 2),
                11.683,
                (23.4, 95.25, 0.0, 112.0, 6071),
            ),
            (
                "split eliezer high.csv",
                datetime(2024, 4, 22, 18, 47),
                17.147,
                (23.6, 95.17, 0.0, 80.0, 6401),
            ),
            (
                "split eliezer low.csv",
                datetime(2024, 4, 22, 19, 12),
                16.976,
                (23.5, 95.19, 0.0, 80.0, 6451),
            ),
        )
        for filename, weather_time, delta, values in cases:
            with self.subTest(filename=filename):
                run = self._load_real_runs(filename)[1]
                first = sync_weather_to_run(run, self.weather_records)
                second = sync_weather_to_run(run, self.weather_records)
                self.assertEqual(first, second)
                self.assertEqual(first["sync_method"], "datetime")
                self.assertEqual(first["weather_datetime"], weather_time)
                self.assertAlmostEqual(first["time_delta_seconds"], delta)
                self.assertEqual(
                    (
                        first["temperature"],
                        first["pressure"],
                        first["wind_speed"],
                        first["wind_direction"],
                        first["weather_record"]["source_row"],
                    ),
                    values,
                )

    def test_nearest_exact_tie_duplicate_and_unordered_selection(self):
        target = datetime(2024, 4, 22, 12, 0, 30)
        before = _weather(datetime(2024, 4, 22, 12, 0), temp_c=20.0)
        after = _weather(datetime(2024, 4, 22, 12, 1), temp_c=21.0)

        tie = sync_weather_to_run(target, [after, before])
        self.assertEqual(tie["weather_record"], after)
        self.assertEqual(tie["time_delta_seconds"], 30.0)
        self.assertTrue(any("equally close" in warning for warning in tie["warnings"]))

        exact = _weather(target, temp_c=22.0)
        self.assertEqual(
            sync_weather_to_run(target, [after, exact, before])["weather_record"],
            exact,
        )

        first_duplicate = _weather(target, temp_c=23.0)
        second_duplicate = _weather(target, temp_c=24.0)
        duplicate = sync_weather_to_run(target, [first_duplicate, second_duplicate])
        self.assertEqual(duplicate["weather_record"], first_duplicate)

        nearer_before = sync_weather_to_run(
            datetime(2024, 4, 22, 12, 0, 20),
            [after, before],
        )
        nearer_after = sync_weather_to_run(
            datetime(2024, 4, 22, 12, 0, 40),
            [after, before],
        )
        self.assertEqual(nearer_before["weather_record"], before)
        self.assertEqual(nearer_after["weather_record"], after)

    def test_limit_date_fallback_and_midnight_boundaries(self):
        target = datetime(2024, 4, 22, 12, 0)
        at_limit = sync_weather_to_run(
            target,
            [_weather(datetime(2024, 4, 22, 12, 5))],
        )
        beyond_limit = sync_weather_to_run(
            target,
            [_weather(datetime(2024, 4, 22, 12, 5, 0, 1000))],
            allow_time_only_fallback=False,
        )
        self.assertTrue(at_limit["matched"])
        self.assertEqual(at_limit["time_delta_seconds"], 300.0)
        self.assertFalse(beyond_limit["matched"])

        fallback = sync_weather_to_run(
            datetime(2024, 4, 23, 23, 59, 55),
            [_weather(datetime(2024, 4, 22, 0, 0, 5))],
        )
        self.assertEqual(fallback["sync_method"], "time_only")
        self.assertEqual(fallback["time_delta_seconds"], 10.0)

        time_only = sync_weather_to_run(
            time(23, 59, 55),
            [_weather(datetime(2024, 4, 22, 0, 0, 5))],
        )
        self.assertEqual(time_only["sync_method"], "manual_date_assumption")
        self.assertEqual(time_only["time_delta_seconds"], 10.0)

    def test_invalid_run_and_weather_timestamps_do_not_create_matches(self):
        invalid_records = [
            {"timestamp": "2024-04-22 12:00", "temp_c": 24.0},
            {"weather_datetime": None},
            "not-a-record",
        ]
        for run_value in (None, "", "not-a-date", {"start_timestamp": None}):
            with self.subTest(run_value=run_value):
                result = sync_weather_to_run(run_value, invalid_records)
                self.assertFalse(result["matched"])
                self.assertEqual(result["sync_method"], "not_found")
                self.assertIsNone(result["weather_record"])

        result = sync_weather_to_run(datetime(2024, 4, 22, 12), invalid_records)
        self.assertFalse(result["matched"])
        self.assertTrue(any("No valid weather records" in item for item in result["warnings"]))

    def test_real_cross_date_fallback_is_currently_time_only(self):
        run = self._load_real_runs("altas ioniq_16012026.csv")[1]
        without_fallback = sync_weather_to_run(
            run,
            self.weather_records,
            allow_time_only_fallback=False,
        )
        with_fallback = sync_weather_to_run(run, self.weather_records)

        self.assertFalse(without_fallback["matched"])
        self.assertTrue(with_fallback["matched"])
        self.assertEqual(with_fallback["sync_method"], "time_only")
        self.assertEqual(
            with_fallback["weather_datetime"],
            datetime(2024, 4, 22, 13, 30),
        )
        self.assertAlmostEqual(with_fallback["time_delta_seconds"], 17.536)
        self.assertEqual(
            (
                with_fallback["temperature"],
                with_fallback["pressure"],
                with_fallback["wind_speed"],
                with_fallback["wind_direction"],
            ),
            (23.1, 95.42, 0.0, 113.0),
        )

    def test_sync_traceability_reaches_corrected_comparison_pair(self):
        high_runs = self._load_real_runs("split eliezer high.csv")
        low_runs = self._load_real_runs("split eliezer low.csv")
        parsed = parse_split_sources(
            [
                {
                    "filename": "split eliezer high.csv",
                    "role": "high",
                    "all_run_data": high_runs,
                },
                {
                    "filename": "split eliezer low.csv",
                    "role": "low",
                    "all_run_data": low_runs,
                },
            ],
            default_split_interval_config(),
        )
        enriched, metadata = synchronize_weather_for_split_runs(
            parsed,
            self.weather_records,
        )
        components = {
            "high_plus": next(item for item in enriched["high"] if item["heading"] == "+"),
            "low_plus": next(item for item in enriched["low"] if item["heading"] == "+"),
            "high_minus": next(item for item in enriched["high"] if item["heading"] == "-"),
            "low_minus": next(item for item in enriched["low"] if item["heading"] == "-"),
        }
        weather_context = build_split_candidate_weather_context(components)
        raw = calculate_complete_split_pair(
            **components,
            effective_mass=1545.0,
            config=default_split_interval_config(),
        )
        corrected = apply_split_pair_correction(
            raw,
            weather_sync_ambient_conditions(weather_context["weather_sync"]),
        )
        pair = build_split_comparison_pair(corrected, pair_id="temporal_trace")

        self.assertEqual(metadata["high_synchronized"], len(parsed["high"]))
        self.assertEqual(metadata["low_synchronized"], len(parsed["low"]))
        self.assertTrue(pair["correction_available"])
        high_plus = pair["ambient_by_component"]["high_plus"]
        self.assertEqual(high_plus["run_datetime"], datetime(2024, 4, 22, 18, 47, 17, 147000))
        self.assertEqual(high_plus["weather_datetime"], datetime(2024, 4, 22, 18, 47))
        self.assertEqual(high_plus["sync_method"], "datetime")
        self.assertAlmostEqual(high_plus["time_delta_seconds"], 17.147)
        self.assertEqual(high_plus["temperature_c"], 23.6)
        self.assertEqual(high_plus["pressure_kpa"], 95.17)
        self.assertEqual(high_plus["wind_speed_mps"], 0.0)
        self.assertEqual(high_plus["wind_direction_deg"], 80.0)
        self.assertEqual(high_plus["source_file"], "AGRICULTR_SPLIT.csv")
        self.assertEqual(
            pair["weather_sync"]["high_plus"]["weather_record"]["source_row"],
            6401,
        )


if __name__ == "__main__":
    unittest.main()

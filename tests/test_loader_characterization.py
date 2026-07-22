"""Characterization coverage for the inherited VBOX coastdown loader."""

from contextlib import chdir
from datetime import date, datetime
import builtins
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import pandas as pd

from data.loaders import _read_text_lines, carregar_dados_csv_robusto


ROOT_DIR = Path(__file__).resolve().parents[1]
STANDARD_SAMPLE = ROOT_DIR / "sample_data" / "Standard" / "ExemploCSV1_Coastdown.csv"
SPLIT_SAMPLE = (
    ROOT_DIR / "sample_data" / "Split" / "coastdown" / "split eliezer high.csv"
)
WORK_DIR = ROOT_DIR / ".tmp_loader_characterization_tests"


def _vbox_content(
    *,
    delimiter=",",
    first_line="Test Date: 22/04/2024 15:49",
    date_value="22-Apr-2024",
    start_time="18:47:17.147",
    interval_values=("4.25", "4.50"),
    include_header=True,
    header_fields=None,
):
    metadata = [
        first_line,
        f"Time zone{delimiter}E. South America Standard Time",
        f"Test Date{delimiter}{date_value}",
        "Trigger",
        f"Requires Trigger{delimiter}Off",
        f"Trigger Channel{delimiter}",
        "Deceleration",
        f"Ignore runs that exceed (g){delimiter}0.20",
        f"Smooth Level{delimiter}4",
        "Speed Quality",
        f"Check{delimiter}Off",
        f"Speed threshold (km/h){delimiter}0.10",
        f"In (s){delimiter}0.05",
        "",
    ]
    if not include_header:
        return "\n".join(metadata)

    header = header_fields or [
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
    ]
    row = [
        "On",
        "+",
        "1",
        "8.75",
        "500",
        start_time,
        "0.10",
        *interval_values,
        "ação",
    ]
    return "\n".join([*metadata, delimiter.join(header), delimiter.join(row)])


class LoaderCharacterizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK_DIR.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def setUp(self):
        self.temp_path = WORK_DIR / self._testMethodName
        self.temp_path.mkdir(exist_ok=True)
        self._chdir = chdir(self.temp_path)
        self._chdir.__enter__()

    def tearDown(self):
        self._chdir.__exit__(None, None, None)
        shutil.rmtree(self.temp_path, ignore_errors=True)

    def _write(self, content, *, encoding="utf-8", name="fixture.csv"):
        path = self.temp_path / name
        path.write_bytes(content.encode(encoding))
        return path

    def test_raw_text_reader_preserves_tolerant_line_behavior(self):
        path = self.temp_path / "raw.txt"
        path.write_bytes(b"first\r\ninvalid:\xff\n")

        self.assertEqual(_read_text_lines(path), ["first\n", "invalid:\n"])

    def test_raw_text_reader_preserves_read_errors(self):
        path = self.temp_path / "unreadable.txt"

        with patch("builtins.open", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(PermissionError, "denied"):
                _read_text_lines(path)

    def test_known_standard_sample_output(self):
        frame, runs, test_date = carregar_dados_csv_robusto(str(STANDARD_SAMPLE))

        self.assertEqual(frame.shape, (10, 22))
        self.assertEqual(test_date, date(2025, 5, 14))
        self.assertEqual(sorted(runs), list(range(1, 11)))
        self.assertEqual(runs[1]["heading"], "+")
        self.assertEqual(
            runs[1]["start_timestamp"],
            datetime(2025, 5, 14, 12, 26, 21, 614000),
        )
        self.assertEqual(runs[1]["velocities"], [100.0 - 5.0 * i for i in range(15)])
        self.assertEqual(runs[1]["times"][:4], [0.0, 4.44, 9.0, 16.33])

    def test_known_split_sample_output(self):
        frame, runs, test_date = carregar_dados_csv_robusto(
            str(SPLIT_SAMPLE),
            using_split_method=True,
        )

        self.assertEqual(frame.shape, (20, 13))
        self.assertEqual(test_date, date(2024, 4, 22))
        self.assertEqual(sorted(runs), list(range(1, 21)))
        self.assertEqual(
            [item["time_s"] for item in runs[1]["interval_measurements"]],
            [4.23, 4.56, 4.81, 5.12, 5.67],
        )

    def test_comma_delimiter_and_decimal_point_are_accepted(self):
        path = self._write(_vbox_content())

        frame, runs, _ = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
        )

        self.assertEqual(frame.shape, (1, 10))
        self.assertEqual(
            [item["time_s"] for item in runs[1]["interval_measurements"]],
            [4.25, 4.5],
        )

    def test_semicolon_data_delimiter_is_currently_rejected(self):
        path = self._write(_vbox_content(delimiter=";"))

        with self.assertRaisesRegex(ValueError, "Colunas essenciais não encontradas"):
            carregar_dados_csv_robusto(str(path), using_split_method=True)

    def test_quoted_decimal_comma_interval_values_are_accepted(self):
        path = self._write(
            _vbox_content(interval_values=('"4,25"', '"4,50"'))
        )

        _, runs, _ = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
        )

        self.assertEqual(
            [item["time_s"] for item in runs[1]["interval_measurements"]],
            [4.25, 4.5],
        )

    def test_utf8_and_iso_8859_1_inputs_are_accepted(self):
        for encoding in ("utf-8", "iso-8859-1"):
            with self.subTest(encoding=encoding):
                path = self._write(
                    _vbox_content(),
                    encoding=encoding,
                    name=f"{encoding}.csv",
                )

                frame, runs, _ = carregar_dados_csv_robusto(
                    str(path),
                    using_split_method=True,
                )

                self.assertEqual(frame.iloc[0]["notes"], "ação")
                self.assertEqual(len(runs), 1)

    def test_missing_header_row_keeps_current_generic_error(self):
        path = self._write(_vbox_content(include_header=False))

        with self.assertRaisesRegex(
            ValueError,
            "Erro inesperado ao processar.*list index out of range",
        ):
            carregar_dados_csv_robusto(str(path))

    def test_missing_required_column_keeps_current_validation_error(self):
        header = [
            "Run-Use",
            "Run",
            "Time (s)",
            "Distance (m)",
            "Start Time",
            "Max Decel (g)",
            "90-85",
            "85-80",
            "Notes",
        ]
        path = self._write(_vbox_content(header_fields=header))

        with self.assertRaisesRegex(
            ValueError,
            r"Colunas essenciais não encontradas.*heading",
        ):
            carregar_dados_csv_robusto(str(path))

    def test_ambiguous_day_first_date_keeps_current_interpretation(self):
        path = self._write(
            _vbox_content(
                first_line="Test Date: 01/02/2024 03:04",
                date_value="",
            )
        )

        _, _, test_date = carregar_dados_csv_robusto(str(path))

        self.assertEqual(test_date, date(2024, 2, 1))

    def test_invalid_date_keeps_current_validation_error(self):
        path = self._write(
            _vbox_content(
                first_line="Test Date: 31/02/2024 03:04",
                date_value="not-a-date",
            )
        )

        with self.assertRaisesRegex(ValueError, "Não foi possível encontrar a 'Test Date'"):
            carregar_dados_csv_robusto(str(path))

    def test_invalid_run_time_is_retained_with_no_timestamp(self):
        path = self._write(_vbox_content(start_time="not-a-time"))

        _, runs, _ = carregar_dados_csv_robusto(str(path), using_split_method=True)

        self.assertEqual(runs[1]["start_time_str"], "not-a-time")
        self.assertIsNone(runs[1]["start_timestamp"])

    def test_empty_file_keeps_current_missing_date_error(self):
        path = self._write("")

        with self.assertRaisesRegex(ValueError, "Não foi possível encontrar a 'Test Date'"):
            carregar_dados_csv_robusto(str(path))

    def test_read_failure_keeps_current_translated_error(self):
        path = self._write(_vbox_content())
        real_open = builtins.open

        def fail_fixture_reads(file, mode="r", *args, **kwargs):
            if (
                isinstance(file, (str, os.PathLike))
                and Path(file).resolve() == path.resolve()
                and "r" in mode
            ):
                raise PermissionError("fixture cannot be read")
            return real_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=fail_fixture_reads):
            with self.assertRaisesRegex(
                ValueError,
                "Não foi possível encontrar a 'Test Date'",
            ):
                carregar_dados_csv_robusto(str(path))

    def test_is_alta_true_false_and_omitted_are_equivalent(self):
        path = self._write(_vbox_content())

        true_result = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
            is_alta=True,
        )
        false_result = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
            is_alta=False,
        )
        omitted_result = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
        )

        pd.testing.assert_frame_equal(true_result[0], false_result[0])
        pd.testing.assert_frame_equal(true_result[0], omitted_result[0])
        self.assertEqual(true_result[1:], false_result[1:])
        self.assertEqual(true_result[1:], omitted_result[1:])


if __name__ == "__main__":
    unittest.main()

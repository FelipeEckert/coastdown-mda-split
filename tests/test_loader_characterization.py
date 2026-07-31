"""Characterization coverage for the inherited VBOX coastdown loader."""

from contextlib import chdir
from datetime import date, datetime
import builtins
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from data.loaders import (
    _parse_coastdown_test_header,
    _read_text_lines,
    _validate_coastdown_columns,
    carregar_dados_csv_robusto,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
STANDARD_SAMPLE = ROOT_DIR / "sample_data" / "Standard" / "ExemploCSV1_Coastdown.csv"
STANDARD_LEGACY_SAMPLE = (
    ROOT_DIR / "sample_data" / "Standard" / "ExemploCSV2_Coastdown.csv"
)
SPLIT_COASTDOWN_DIR = ROOT_DIR / "sample_data" / "Split" / "coastdown"
SPLIT_COASTDOWN_EXPECTATIONS = {
    "altas ioniq.csv": (13, 13),
    "altas ioniq_16012026.csv": (20, 20),
    "baixas ioniq.csv": (16, 16),
    "baixas ioniq_16012026.csv": (20, 20),
    "ford-HighSpeed-ok.csv": (14, 14),
    "Ford-LowSpeed-ok.csv": (18, 18),
    "intercalado ioniq_16012026.csv": (20, 20),
    "spli_MrLee_LowSpd_ctvi.csv": (20, 20),
    "split eliezer high.csv": (20, 20),
    "split eliezer low.csv": (20, 20),
    "split_MrLee_HighSpd_ctvi.csv": (20, 20),
}


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


class CoastdownTestHeaderTests(unittest.TestCase):
    def test_line_3_date_formats_and_delimiters_keep_precedence(self):
        cases = (
            ("Test Date,22-Apr-2024", date(2024, 4, 22)),
            ("Test Date;22-Apr-24", date(2024, 4, 22)),
        )

        for third_line, expected_date in cases:
            with self.subTest(third_line=third_line):
                debug_output = []
                result = _parse_coastdown_test_header(
                    ["not a Test Date", "metadata", third_line], debug_output
                )

                self.assertEqual(result, (expected_date, None))
                self.assertIn(
                    f"Delimitador detectado para linha 3: "
                    f"'{';' if ';' in third_line else ','}'",
                    debug_output,
                )

    def test_line_1_fallback_keeps_date_and_time_formats(self):
        cases = (
            (
                ["Test Date: 22/04/2024", "metadata", "Test Date,"],
                date(2024, 4, 22),
                None,
            ),
            (
                ["Test Date: 22/04/2024 15:49", "metadata", "Test Date,"],
                date(2024, 4, 22),
                datetime(2024, 4, 22, 15, 49),
            ),
            (
                ["Test Date: 22/04/2024 15:49:30"],
                date(2024, 4, 22),
                datetime(2024, 4, 22, 15, 49, 30),
            ),
            (
                ["Test Date:22/04/2024 15:49"],
                date(2024, 4, 22),
                datetime(2024, 4, 22, 15, 49),
            ),
        )

        for lines, expected_date, expected_start in cases:
            with self.subTest(lines=lines):
                result = _parse_coastdown_test_header(lines, [])

                self.assertEqual(result, (expected_date, expected_start))

    def test_line_3_date_and_line_1_time_keep_two_pass_order(self):
        debug_output = []

        result = _parse_coastdown_test_header(
            [
                "Test Date: 23/04/2024 15:49:30",
                "metadata",
                "Test Date,22-Apr-2024",
            ],
            debug_output,
        )

        self.assertEqual(
            result,
            (date(2024, 4, 22), datetime(2024, 4, 23, 15, 49, 30)),
        )
        self.assertNotIn(
            "Tentando fallback: Conteúdo da linha 1 (índice 0): "
            "'Test Date: 23/04/2024 15:49:30'",
            debug_output,
        )

    def test_invalid_line_1_date_keeps_line_3_date_for_time_fallback(self):
        result = _parse_coastdown_test_header(
            [
                "Test Date: 31/02/2024 03:04",
                "metadata",
                "Test Date,22-Apr-2024",
            ],
            [],
        )

        self.assertEqual(
            result,
            (date(2024, 4, 22), datetime(2024, 4, 22, 3, 4)),
        )

        debug_output = []
        result = _parse_coastdown_test_header(
            [
                "Test Date: 31/02/2024 03:04:05",
                "metadata",
                "Test Date,22-Apr-2024",
            ],
            debug_output,
        )
        self.assertEqual(result, (date(2024, 4, 22), None))
        self.assertTrue(
            any("ERRO compondo hora com test_date" in line for line in debug_output)
        )

    def test_malformed_and_missing_headers_keep_current_diagnostics(self):
        cases = (
            (
                [],
                "ERRO: Arquivo tem menos de 3 linhas. Não foi possível ler a "
                "linha 3 para a data.",
            ),
            (
                ["not a Test Date", "metadata", "Test Date"],
                "  -> ERRO: Linha 3 não tem colunas suficientes para extrair "
                "a data da coluna B. Partes: ['Test Date']",
            ),
            (
                ["not a Test Date", "metadata", "Test Date,"],
                "  -> A parte da data da Linha 3, Coluna B está vazia.",
            ),
            (
                ["Test Date: 31/02/2024 03:04", "metadata", "Test Date,bad"],
                "  -> (2ª passada) ERRO parse data linha 1: day is out of range "
                "for month",
            ),
            (
                ["test date: 22/04/2024", "metadata", "Test Date,bad"],
                "  -> (2ª passada) Linha 1 não bateu com regex de Test Date.",
            ),
        )

        for lines, expected_diagnostic in cases:
            with self.subTest(lines=lines):
                debug_output = []

                self.assertEqual(
                    _parse_coastdown_test_header(lines, debug_output),
                    (None, None),
                )
                self.assertIn(expected_diagnostic, debug_output)

    def test_unexpected_metadata_errors_keep_each_pass_isolated(self):
        class BadLine:
            def strip(self):
                raise RuntimeError("bad metadata")

        debug_output = []
        recovered = _parse_coastdown_test_header(
            ["Test Date: 22/04/2024 15:49", "metadata", BadLine()],
            debug_output,
        )
        self.assertEqual(
            recovered,
            (date(2024, 4, 22), datetime(2024, 4, 22, 15, 49)),
        )
        self.assertIn(
            "ERRO inesperado ao tentar extrair a data do cabeçalho: bad metadata",
            debug_output,
        )

        debug_output = []
        retained = _parse_coastdown_test_header(
            [BadLine(), "metadata", "Test Date,22-Apr-2024"], debug_output
        )
        self.assertEqual(retained, (date(2024, 4, 22), None))
        self.assertIn(
            "  -> (2ª passada) ERRO inesperado: bad metadata",
            debug_output,
        )


class LoaderCharacterizationTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self._temp_dir.name)
        self._chdir = chdir(self.temp_path)
        self._chdir.__enter__()

    def tearDown(self):
        self._chdir.__exit__(None, None, None)
        self._temp_dir.cleanup()

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

    def test_normalized_column_validation_keeps_current_alias_mapping(self):
        columns = [
            "runuse",
            "heading",
            "run_num",
            "times",
            "distancem",
            "starttime",
            "maxdecelg",
            "notes_0",
            "unexpected",
        ]

        self.assertEqual(
            _validate_coastdown_columns(columns, []),
            {
                "run_use": "runuse",
                "run": "run_num",
                "time_s": "times",
                "distance_m": "distancem",
                "start_time": "starttime",
                "max_decel_g": "maxdecelg",
                "heading": "heading",
                "notes": "notes_0",
            },
        )

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

    def test_known_standard_legacy_duplicate_column_layout(self):
        frame, runs, test_date = carregar_dados_csv_robusto(
            str(STANDARD_LEGACY_SAMPLE)
        )

        self.assertEqual(frame.shape, (12, 24))
        self.assertEqual(len(runs), 12)
        self.assertEqual(test_date, date(2024, 10, 24))
        self.assertEqual(
            list(frame.columns[7:9]),
            ["speed_at_end_kmh", "speed_at_end_kmh_0"],
        )

    def test_all_split_coastdown_samples_load_with_expected_shapes(self):
        for filename, (row_count, run_count) in SPLIT_COASTDOWN_EXPECTATIONS.items():
            with self.subTest(filename=filename):
                frame, runs, test_date = carregar_dados_csv_robusto(
                    str(SPLIT_COASTDOWN_DIR / filename),
                    using_split_method=True,
                )

                self.assertEqual(len(frame), row_count)
                self.assertEqual(len(runs), run_count)
                self.assertIsInstance(test_date, date)
                self.assertTrue(
                    {"runuse", "heading", "run", "start_time"}.issubset(frame.columns)
                )
                first_run = runs[min(runs)]
                self.assertIsInstance(first_run["start_timestamp"], datetime)
                self.assertIsInstance(
                    first_run["interval_measurements"][0]["time_s"],
                    float,
                )

    def test_comma_delimiter_and_decimal_point_are_accepted(self):
        path = self._write(_vbox_content())

        frame, runs, _ = carregar_dados_csv_robusto(
            str(path),
            using_split_method=True,
        )

        self.assertEqual(frame.shape, (1, 10))
        self.assertEqual(
            list(frame.columns),
            [
                "runuse",
                "heading",
                "run",
                "time_s",
                "distance_m",
                "start_time",
                "max_decel_g",
                "9085",
                "8580",
                "notes",
            ],
        )
        self.assertEqual(
            [item["time_s"] for item in runs[1]["interval_measurements"]],
            [4.25, 4.5],
        )

    def test_bom_whitespace_and_capitalization_keep_current_column_names(self):
        header = [
            "\ufeffRUN-USE",
            " Heading ",
            "RUN",
            "Time (S)",
            "Distance (M)",
            "START TIME",
            "MAX DECEL (G)",
            "90-85",
            "85-80",
            "Notes",
        ]
        path = self._write(_vbox_content(header_fields=header))

        with patch("builtins.print") as print_mock:
            frame, _, _ = carregar_dados_csv_robusto(
                str(path),
                using_split_method=True,
            )

        print_mock.assert_not_called()
        self.assertEqual(
            list(frame.columns[:7]),
            [
                "runuse",
                "heading",
                "run",
                "time_s",
                "distance_m",
                "start_time",
                "max_decel_g",
            ],
        )

    def test_empty_duplicate_and_unexpected_columns_keep_order_without_warning(self):
        header = [
            "Run-Use",
            "Heading",
            "Run",
            "Time (s)",
            "Distance (m)",
            "Start Time",
            "Max Decel (g)",
            "",
            "",
            "Notes",
            "Unexpected",
            "Unexpected",
        ]
        path = self._write(_vbox_content(header_fields=header))

        with patch("builtins.print") as print_mock:
            frame, _, _ = carregar_dados_csv_robusto(
                str(path),
                using_split_method=True,
            )

        print_mock.assert_not_called()
        self.assertEqual(
            list(frame.columns[7:]),
            ["unnamed_col_0", "unnamed_col_1", "notes", "unexpected", "unexpected_0"],
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

        with patch("builtins.print") as print_mock:
            with self.assertRaises(ValueError) as context:
                carregar_dados_csv_robusto(str(path))

        print_mock.assert_not_called()
        self.assertEqual(
            str(context.exception),
            "Colunas essenciais não encontradas após normalização: ['heading']. "
            "Colunas detectadas: ['runuse', 'run', 'time_s', 'distance_m', "
            "'start_time', 'max_decel_g', '9085', '8580', 'notes']",
        )

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

        debug_text = (self.temp_path / "debug_vbox_date.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "ERRO inesperado ao tentar extrair a data do cabeçalho: "
            "fixture cannot be read",
            debug_text,
        )
        self.assertIn("  -> (2ª passada) ERRO inesperado:", debug_text)

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

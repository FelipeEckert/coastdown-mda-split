# coding: utf-8
"""Regression tests for the VBOX loader's former shared debug side effect."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir
from datetime import date, datetime
import builtins
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from data.loaders import carregar_dados_csv_robusto


ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLE_PATH = (
    ROOT_DIR / "sample_data" / "Split" / "coastdown" / "split eliezer high.csv"
)
DEBUG_FILENAME = "debug_vbox_date.txt"
WORK_DIR = ROOT_DIR / ".tmp_loader_debug_tests"


class LoaderDebugFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK_DIR.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def setUp(self):
        (WORK_DIR / DEBUG_FILENAME).unlink(missing_ok=True)

    def _parse_sample(self):
        return carregar_dados_csv_robusto(
            str(SAMPLE_PATH),
            using_split_method=True,
            is_alta=True,
        )

    def _assert_expected_output(self, result):
        frame, runs, test_date = result
        self.assertEqual(test_date, date(2024, 4, 22))
        self.assertEqual(frame.shape, (20, 13))
        self.assertEqual(sorted(runs), list(range(1, 21)))
        self.assertEqual(runs[1]["heading"], "+")
        self.assertEqual(
            runs[1]["start_timestamp"],
            datetime(2024, 4, 22, 18, 47, 17, 147000),
        )
        self.assertEqual(
            [item["time_s"] for item in runs[1]["interval_measurements"]],
            [4.23, 4.56, 4.81, 5.12, 5.67],
        )

    def test_successful_parse_does_not_create_debug_file(self):
        debug_path = WORK_DIR / DEBUG_FILENAME
        with chdir(WORK_DIR):
            self._parse_sample()

        self.assertFalse(debug_path.exists())

    def test_successful_parse_does_not_modify_existing_debug_file(self):
        debug_path = WORK_DIR / DEBUG_FILENAME
        original = b"existing support artifact"
        debug_path.write_bytes(original)

        with chdir(WORK_DIR):
            self._parse_sample()

        self.assertEqual(debug_path.read_bytes(), original)

    def test_successful_parse_when_relative_writes_are_denied(self):
        real_open = builtins.open

        def deny_relative_writes(file, mode="r", *args, **kwargs):
            path = os.fspath(file)
            if not os.path.isabs(path) and any(flag in mode for flag in "wax+"):
                raise PermissionError("working directory is read-only")
            return real_open(file, mode, *args, **kwargs)

        with chdir(WORK_DIR), patch(
            "builtins.open",
            side_effect=deny_relative_writes,
        ):
            self._parse_sample()

    def test_concurrent_parses_do_not_use_shared_debug_state(self):
        debug_path = WORK_DIR / DEBUG_FILENAME
        with chdir(WORK_DIR), ThreadPoolExecutor(
            max_workers=4
        ) as executor:
            list(executor.map(lambda _: self._parse_sample(), range(4)))

        self.assertFalse(debug_path.exists())

    def test_parser_outputs_remain_equivalent_to_expected_sample(self):
        with chdir(WORK_DIR):
            result = self._parse_sample()

        self._assert_expected_output(result)


if __name__ == "__main__":
    unittest.main()

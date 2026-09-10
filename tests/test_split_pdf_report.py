"""Checks for the presentation-only PDF scaffold (no PDF rendering)."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import unittest

from reportlab.lib.units import mm

from reports.report_styles import PAGE_MARGIN, PAGE_SIZE, build_report_styles
from reports.split_pdf_report import export_split_final_results_to_pdf


class SplitPdfScaffoldTests(unittest.TestCase):
    def test_landscape_print_styles_are_independent(self):
        self.assertEqual(PAGE_SIZE, (297 * mm, 210 * mm))
        self.assertEqual(PAGE_MARGIN, 15 * mm)
        first, second = build_report_styles(), build_report_styles()
        self.assertEqual(second["Body"].fontSize, 10)
        self.assertEqual(second["Table"].fontSize, 9)
        self.assertEqual(second["TableHeader"].fontName, "Helvetica-Bold")
        first["Body"].fontSize = 30
        self.assertEqual(second["Body"].fontSize, 10)

    def test_stub_accepts_optional_test_metadata_without_mutation(self):
        inputs = dict(
            final_results={"selected_pairs": [], "mean_f0": 123.456},
            vehicle_data={"model": "Example"}, deviation_analysis={},
            graph_series=[], test_name="Example test",
            generated_at=datetime(2026, 9, 10, 12),
        )
        for extra in ({}, {"test_metadata": None}, {"test_metadata": {
            "test_date": "2026-09-09", "operator": "Operator",
            "equipment": {"logger": "Example logger"},
        }}):
            with self.subTest(extra=extra):
                snapshot = {**inputs, **extra}
                before = deepcopy(snapshot)
                with self.assertRaisesRegex(
                    NotImplementedError, "Split PDF rendering is not implemented yet",
                ):
                    export_split_final_results_to_pdf(**snapshot)
                self.assertEqual(snapshot, before)

    def test_imports_and_stub_do_not_load_application_logic(self):
        result = subprocess.run(
            [sys.executable, "-c", """
import sys
from datetime import datetime

class Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition('.')[0] in {'streamlit', 'core', 'data', 'pages', 'utils'}:
            raise AssertionError('Reporting imported application logic: ' + fullname)

sys.meta_path.insert(0, Blocker())
import reports
from reports.report_styles import build_report_styles
from reports.split_pdf_report import export_split_final_results_to_pdf
build_report_styles()
try:
    export_split_final_results_to_pdf(
        final_results={}, vehicle_data={}, deviation_analysis={}, graph_series=[],
        test_name='Test', generated_at=datetime(2026, 9, 10),
    )
except NotImplementedError:
    pass
else:
    raise AssertionError('Scaffold unexpectedly rendered a report')
"""],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

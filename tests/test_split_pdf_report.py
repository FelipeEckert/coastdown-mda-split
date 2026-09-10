"""Page 1 PDF checks. Inspection dependency: python -m pip install pypdf."""

from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import unittest

from pypdf import PdfReader
from reportlab.lib.units import mm

from reports.report_styles import PAGE_MARGIN, PAGE_SIZE, build_report_styles
from reports.split_pdf_report import export_split_final_results_to_pdf


def sample_inputs():
    """Synthetic supplied values for tests and the clearly labeled QA sample."""
    return dict(
        final_results={
            "selected_pairs": [{"id": f"example-{i}", "F0_mean": 999.0} for i in range(6)],
            "num_pairs": 6, "mean_f0": 139.4112, "mean_f2": 0.049859,
            "mean_energy": 0.1732, "cv_f0": 12.34, "cv_f2": 15.67,
            "conformity_status": "nonconforming", "warnings": [],
        },
        vehicle_data={
            "model": "Veículo de demonstração", "vin": "SYNTHETIC-001",
            "running_order_mass_kg": 1364.0, "test_mass_kg": 1500.0,
            "rotational_equivalent_mass_kg": 45.0, "effective_mass_kg": 1545.0,
        },
        deviation_analysis={"time_summary": {
            "passed": True, "cv_limit_pct": 2.5, "opposite_mean_limit_pct": 10.0,
            "groups": {key: {"cv_pct": value, "passed": True} for key, value in (
                ("high_plus", 1.21), ("high_minus", 1.42),
                ("low_plus", 1.15), ("low_minus", 1.36),
            )},
            "opposite_direction": {
                "high": {"diff_pct": 3.12, "passed": True},
                "low": {"diff_pct": 2.48, "passed": True},
            },
        }},
        graph_series=[], test_name="DEMONSTRAÇÃO - dados sintéticos / sem validade de ensaio",
        generated_at=datetime.fromisoformat("2026-09-10T14:30:00-03:00"),
        test_metadata={
            "test_date": "2026-09-09", "responsible_engineer": "Eng. Exemplo",
            "operator": "Operador Exemplo", "driver": "Condutor Exemplo",
            "location": "Pista de demonstração", "service_identifier": "DEMO-001",
            "report_identifier": "SPLIT-DEMO-001", "start_time": "09:00",
            "end_time": "09:45", "method": "Split / ABNT NBR 10312",
            "configuration": "High 90-70 km/h (ref. 80); Low 45-35 km/h (ref. 40); passo 5 km/h",
            "equipment": {"logger": "DEMO-DAQ", "meteo": "DEMO-MET"},
        },
    )


class SplitPdfReportTests(unittest.TestCase):
    def render(self, inputs):
        payload = export_split_final_results_to_pdf(**inputs)
        self.assertIsInstance(payload, bytes)
        self.assertTrue(payload.startswith(b"%PDF-"))
        reader = PdfReader(BytesIO(payload))
        self.assertEqual(len(reader.pages), 1)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.width), PAGE_SIZE[0], places=3)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.height), PAGE_SIZE[1], places=3)
        return reader, reader.pages[0].extract_text()

    def test_landscape_print_styles_are_independent(self):
        self.assertEqual(PAGE_SIZE, (297 * mm, 210 * mm))
        self.assertEqual(PAGE_MARGIN, 15 * mm)
        first, second = build_report_styles(), build_report_styles()
        self.assertEqual(second["Body"].fontSize, 10)
        self.assertEqual(second["Table"].fontSize, 9)
        self.assertEqual(second["TableHeader"].fontName, "Helvetica-Bold")
        first["Body"].fontSize = 30
        self.assertEqual(second["Body"].fontSize, 10)

    def test_page_one_preserves_canonical_values_and_metadata(self):
        inputs = sample_inputs()
        inputs["final_results"]["selected_pairs"] = inputs["final_results"]["selected_pairs"][:1]
        before = deepcopy(inputs)
        _, text = self.render(inputs)
        self.assertEqual(inputs, before)
        for expected in (
            "139.4112", "0.049859", "0.1732", "12.34", "15.67", "1545.00",
            "1364.00", "1500.00", "45.00", "SPLIT-DEMO-001", "DEMO-DAQ",
            "2026-09-09", "09:00 / 09:45", "Eng. Exemplo / Operador Exemplo",
            "Condutor Exemplo", "Pista de demonstração", "Veículo de demonstração",
            "Página 1", "2026-09-10 14:30:00-03:00", "N/(km/h)²",
            "Validação normativa dos tempos", "Conforme", "Diagnóstico dos coeficientes",
            "CV de F0/F2 é diagnóstico", "High 90-70", "1.21", "3.12",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("999.0000", text)
        self.assertNotIn("Não conforme", text)
        self.assertIn("\n6\n", text)  # Do not infer the count from the pair fixture.

    def test_status_is_supplied_not_revalidated(self):
        for passed, label in ((True, "Conforming"), (False, "Nonconforming"),
                              (None, "Not evaluable (N/A)")):
            with self.subTest(passed=passed):
                inputs = sample_inputs()
                inputs["language"] = "en"
                inputs["deviation_analysis"]["time_summary"]["passed"] = passed
                # Deliberately inconsistent sentinels: rendering must not repair them.
                inputs["deviation_analysis"]["time_summary"]["groups"]["high_plus"] = {
                    "cv_pct": 99.25, "passed": True,
                }
                inputs["deviation_analysis"]["time_summary"]["cv_limit_pct"] = 1.23
                inputs["final_results"]["mean_f0"] = -123.4567
                _, text = self.render(inputs)
                self.assertIn("Normative time validation | " + label, text)
                self.assertIn("99.25 %", text)
                self.assertIn("Limit: 1.23 %", text)
                self.assertIn("-123.4567", text)
                self.assertIn("does not determine normative time conformity", text)

    def test_missing_optional_values_are_unavailable(self):
        inputs = sample_inputs()
        inputs.pop("test_metadata")
        inputs["vehicle_data"] = {"test_date": "1999-01-01"}
        inputs["final_results"] = {"selected_pairs": [], "mean_f0": float("nan"),
                                   "mean_f2": float("inf"), "mean_energy": None}
        inputs["deviation_analysis"] = {"time_summary": {}}
        _, text = self.render(inputs)
        self.assertIn("N/A", text)
        self.assertIn("Não avaliável", text)
        self.assertNotIn("1999-01-01", text)
        self.assertNotIn("nan", text.lower())
        inputs["test_metadata"] = None
        self.render(inputs)

    def test_metadata_markup_and_software_are_literal(self):
        inputs = sample_inputs()
        inputs["test_metadata"].update({
            "location": "Pista <b>A & B</b>",
            "software_name": "Example software", "software_version": "9.8.7",
        })
        reader, text = self.render(inputs)
        self.assertIn("Pista <b>A & B</b>", text)
        self.assertIn("Example software / 9.8.7", text)
        self.assertEqual(reader.metadata.creator, "Example software / 9.8.7")

    def test_invalid_structure_and_overflow_raise_readable_errors(self):
        for key, value, message in (
            ("final_results", {}, "selected_pairs"),
            ("deviation_analysis", {}, "time_summary"),
            ("test_metadata", [], "test_metadata"),
            ("generated_at", None, "generated_at"),
            ("language", "fr", "language"),
            ("test_metadata", {"location": "long metadata " * 2000}, "exceeds one page"),
        ):
            with self.subTest(key=key, message=message):
                inputs = sample_inputs()
                inputs[key] = value
                with self.assertRaisesRegex(ValueError, message):
                    export_split_final_results_to_pdf(**inputs)

    def test_rendering_does_not_load_application_logic(self):
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
payload = export_split_final_results_to_pdf(
    final_results={'selected_pairs': []}, vehicle_data={},
    deviation_analysis={'time_summary': {}}, graph_series=[],
    test_name='Test', generated_at=datetime(2026, 9, 10),
)
assert payload.startswith(b'%PDF-')
"""],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

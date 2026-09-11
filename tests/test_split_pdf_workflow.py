"""Metadata isolation, dialog interaction and canonical PDF handoff checks."""

from copy import deepcopy
from io import BytesIO
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

from reports.split_pdf_report import export_split_final_results_to_pdf
from tests.test_split_pdf_report import sample_run_inputs
from translations import get_translator
from utils.split_pdf_workflow import pdf_metadata, prefill_report_metadata


APP = '''
import streamlit as st
from tests.test_split_pdf_report import sample_run_inputs
from translations import get_translator
from utils.split_pdf_workflow import render_pdf_export
st.session_state.setdefault("tests", {
    "A": {"name": "Test A", "test_metadata": {"location": "Track A"}},
    "B": {"name": "Test B", "test_metadata": {"location": "Track B"}},
})
st.session_state.active_test_id = st.selectbox("Active test", ["A", "B"])
st.session_state.language = st.selectbox("Language", ["pt", "en"])
st.session_state.vehicle_info = {"test_date": "2026-09-11"}
st.session_state.split_interval_config = {
    "high": {"start": 101, "end": 87, "reference": 94},
    "low": {"start": 63, "end": 49, "reference": 56}, "step_kmh": 7,
}
inputs = sample_run_inputs()
render_pdf_export(inputs["final_results"], inputs["vehicle_data"],
                  inputs["deviation_analysis"], get_translator(st.session_state.language))
'''


class SplitPdfWorkflowTests(unittest.TestCase):
    def test_prefill_preserves_saved_blanks_and_canonical_configuration(self):
        test = {"driver": "Driver", "location": "Old", "equipment": {"logger": "DAQ"},
                "test_metadata": {"location": "", "operator": "N/A", "configuration": "old"}}
        state = {"vehicle_info": {"test_date": "2026-09-11"},
                 "split_interval_config": {"step_kmh": 3}}
        before = deepcopy((test, state))
        metadata = prefill_report_metadata(test, state)
        self.assertEqual(metadata["driver"], "Driver")
        self.assertEqual(metadata["location"], "")
        self.assertEqual(metadata["operator"], "N/A")
        self.assertEqual(metadata["equipment"]["logger"], "DAQ")
        self.assertEqual(metadata["configuration"], {"step_kmh": 3})
        self.assertEqual((test, state), before)

    def test_blank_metadata_generates_pdf_in_both_languages(self):
        for language, missing in (("pt", "Não informado"), ("en", "Not provided")):
            inputs = sample_run_inputs()
            inputs["language"] = language
            metadata = prefill_report_metadata({}, {"split_interval_config": {
                "high": {"start": 101, "end": 87, "reference": 94},
                "low": {"start": 63, "end": 49, "reference": 56}, "step_kmh": 7,
            }})
            metadata["operator"] = "N/A"
            metadata["comments"] = "Short comment"
            inputs["test_metadata"] = pdf_metadata(metadata, get_translator(language))
            reader = PdfReader(BytesIO(export_split_final_results_to_pdf(**inputs)))
            self.assertEqual(len(reader.pages), 3)
            text = reader.pages[0].extract_text()
            self.assertIn(missing, text)
            self.assertIn("N/A", text)
            self.assertIn("Short comment", text)

    def test_dialog_prefill_save_switch_language_and_explicit_generation(self):
        app = AppTest.from_string(APP, default_timeout=20).run()
        with patch("utils.split_pdf_workflow.export_split_final_results_to_pdf",
                   wraps=export_split_final_results_to_pdf) as export:
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.text_input(key="split_pdf_A_location").value, "Track A")
            self.assertEqual(app.text_input(key="split_pdf_A_test_date").value, "2026-09-11")
            self.assertTrue(app.text_input(key="split_pdf_A_test_date").disabled)
            app.text_input(key="split_pdf_A_driver").set_value("Driver A").run()
            self.assertEqual(app.session_state["tests"]["A"]["test_metadata"]["driver"], "Driver A")
            self.assertNotIn("configuration", app.session_state["tests"]["A"]["test_metadata"])
            self.assertEqual(app.session_state["tests"]["B"]["test_metadata"], {"location": "Track B"})
            export.assert_not_called()
            next(button for button in app.button if button.label == "Gerar PDF").click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(export.call_count, 1)
            supplied = export.call_args.kwargs
            self.assertEqual(supplied["test_metadata"]["driver"], "Driver A")
            self.assertEqual(supplied["final_results"], sample_run_inputs()["final_results"])
            self.assertTrue(app.get("download_button"))
            self.assertEqual(supplied["test_metadata"]["comments"], "")
            pdf = PdfReader(BytesIO(export_split_final_results_to_pdf(**supplied)))
            self.assertIn("Comentários: Não informado", pdf.pages[0].extract_text())
            app.selectbox[0].select("B").run()
            app.selectbox[1].select("en").run()
            app.button[0].click().run()
            self.assertEqual(app.text_input(key="split_pdf_B_location").value, "Track B")
            self.assertEqual(app.text_input(key="split_pdf_B_driver").value, "")
            self.assertTrue(any(button.label == "Generate PDF" for button in app.button))
            app.selectbox[0].select("A").run()
            app.button[0].click().run()
            self.assertEqual(app.text_input(key="split_pdf_A_driver").value, "Driver A")


if __name__ == "__main__":
    unittest.main()

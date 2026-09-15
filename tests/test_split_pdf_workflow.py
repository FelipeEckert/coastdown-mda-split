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
    def test_vehicle_vin_input_updates_canonical_vehicle_and_pdf_handoff(self):
        source = '''
import streamlit as st
from pages.page_2_dados_veiculo import render
from translations import get_translator
st.session_state.setdefault("active_test_id", "VIN-test")
st.session_state.setdefault("vehicle_info", {"vin": "Existing VIN"})
st.session_state.setdefault("data_loaded", True)
st.session_state.setdefault("total_mass", 0.0)
render(get_translator("en"))
'''
        app = AppTest.from_string(source, default_timeout=20).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="vehicle_vin_VIN-test").value, "Existing VIN")
        app.text_input(key="vehicle_vin_VIN-test").set_value("Updated VIN").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["vehicle_info"]["vin"], "Updated VIN")
        app.text_input(key="vehicle_vin_VIN-test").set_value("").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["vehicle_info"]["vin"], "")

    def test_prefill_uses_known_vehicle_equipment_and_split_identity(self):
        metadata = prefill_report_metadata({"method": "Standard"}, {
            "vehicle_info": {"equipment": {"logger": "DAQ", "vbox": "VBOX 3"},
                             "operator": "Known operator"}, "csv_test_date": "2024-04-22",
        })
        self.assertEqual(metadata["equipment"]["logger"], "DAQ")
        self.assertEqual(metadata["equipment"]["vbox"], "VBOX 3")
        self.assertEqual(metadata["operator"], "Known operator")
        self.assertEqual(metadata["method"], "Split")
        self.assertEqual(metadata["test_date"], "2024-04-22")
        self.assertEqual(metadata["start_time"], "")
        self.assertEqual(metadata["end_time"], "")
        partial = prefill_report_metadata({
            "equipment": {"logger": "DAQ", "vbox": "Known VBOX", "meteo": "Known station"},
            "test_metadata": {"equipment": {"logger": "", "weather_station": "N/A"}},
        }, {})
        self.assertEqual(partial["equipment"], {
            "logger": "", "vbox": "Known VBOX", "weather_station": "N/A",
        })

    def test_dialog_builds_current_selected_graphs_and_ignores_saved_series(self):
        from tests.test_split_pdf_integration import real_pipeline_inputs
        from utils.split_graphs import build_split_selected_plot_series
        inputs, state, _ = real_pipeline_inputs()
        app = AppTest.from_string(APP, default_timeout=30).run()
        app.session_state["split_input_sources"] = state["split_input_sources"]
        app.session_state["tests"]["A"]["graph_series"] = [{"stale": True}]
        with patch("utils.split_pdf_workflow.export_split_final_results_to_pdf", return_value=b"pdf") as export, patch(
            "tests.test_split_pdf_report.sample_run_inputs", return_value=inputs,
        ):
            app.button[0].click().run()
            next(button for button in app.button if button.label == "Gerar PDF").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(export.call_args.kwargs["graph_series"], build_split_selected_plot_series(
            inputs["final_results"]["selected_pairs"], state["split_input_sources"],
        ))

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

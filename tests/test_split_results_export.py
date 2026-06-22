# coding: utf-8
"""Tests for the pure final Split workbook exporter."""

from copy import deepcopy
import io
import unittest

from openpyxl import load_workbook

from data.split_exporters import export_split_final_results_to_excel


def _pair(pair_id, *, selected=True, temperature=25.0, wind=1.0):
    components = {}
    for index, component in enumerate(("high_plus", "low_plus", "high_minus", "low_minus"), 1):
        components[component] = {
            "run_id": index,
            "filename": None if component == "low_minus" else f"{component}.csv",
            "delta_t_s": 10.0 + index,
            "source_role": component.split("_")[0],
            "content_sha256": f"hash-{index}",
        }
    return {
        "id": pair_id,
        "selected": selected,
        "selection_source": "manual",
        **components,
        **{f"{component}_run": index for index, component in enumerate(components, 1)},
        **{f"{component}_delta_t_s": 10.0 + index for index, component in enumerate(components, 1)},
        "F0_mean": 100.0 if pair_id == "one" else 110.0,
        "F2_mean": 0.004 if pair_id == "one" else 0.0042,
        "energy": 1.25,
        "ambient_by_component": {
            component: {
                "temperature_c": temperature,
                "pressure_kpa": 101.3,
                "wind_speed_ms": wind,
                "sync_method": "nearest",
            }
            for component in components
        },
        "warnings": [],
    }


class SplitResultsExportTests(unittest.TestCase):
    def test_fixed_environmental_conditions_export_values_and_dash_wind(self):
        pair = _pair("fixed")
        pair["ambient_by_component"] = {}
        pair["environmental_conditions"] = {
            "mode": "fixed", "temperature_c": 23.0,
            "pressure_kpa": 100.5, "wind_speed_mps": None,
        }
        wb = self._workbook([pair])
        flat = [value for row in wb["Meteorologia"].iter_rows(values_only=True) for value in row]

        self.assertIn("23.0", flat)
        self.assertIn("100.5", flat)
        self.assertIn("-", flat)

    def _workbook(self, pairs):
        payload = export_split_final_results_to_excel(
            final_results={},
            selected_pairs=pairs,
            vehicle_data={"vehicle_info": {"model": "Carro", "effective_mass": 1500}, "total_mass": 1450},
        )
        self.assertGreater(len(payload), 1000)
        self.assertEqual(payload[:2], b"PK")
        return load_workbook(io.BytesIO(payload), data_only=True)

    def test_workbook_contains_expected_sheets_and_summary(self):
        wb = self._workbook([_pair("one"), _pair("two")])
        self.assertEqual(wb.sheetnames, [
            "Resumo Final", "Dados do Veículo", "Pares Selecionados",
            "Análise de Desvios", "Tempos deltaT", "Meteorologia", "Rastreabilidade",
        ])
        values = [cell.value for row in wb["Resumo Final"].iter_rows() for cell in row]
        self.assertIn("F0 final (N)", values)
        self.assertIn("F2 final (N/(km/h)²)", values)
        self.assertIn("CV F0 (%)", values)

    def test_only_explicitly_selected_pairs_are_exported_and_input_is_unchanged(self):
        pairs = [_pair("one"), _pair("hidden", selected=False)]
        before = deepcopy(pairs)
        wb = self._workbook(pairs)
        ws = wb["Pares Selecionados"]
        labels = [ws.cell(row, 1).value for row in range(3, ws.max_row + 1)]
        self.assertEqual(len(labels), 1)
        self.assertEqual(pairs, before)

    def test_missing_values_use_dash_and_weather_alerts_do_not_include_pressure(self):
        wb = self._workbook([_pair("one", temperature=36.0, wind=3.1)])
        pairs_ws = wb["Pares Selecionados"]
        all_values = [cell.value for row in pairs_ws.iter_rows() for cell in row]
        self.assertIn("-", all_values)
        weather_values = [cell.value for row in wb["Meteorologia"].iter_rows() for cell in row]
        alert = next(value for value in weather_values if isinstance(value, str) and "Vento acima" in value)
        self.assertIn("Temperatura acima de 35 °C", alert)
        self.assertNotIn("Pressão", alert)

    def test_delta_t_sheet_contains_opposite_direction_rows(self):
        wb = self._workbook([_pair("one"), _pair("two")])
        values = [cell.value for row in wb["Tempos deltaT"].iter_rows() for cell in row]
        self.assertIn("High", values)
        self.assertIn("Low", values)
        self.assertIn("Aprovado", values)

    def test_exporter_module_does_not_import_streamlit(self):
        import data.split_exporters as module
        self.assertNotIn("streamlit", module.__dict__)


if __name__ == "__main__":
    unittest.main()

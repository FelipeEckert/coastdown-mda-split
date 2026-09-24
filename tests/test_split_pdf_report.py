"""Split PDF checks. Inspection dependency: python -m pip install pypdf."""

from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.lib.units import mm

from reports.report_styles import PAGE_MARGIN, PAGE_SIZE, build_report_styles
from reports.split_pdf_report import LOGO_PATH, export_split_final_results_to_pdf


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


def sample_run_inputs():
    """Two selected pairs with explicit synthetic measured values and custom bins."""
    inputs = sample_inputs()
    pairs = []
    for pair_index in (1, 2):
        pair = {"id": f"demo-{pair_index}", "ambient_by_component": {}}
        for component in ("high_plus", "high_minus", "low_plus", "low_minus"):
            high = component.startswith("high")
            labels = ["101-94", "94-87"] if high else ["63-56", "56-49"]
            pair[component] = {
                "run_id": f"{pair_index}{component[0].upper()}{'+' if component.endswith('plus') else '-'}",
                "filename": "split_demo.csv", "start_time_str": "09:01:00",
                "subintervals": labels, "source_columns": labels,
                "subinterval_times_s": [7.431, 9.052] if high else [6.321, 7.102],
                "delta_t_s": 16.483 if high else 13.423,
            }
            pair["ambient_by_component"][component] = {
                "temperature_c": 25.6, "pressure_kpa": 101.32, "wind_speed_mps": 1.42,
                "source_file": "meteo_demo.csv", "weather_datetime": "09:01:02",
                "sync_method": "nearest_datetime", "time_delta_seconds": 2.0,
                "matched": True, "warnings": [],
            }
        pairs.append(pair)
    pairs[0]["ambient_by_component"]["low_minus"]["warnings"] = ["Horário meteo sem fuso declarado."]
    inputs["final_results"]["selected_pairs"] = pairs
    inputs["final_results"]["num_pairs"] = 2
    inputs["test_metadata"]["configuration"] = (
        "High 101-87 km/h (ref. 94); Low 63-49 km/h (ref. 56); passo 7 km/h"
    )
    # Explicit synthetic snapshots, including distinct curves for visual QA.
    run_points = {
        "1H+": ([7.431, 9.052], [0.0, 7.431, 16.483]),
        "1H-": ([7.9, 8.7], [0.0, 7.9, 16.6]),
        "2H+": ([8.3, 8.4], [0.0, 8.3, 16.7]),
        "2H-": ([8.8, 8.0], [0.0, 8.8, 16.8]),
        "1L+": ([6.321, 7.102], [0.0, 6.321, 13.423]),
        "1L-": ([6.7, 6.8], [0.0, 6.7, 13.5]),
        "2L+": ([7.1, 6.5], [0.0, 7.1, 13.6]),
        "2L-": ([7.5, 6.2], [0.0, 7.5, 13.7]),
    }
    for pair in pairs:
        for component in ("high_plus", "high_minus", "low_plus", "low_minus"):
            record = pair[component]
            high = component.startswith("high")
            subinterval_times, times = run_points[record["run_id"]]
            record["subinterval_times_s"] = subinterval_times
            record["delta_t_s"] = times[-1]
            inputs["graph_series"].append({
                "record": deepcopy(record), "interval_name": "high" if high else "low",
                "direction": "+" if component.endswith("plus") else "-",
                "times_s": times,
                "speeds_kmh": [101.0, 94.0, 87.0] if high else [63.0, 56.0, 49.0],
                "data_mode": "interval_curve", "interval_rows": [],
            })
    for pair, values in zip(pairs, (
        (138.2345, .049123, .1721, 140.5879, .050595, .1743, 139.4112, .049859, .1732),
        (136.2345, .048123, .1711, 142.5879, .051595, .1753, 139.4112, .049859, .1732),
    )):
        pair.update(zip(("F0_plus", "F2_plus", "energy_plus", "F0_minus", "F2_minus",
                         "energy_minus", "F0_mean", "F2_mean", "energy"), values))
    return inputs


class SplitPdfReportTests(unittest.TestCase):
    def render(self, inputs):
        payload = export_split_final_results_to_pdf(**inputs)
        self.assertIsInstance(payload, bytes)
        self.assertTrue(payload.startswith(b"%PDF-"))
        reader = PdfReader(BytesIO(payload))
        self.assertGreaterEqual(len(reader.pages), 3)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.width), PAGE_SIZE[0], places=3)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.height), PAGE_SIZE[1], places=3)
        return reader, reader.pages[0].extract_text()

    def test_landscape_print_styles_are_independent(self):
        self.assertEqual(PAGE_SIZE, (297 * mm, 210 * mm))
        self.assertEqual(PAGE_MARGIN, 8 * mm)
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

    def test_reference_layout_has_method_cards_and_report_footer(self):
        _, text = self.render(sample_inputs())
        for label in ("Método\n", "Configuração\n", "Equipamentos\n", "Página 1"):
            self.assertIn(label, text)
        # Both the test panel and footer retain the supplied report identification.
        self.assertEqual(text.count("DEMO-001 / SPLIT-DEMO-001"), 2)

    def test_local_logo_is_embedded_with_text_only_fallback(self):
        reader, _ = self.render(sample_inputs())
        self.assertEqual(len(reader.pages[0].images), 1 if LOGO_PATH.is_file() else 0)
        with patch("reports.split_pdf_report.LOGO_PATH", LOGO_PATH.with_name("missing_logo.png")):
            reader, text = self.render(sample_inputs())
        self.assertEqual(len(reader.pages[0].images), 0)
        self.assertIn("COASTDOWN MDA SPLIT", text)
        self.assertIn("RELATÓRIO TÉCNICO", text)

    def test_measured_page_preserves_times_and_hides_weather_traceability(self):
        inputs = sample_run_inputs()
        # Sentinels explicitly differ from interval sums and all pair-level values.
        inputs["final_results"]["selected_pairs"][0]["high_plus"]["delta_t_s"] = 123.456
        inputs["final_results"]["selected_pairs"][0]["temp_plus_used"] = 999.0
        before = deepcopy(inputs)
        reader, _ = self.render(inputs)
        self.assertEqual(inputs, before)
        self.assertEqual(len(reader.pages), 3)
        text = reader.pages[1].extract_text()
        for expected in ("Par 1", "Par 2", "High+", "Low+", "High-", "Low-",
                         "101-94", "94-87", "63-56", "56-49", "7.43", "123.46"):
            self.assertIn(expected, text)
        for hidden in ("split_demo.csv", "meteo_demo.csv", "09:01:02", "nearest_datetime",
                       "Horário meteo sem fuso declarado.", "sincronização"):
            self.assertNotIn(hidden, text)
        self.assertNotIn("999.0", text)
        self.assertNotIn("90-85", text)

    def test_identical_runs_collapse_but_different_sources_or_weather_do_not(self):
        inputs = sample_run_inputs()
        pair = inputs["final_results"]["selected_pairs"][0]
        inputs["graph_series"] = []
        inputs["final_results"]["selected_pairs"] = [pair, deepcopy(pair)]
        reader, _ = self.render(inputs)
        text = reader.pages[1].extract_text()
        self.assertEqual(text.count("1H+"), 2)
        inputs["final_results"]["selected_pairs"][1]["ambient_by_component"]["high_plus"]["temperature_c"] = 27.8
        reader, _ = self.render(inputs)
        text = reader.pages[1].extract_text()
        self.assertEqual(text.count("1H+"), 2)
        self.assertNotIn("27.8", text)
        inputs["final_results"]["selected_pairs"][1]["high_plus"]["filename"] = "another.csv"
        reader, _ = self.render(inputs)
        self.assertEqual(reader.pages[1].extract_text().count("1H+"), 2)

    def test_mapping_times_and_missing_run_weather_do_not_use_pair_averages(self):
        inputs = sample_run_inputs()
        pair = inputs["final_results"]["selected_pairs"][0]
        inputs["final_results"]["selected_pairs"] = [pair]
        pair["high_plus"]["subinterval_times_s"] = {"94-87": 8.123, "101-94": 6.456}
        pair["low_minus"].pop("subinterval_times_s")
        pair["ambient_by_component"] = {}
        pair["environmental_conditions"] = {"temperature_c": 888.8, "mode": "fixed"}
        pair["temp_plus_used"] = 888.8
        pair["weather_components"] = {"high_plus": {
            "temperature_c": 21.5, "pressure_kpa": 100.01, "wind_speed_ms": 0.55,
            "method": "saved_method", "source_timestamp": "09:02:00", "time_diff_s": 3.5,
        }}
        pair["low_plus"]["weather_sync"] = {"temperature": 22.6, "wind_speed": 0.77}
        reader, _ = self.render(inputs)
        text = reader.pages[1].extract_text()
        for expected in ("8.12", "6.46", "N/A"):
            self.assertIn(expected, text)
        self.assertNotIn("888.8", text)

    def test_dense_rows_and_wide_intervals_fail_without_clipping_or_page_three(self):
        inputs = sample_run_inputs()
        base = inputs["final_results"]["selected_pairs"][0]
        pairs = []
        for index in range(18):
            pair = deepcopy(base)
            pair["high_plus"]["run_id"] = f"run-{index}"
            pairs.append(pair)
        inputs["final_results"]["selected_pairs"] = pairs
        with self.assertRaisesRegex(ValueError, "Page 2"):
            export_split_final_results_to_pdf(**inputs)
        inputs = sample_run_inputs()
        record = inputs["final_results"]["selected_pairs"][0]["high_plus"]
        record["subintervals"] = [f"{113-i}-{112-i}" for i in range(9)]
        record["subinterval_times_s"] = [1.111] * 9
        with self.assertRaisesRegex(ValueError, "Page 2"):
            export_split_final_results_to_pdf(**inputs)

    def test_four_dynamic_subintervals_fit_the_compact_table(self):
        inputs = sample_run_inputs()
        record = inputs["final_results"]["selected_pairs"][0]["high_plus"]
        record["subintervals"] = ["98-94", "94-90", "90-86", "86-82"]
        record["subinterval_times_s"] = [1.111, 2.222, 3.333, 4.444]
        # All High rows use the same caller-configured columns.
        for pair in inputs["final_results"]["selected_pairs"]:
            for component in ("high_plus", "high_minus"):
                pair[component]["subintervals"] = record["subintervals"]
        reader, _ = self.render(inputs)
        self.assertEqual(len(reader.pages), 3)
        for value in (*record["subintervals"], "1.11", "2.22", "3.33", "4.44"):
            self.assertIn(value, reader.pages[1].extract_text())

    def test_vector_charts_preserve_exact_points_and_page_one(self):
        from reportlab.graphics.charts.lineplots import LinePlot
        from reports.split_pdf_report import _run_chart
        inputs = sample_run_inputs()
        baseline, _ = self.render(inputs)
        # Points deliberately unrelated to the table times: never reconstruct them.
        inputs["graph_series"][0]["times_s"] = [2.125, 4.625, 17.375]
        inputs["graph_series"][0]["speeds_kmh"] = [102.75, 95.25, 86.125]
        inputs["graph_series"][1]["data_mode"] = "aggregate"
        before = deepcopy(inputs)
        with patch("reports.split_pdf_report._run_chart", wraps=_run_chart) as draw:
            reader, _ = self.render(inputs)
        self.assertEqual(inputs, before)
        self.assertEqual(len(reader.pages), 3)
        self.assertEqual(reader.pages[0].get_contents().get_data(),
                         baseline.pages[0].get_contents().get_data())
        self.assertEqual(draw.call_count, 2)
        drawing = _run_chart(inputs["graph_series"], "high", 790, 160, "High", lambda pt, en: en)
        chart = next(item for item in drawing.contents if isinstance(item, LinePlot))
        self.assertEqual(chart.data[0], [(2.125, 102.75), (4.625, 95.25), (17.375, 86.125)])
        text = reader.pages[1].extract_text()
        for label in ("1H+", "1H-", "2L+", "2L-", "extremos", "Tempo [s]", "Velocidade [km/h]"):
            self.assertIn(label, text)
        self.assertEqual(len(reader.pages[1].images), 1 if LOGO_PATH.is_file() else 0)

    def test_invalid_graph_shapes_are_explicit_and_missing_graphs_are_unavailable(self):
        for changes in ({"times_s": [0]}, {"speeds_kmh": [1, float("nan"), 3]},
                        {"times_s": [0, True, 3]}, {"interval_name": "standard"},
                        {"record": None}, {"direction": "unknown"}):
            inputs = sample_run_inputs()
            inputs["graph_series"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                export_split_final_results_to_pdf(**inputs)
        inputs = sample_run_inputs()
        inputs["graph_series"] = []
        reader, _ = self.render(inputs)
        self.assertEqual(reader.pages[1].extract_text().count("Curvas indisponíveis (N/A)."), 2)

    def test_pair_page_uses_only_stored_corrected_values_and_preserves_earlier_pages(self):
        inputs = sample_run_inputs()
        baseline, _ = self.render(inputs)
        pair = inputs["final_results"]["selected_pairs"][0]
        pair.update(F0_plus=-123.4567, F2_plus=.012345, energy_plus=.1234,
                    F0_minus=234.5678, F2_minus=.067891, energy_minus=.2345,
                    F0_mean=345.6789, F2_mean=.078912, energy=.3456,
                    f0_prime_plus=9999.0, f2_prime_mean=8888.0)
        before = deepcopy(inputs)
        reader, _ = self.render(inputs)
        self.assertEqual(inputs, before)
        for index in (0, 1):
            self.assertEqual(reader.pages[index].get_contents().get_data(),
                             baseline.pages[index].get_contents().get_data())
        text = reader.pages[2].extract_text()
        for value in ("-123.4567", "0.012345", "0.1234", "234.5678", "0.067891",
                      "0.2345", "345.6789", "0.078912", "0.3456"):
            self.assertEqual(text.count(value), 2 if value in ("345.6789", "0.078912", "0.3456") else 1)
        for label in ("Pares e coeficientes | Split", "High+ | 1H+", "Low+ | 1L+",
                      "High- | 1H-", "Low- | 1L-", "Média", "Página 3", "N/(km/h)²"):
            self.assertIn(label, text)
        self.assertNotIn("9999", text)
        self.assertNotIn("8888", text)

    def test_pair_page_merges_directional_cells_and_keeps_missing_energy_unavailable(self):
        from reportlab.platypus import Paragraph
        from reports.split_pdf_report import _pair_tables
        inputs = sample_run_inputs()
        inputs["language"] = "en"
        pairs = inputs["final_results"]["selected_pairs"]
        pairs[0].pop("energy_plus")
        pairs[0].pop("energy_minus")
        reader, _ = self.render(inputs)
        text = reader.pages[2].extract_text()
        for label in ("Pairs and coefficients", "Corrected F0", "Corrected F2", "Mean", "N/A"):
            self.assertIn(label, text)
        self.assertNotIn("0.1721", text)
        self.assertNotIn("0.1743", text)
        styles = build_report_styles()
        story = _pair_tables(inputs["final_results"], PAGE_SIZE[0] - 2 * PAGE_MARGIN,
                             lambda text, style="Table": Paragraph(str(text), styles[style]),
                             lambda pt, en: en)
        block = story[0]._cellvalues[2][0][0]._cellvalues[0][0]
        for column in (1, 2, 3):
            for row in (2, 4):
                self.assertIn(("SPAN", (column, row), (column, row + 1)), block._spanCmds)
        inputs["final_results"]["selected_pairs"] = []
        reader, _ = self.render(inputs)
        self.assertIn("Pairs unavailable (N/A).", reader.pages[2].extract_text())

    def test_pair_page_supports_odd_blocks_and_continues_overflow(self):
        inputs = sample_inputs()
        inputs["final_results"]["selected_pairs"] = [{"id": f"pair-{i}"} for i in range(5)]
        reader, _ = self.render(inputs)
        self.assertIn("pair-4", reader.pages[2].extract_text())
        inputs["final_results"]["selected_pairs"] = [{"id": f"pair-{i}"} for i in range(20)]
        from reports.split_pdf_report import _run_tables
        # Isolate unlimited coefficient pagination from the fixed measured-page capacity.
        with patch("reports.split_pdf_report._run_tables", side_effect=lambda pairs, *args: _run_tables(pairs[:2], *args)):
            reader, _ = self.render(inputs)
        self.assertGreater(len(reader.pages), 3)
        self.assertIn("pair-19", reader.pages[-1].extract_text())

    def test_final_results_section_uses_supplied_consolidation_without_averaging(self):
        for language, title in (("pt", "Resultados finais"), ("en", "Final results")):
            inputs = sample_run_inputs()
            inputs["language"] = language
            inputs["final_results"].update(mean_f0=-765.4321, mean_f2=.123456, mean_energy=9.8765)
            inputs["final_results"]["selected_pairs"][1].update(
                F0_mean=142.4112, F2_mean=.051859, energy=.1772,
            )
            before = deepcopy(inputs)
            reader, _ = self.render(inputs)
            self.assertEqual(inputs, before)
            text = reader.pages[2].extract_text().split(title, 1)[1]
            for value in ("demo-1", "demo-2", "139.4112", "142.4112", "0.049859", "0.051859",
                          "0.1732", "0.1772", "-765.4321", "0.123456", "9.8765"):
                self.assertIn(value, text)
            self.assertIn("F0 final" if language == "pt" else "Final F0", text)
            self.assertIn("Energia final" if language == "pt" else "Final energy", text)
        inputs = sample_inputs()
        inputs["final_results"] = {"selected_pairs": []}
        reader, _ = self.render(inputs)
        text = reader.pages[2].extract_text().split("Resultados finais", 1)[1]
        self.assertEqual(text.count("N/A"), 3)

    def test_run_shape_errors_are_explicit(self):
        for labels, stored in ((["a", "a"], [1, 2]), (["a"], [1, 2]), ([1], [1])):
            with self.subTest(labels=labels, stored=stored):
                inputs = sample_run_inputs()
                inputs["final_results"]["selected_pairs"][0]["high_plus"].update(
                    subintervals=labels, subinterval_times_s=stored,
                )
                with self.assertRaises(ValueError):
                    export_split_final_results_to_pdf(**inputs)

    def test_measured_weather_rejects_fixed_and_unmatched_snapshots(self):
        from core.split_corrections import fixed_ambient_conditions
        from reports.split_pdf_report import _measured_runs
        inputs = sample_run_inputs()
        pair = inputs["final_results"]["selected_pairs"][0]
        measured = deepcopy(pair["ambient_by_component"])
        pair.update(fixed_ambient_conditions(99.8, 77.7))
        pair["weather_components"] = {"high_plus": measured["high_plus"]}
        pair["low_plus"]["weather_sync"] = measured["low_plus"]
        pair["weather_components"]["high_minus"] = {**measured["high_minus"], "matched": False}
        rows = _measured_runs([pair])
        self.assertEqual(rows["high"][0]["weather"], measured["high_plus"])
        self.assertEqual(rows["low"][0]["weather"], measured["low_plus"])
        self.assertEqual(rows["high"][1]["weather"], {})
        self.assertEqual(rows["low"][1]["weather"], {})
        reader, _ = self.render(inputs)
        text = reader.pages[1].extract_text()
        self.assertNotIn("99.8", text)
        self.assertNotIn("77.70", text)
        self.assertNotIn("Climate conditions", text)

    def test_run_page_translation_and_empty_sections(self):
        inputs = sample_run_inputs()
        inputs["language"] = "en"
        reader, _ = self.render(inputs)
        text = reader.pages[1].extract_text()
        for label in ("Measured data", "High+", "Low-", "Direction +", "Direction -", "Speed [km/h]", "Time [s]", "Page 2"):
            self.assertIn(label, text)
        inputs["final_results"]["selected_pairs"] = []
        reader, _ = self.render(inputs)
        self.assertEqual(len(reader.pages), 3)
        self.assertIn("N/A", reader.pages[1].extract_text())

    def test_invalid_structure_and_overflow_raise_readable_errors(self):
        for key, value, message in (
            ("final_results", {}, "selected_pairs"),
            ("deviation_analysis", {}, "time_summary"),
            ("test_metadata", [], "test_metadata"),
            ("generated_at", None, "generated_at"),
            ("language", "fr", "language"),
        ):
            with self.subTest(key=key, message=message):
                inputs = sample_inputs()
                inputs[key] = value
                with self.assertRaisesRegex(ValueError, message):
                    export_split_final_results_to_pdf(**inputs)

    def test_variable_pair_pages_and_localized_totals(self):
        for language in ("pt", "en"):
            for count in (1, 2, 5, 8, 20, 50):
                with self.subTest(language=language, count=count):
                    inputs = sample_run_inputs()
                    inputs["language"] = language
                    base = inputs["final_results"]["selected_pairs"][0]
                    pairs = [{**deepcopy(base), "id": f"selected-{i:03d}"} for i in range(count)]
                    inputs["final_results"].update(selected_pairs=pairs, num_pairs=count)
                    before = deepcopy(inputs)
                    from reports.split_pdf_report import _run_tables
                    # Page 2 card capacity is tested independently with the real pipeline.
                    with patch("reports.split_pdf_report._run_tables", side_effect=lambda pairs, *args: _run_tables(pairs[:2], *args)):
                        reader, _ = self.render(inputs)
                    self.assertEqual(inputs, before)
                    texts = [page.extract_text() for page in reader.pages]
                    prefix = "Par | " if language == "pt" else "Pair | "
                    positions = []
                    for pair in pairs:
                        matches = [i for i, text in enumerate(texts) if prefix + pair["id"] in text]
                        self.assertEqual(len(matches), 1)
                        positions.append(matches[0])
                        block = texts[matches[0]].split(prefix + pair["id"], 1)[1].split(prefix, 1)[0]
                        for value in ("High+", "Low+", "High-", "Low-", "0.1721", "0.1743"):
                            self.assertIn(value, block)
                    self.assertEqual(positions, sorted(positions))
                    final_title = "Resultados finais" if language == "pt" else "Final results"
                    final_page = next(i for i, text in enumerate(texts) if final_title in text)
                    self.assertGreaterEqual(final_page, positions[-1])
                    if count == 8:
                        self.assertGreater(final_page, positions[-1])
                    if count >= 20:
                        self.assertGreater(len(set(positions)), 1)
                    for i, text in enumerate(texts, 1):
                        footer = f"Página {i} de {len(texts)}" if language == "pt" else f"Page {i} of {len(texts)}"
                        self.assertIn(footer, text)
                    final_text = "\n".join(texts[final_page:]).split(final_title, 1)[1]
                    for pair in pairs:
                        self.assertEqual(final_text.count(pair["id"]), 1)
                    self.assertIn("0.1732", texts[-1])

    def test_long_optional_metadata_continues_without_loss(self):
        for language in ("pt", "en"):
            inputs = sample_run_inputs()
            inputs["language"] = language
            for key in ("location", "comments", "responsible_engineer", "report_identifier"):
                inputs["test_metadata"][key] = (key + " wrapped text ") * 400 + "END_" + key
            inputs["test_metadata"]["equipment"] = {"logger": "logger details " * 400 + "END_logger"}
            reader, first = self.render(inputs)
            texts = [page.extract_text() for page in reader.pages]
            self.assertIn("Resumo" if language == "pt" else "Results summary", first)
            self.assertIn("Dados medidos" if language == "pt" else "Measured data", texts[1])
            self.assertGreater(len(texts), 3)
            all_text = "\n".join(texts)
            for key in ("location", "comments", "responsible_engineer", "report_identifier", "logger"):
                self.assertIn("END_" + key, all_text)
            self.assertIn(f"{len(texts)}", texts[-1])

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

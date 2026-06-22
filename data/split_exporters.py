# coding: utf-8
"""Pure Excel export for final Split results."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import io
import math

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from core.split_deviation_analysis import analyze_split_selected_deviations
from core.split_display import format_run_option_label, format_split_pair_label
from core.split_results import consolidate_split_final_results


COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")
COMPONENT_LABELS = {
    "high_plus": "High [+]",
    "low_plus": "Low [+]",
    "high_minus": "High [-]",
    "low_minus": "Low [-]",
}
MISSING = "-"
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
WARNING_FILL = PatternFill("solid", fgColor="FFF3CD")
TITLE_FILL = PatternFill("solid", fgColor="D9EAF7")
THIN_BORDER = Border(*(Side(style="thin", color="B7B7B7") for _ in range(4)))


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _value(value):
    if value is None:
        return MISSING
    if isinstance(value, float) and not math.isfinite(value):
        return MISSING
    if isinstance(value, (list, tuple, set)):
        text = "; ".join(str(item) for item in value if str(item).strip())
        return text or MISSING
    if isinstance(value, dict):
        text = "; ".join(f"{key}: {_value(item)}" for key, item in value.items())
        return text or MISSING
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "n/a"} else MISSING


def _status(value):
    if value is True:
        return "Aprovado"
    if value is False:
        return "Reprovado"
    if value is None:
        return "Inconclusivo"
    return {
        "conforming": "Aprovado",
        "approved": "Aprovado",
        "nonconforming": "Reprovado",
        "failed": "Reprovado",
        "not_evaluable": "Inconclusivo",
        "insufficient_data": "Inconclusivo",
        "incomplete": "Incompleto",
        "warning": "Atenção",
    }.get(value, _value(value))


def _selected_pairs(pairs):
    return [deepcopy(pair) for pair in (pairs or []) if isinstance(pair, dict) and pair.get("selected") is True]


def _component(pair, component):
    record = pair.get(component)
    return record if isinstance(record, dict) else {}


def _component_label(pair, component):
    record = _component(pair, component)
    if record:
        return format_run_option_label(record).replace("dt=", "dt = ")
    run = pair.get(f"{component}_run")
    delta_t = _number(pair.get(f"{component}_delta_t_s"))
    if run in (None, ""):
        return MISSING
    return f"Run {run}" + (f" | dt = {delta_t:.3f} s" if delta_t is not None else "")


def _ambient_values(pair, key, fallback_keys=()):
    values = []
    for ambient in (pair.get("ambient_by_component") or {}).values():
        if isinstance(ambient, dict):
            number = _number(ambient.get(key))
            if number is not None:
                values.append(number)
    for fallback in fallback_keys:
        number = _number(pair.get(fallback))
        if number is not None:
            values.append(number)
    return values


def _weather_for_pair(pair):
    temperatures = _ambient_values(pair, "temperature_c", ("temp_plus_used", "temp_minus_used", "temp_c"))
    pressures = _ambient_values(pair, "pressure_kpa", ("press_plus_used", "press_minus_used", "baro_kpa"))
    winds = _ambient_values(pair, "wind_speed_ms", ("wind_plus_ms", "wind_minus_ms", "wind_ms"))
    temperature = max(temperatures) if temperatures else None
    pressure = sum(pressures) / len(pressures) if pressures else None
    wind = max(winds) if winds else None
    alerts = []
    if wind is not None and wind > 3.0:
        alerts.append("Vento acima de 3 m/s")
    if temperature is not None and temperature > 35.0:
        alerts.append("Temperatura acima de 35 °C")
    return temperature, pressure, wind, alerts


def _append_table(ws, start_row, title, headers, rows):
    ws.cell(start_row, 1, title).font = Font(bold=True, size=12)
    ws.cell(start_row, 1).fill = TITLE_FILL
    header_row = start_row + 1
    for column, header in enumerate(headers, 1):
        cell = ws.cell(header_row, column, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER
    for row_index, row in enumerate(rows, header_row + 1):
        for column, item in enumerate(row, 1):
            cell = ws.cell(row_index, column, _value(item))
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    return header_row + len(rows) + 2


def _finish_sheet(ws):
    ws.freeze_panes = "A3"
    for column in range(1, ws.max_column + 1):
        width = max(len(str(ws.cell(row, column).value or "")) for row in range(1, ws.max_row + 1)) + 2
        ws.column_dimensions[get_column_letter(column)].width = min(max(width, 12), 42)
    ws.auto_filter.ref = ws.dimensions


def _write_summary(wb, final_results, warnings, generated_at):
    ws = wb.active
    ws.title = "Resumo Final"
    rows = [
        ("Data de geração", generated_at.strftime("%d/%m/%Y %H:%M:%S")),
        ("Método", "Split"),
        ("Quantidade de pares selecionados", final_results.get("num_pairs")),
        ("F0 final (N)", final_results.get("mean_f0")),
        ("F2 final (N/(km/h)²)", final_results.get("mean_f2")),
        ("CV F0 (%)", final_results.get("cv_f0")),
        ("CV F2 (%)", final_results.get("cv_f2")),
        ("Energia média (MJ/km)", final_results.get("mean_energy")),
        ("Status final", _status(final_results.get("conformity_status"))),
        ("Warnings principais", warnings),
    ]
    _append_table(ws, 1, "RESULTADOS FINAIS — MÉTODO SPLIT", ("Campo", "Valor"), rows)
    for row in range(4, ws.max_row + 1):
        label = ws.cell(row, 1).value
        if label == "F0 final (N)": ws.cell(row, 2).number_format = "0.0000"
        elif label == "F2 final (N/(km/h)²)": ws.cell(row, 2).number_format = "0.000000"
        elif label in ("CV F0 (%)", "CV F2 (%)"): ws.cell(row, 2).number_format = '0.00"%"'
        elif label == "Energia média (MJ/km)": ws.cell(row, 2).number_format = "0.0000"
    _finish_sheet(ws)


def _write_vehicle(wb, vehicle_data):
    ws = wb.create_sheet("Dados do Veículo")
    rows = []
    source = deepcopy(vehicle_data or {})
    nested = source.pop("vehicle_info", None)
    if isinstance(nested, dict):
        source = {**nested, **source}
    for key, value in source.items():
        rows.append((key.replace("_", " ").title(), value))
    _append_table(ws, 1, "DADOS DO VEÍCULO", ("Campo", "Valor"), rows or [(MISSING, MISSING)])
    _finish_sheet(ws)


def _write_pairs(wb, pairs):
    ws = wb.create_sheet("Pares Selecionados")
    headers = ("Par", "Origem", "High [+]", "Low [+]", "High [-]", "Low [-]", "DeltaT high+", "DeltaT low+", "DeltaT high-", "DeltaT low-", "F0", "F2", "CV F0", "CV F2", "Energia", "Temperatura", "Pressão", "Vento", "Alertas meteorológicos")
    rows = []
    for pair in pairs:
        temperature, pressure, wind, alerts = _weather_for_pair(pair)
        rows.append((format_split_pair_label(pair), pair.get("selection_source"), *(_component_label(pair, component) for component in COMPONENTS), *(pair.get(f"{component}_delta_t_s") if pair.get(f"{component}_delta_t_s") is not None else _component(pair, component).get("delta_t_s") for component in COMPONENTS), pair.get("F0_mean", pair.get("F0")), pair.get("F2_mean", pair.get("F2")), pair.get("cv_F0_percent"), pair.get("cv_F2_percent"), pair.get("energy"), temperature, pressure, wind, alerts))
    _append_table(ws, 1, "PARES USADOS NO RESULTADO FINAL", headers, rows)
    for row in range(3, ws.max_row + 1):
        for column, number_format in ((11, "0.0000"), (12, "0.000000"), (13, '0.00"%"'), (14, '0.00"%"'), (15, "0.0000")):
            ws.cell(row, column).number_format = number_format
    _finish_sheet(ws)


def _write_deviations(wb, analysis):
    ws = wb.create_sheet("Análise de Desvios")
    coefficients = analysis.get("coefficient_summary") or {}
    row = _append_table(ws, 1, "RESUMO CV F0/F2", ("Coeficiente", "Média", "Desvio padrão", "CV (%)", "Limite (%)", "Status"), [
        ("F0", coefficients.get("mean_f0"), coefficients.get("stdev_f0"), coefficients.get("cv_f0_pct"), coefficients.get("limit_pct"), _status(coefficients.get("status"))),
        ("F2", coefficients.get("mean_f2"), coefficients.get("stdev_f2"), coefficients.get("cv_f2_pct"), coefficients.get("limit_pct"), _status(coefficients.get("status"))),
    ])
    deviations = analysis.get("pair_deviations") or []
    row = _append_table(ws, row, "DESVIOS POR PAR", ("Par", "F0", "Desvio F0 (%)", "F2", "Desvio F2 (%)", "Energia", "Alertas"), [(item.get("pair"), item.get("f0"), item.get("f0_deviation_pct"), item.get("f2"), item.get("f2_deviation_pct"), item.get("energy"), item.get("alerts")) for item in deviations])
    loo = analysis.get("leave_one_out") or []
    _append_table(ws, row, "LEAVE-ONE-OUT", ("Par removido", "CV F0 atual", "Novo CV F0", "Variação F0", "CV F2 atual", "Novo CV F2", "Variação F2"), [(item.get("pair"), item.get("current_cv_f0_pct"), item.get("new_cv_f0_pct"), item.get("cv_f0_change_pct_points"), item.get("current_cv_f2_pct"), item.get("new_cv_f2_pct"), item.get("cv_f2_change_pct_points")) for item in loo])
    _finish_sheet(ws)


def _write_times(wb, analysis):
    ws = wb.create_sheet("Tempos deltaT")
    times = analysis.get("time_summary") or {}
    groups = times.get("groups") or {}
    row = _append_table(ws, 1, "CV DOS TEMPOS", ("Grupo", "n", "Média deltaT", "Desvio padrão", "CV deltaT (%)", "Limite (%)", "Status"), [(COMPONENT_LABELS.get(key, key), value.get("count"), value.get("mean"), value.get("stdev"), value.get("cv_pct"), times.get("cv_limit_pct"), _status(value.get("passed"))) for key, value in groups.items()])
    opposite = times.get("opposite_direction") or {}
    _append_table(ws, row, "DIFERENÇA IDA/VOLTA", ("Velocidade", "Média [+]", "Média [-]", "Diferença (%)", "Limite (%)", "Status"), [(key.title(), value.get("mean_plus"), value.get("mean_minus"), value.get("diff_pct"), times.get("opposite_mean_limit_pct"), _status(value.get("passed"))) for key, value in opposite.items()])
    _finish_sheet(ws)


def _write_weather(wb, pairs):
    ws = wb.create_sheet("Meteorologia")
    rows = []
    for pair in pairs:
        temperature, pressure, wind, alerts = _weather_for_pair(pair)
        rows.append((format_split_pair_label(pair), temperature, pressure, wind, alerts))
    _append_table(ws, 1, "METEOROLOGIA POR PAR", ("Par", "Temperatura (°C)", "Pressão (kPa)", "Vento (m/s)", "Alertas"), rows)
    for row in range(3, ws.max_row + 1):
        if (_number(ws.cell(row, 2).value) or -math.inf) > 35 or (_number(ws.cell(row, 4).value) or -math.inf) > 3:
            for column in range(1, 6): ws.cell(row, column).fill = WARNING_FILL
    _finish_sheet(ws)


def _write_traceability(wb, pairs):
    ws = wb.create_sheet("Rastreabilidade")
    rows = []
    for pair in pairs:
        for component in COMPONENTS:
            record = _component(pair, component)
            ambient = (pair.get("ambient_by_component") or {}).get(component) or {}
            rows.append((pair.get("id"), format_split_pair_label(pair), COMPONENT_LABELS[component], record.get("filename", pair.get(f"{component}_file")), record.get("source_role"), record.get("content_sha256") or record.get("source_sha256") or record.get("input_hash"), ambient.get("source") or pair.get("ambient_source"), ambient.get("sync_method") or ambient.get("method"), list(dict.fromkeys([*(pair.get("warnings") or []), *(ambient.get("warnings") or [])]))))
    _append_table(ws, 1, "RASTREABILIDADE DOS PARES", ("pair_id técnico", "Label público", "Componente", "Arquivo", "Papel da fonte", "Hash de entrada", "Fonte meteo", "Método sync meteo", "Warnings"), rows)
    _finish_sheet(ws)


def export_split_final_results_to_excel(*, final_results: dict | None, selected_pairs: list[dict], vehicle_data: dict, deviation_analysis: dict | None = None, generated_at: datetime | None = None) -> bytes:
    """Return an .xlsx report built only from explicitly selected Split pairs."""
    pairs = _selected_pairs(selected_pairs)
    consolidated = consolidate_split_final_results(pairs)
    if final_results:
        # The core consolidation remains authoritative; retain extra warnings only.
        consolidated["warnings"] = list(dict.fromkeys([*(consolidated.get("warnings") or []), *((final_results or {}).get("warnings") or [])]))
    analysis = deepcopy(deviation_analysis) if deviation_analysis is not None else analyze_split_selected_deviations(pairs)
    wb = Workbook()
    _write_summary(wb, consolidated, consolidated.get("warnings") or analysis.get("warnings") or [], generated_at or datetime.now())
    _write_vehicle(wb, vehicle_data)
    _write_pairs(wb, pairs)
    _write_deviations(wb, analysis)
    _write_times(wb, analysis)
    _write_weather(wb, pairs)
    _write_traceability(wb, pairs)
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

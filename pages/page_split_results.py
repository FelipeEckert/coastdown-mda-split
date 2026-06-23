# coding: utf-8
"""Read-only final report for pairs selected in Split Final Comparison."""

from datetime import datetime
import math

import pandas as pd
import streamlit as st

from core.split_deviation_analysis import get_cached_split_deviation_analysis
from core.split_display import (
    format_run_option_label,
    format_split_pair_label,
    format_split_time_group_label,
    get_split_reference_speeds,
)
from core.split_results import consolidate_split_final_results
from core.split_weather_context import split_environmental_values
from core.split_vehicle_mass import normalize_split_vehicle_mass_data
from data.split_exporters import (
    build_split_export_signature,
    export_split_final_results_to_excel,
    get_cached_split_export,
)


COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _display(value, precision=2, suffix=""):
    number = _number(value)
    if number is not None:
        return f"{number:.{precision}f}{suffix}"
    text = str(value).strip() if value is not None else ""
    return text if text and text.lower() not in {"nan", "none", "n/a"} else "-"


def _cv_status(value, t):
    number = _number(value)
    if number is None:
        return t("split_results_status_not_evaluable")
    return t("split_results_status_conforming" if number <= 10.0 else "split_results_status_nonconforming")


def _status_label(status, t):
    return t(f"split_results_status_{status}")


def _check_status_label(passed, t):
    if passed is True:
        return t("split_results_status_conforming")
    if passed is False:
        return t("split_results_status_nonconforming")
    return t("split_results_status_not_evaluable")


def _source_label(source, t):
    return t(f"split_selection_source_{source}") if source in ("manual", "algorithm") else t("split_selection_source_unknown")


def _component_label(pair, component):
    record = pair.get(component)
    if isinstance(record, dict) and record:
        return format_run_option_label(record).replace("dt=", "dt = ")
    run = pair.get(f"{component}_run")
    delta_t = _number(pair.get(f"{component}_delta_t_s"))
    if run in (None, ""):
        return "-"
    return f"Run {run}" + (f" | dt = {delta_t:.3f} s" if delta_t is not None else "")


def _weather_row(pair):
    environmental = split_environmental_values(pair)
    temperature = environmental["temperature_c"]
    pressure = environmental["pressure_kpa"]
    wind = environmental["wind_speed_mps"]
    alerts = []
    if wind is not None and wind > 3.0:
        alerts.append("vento > 3 m/s")
    if temperature is not None and temperature > 35.0:
        alerts.append("temperatura > 35 °C")
    return temperature, pressure, wind, alerts


def _pair_rows(pairs, t):
    rows = []
    for pair in pairs:
        temperature, pressure, wind, alerts = _weather_row(pair)
        rows.append({
            t("split_pair"): format_split_pair_label(pair),
            t("split_selection_source"): _source_label(pair.get("selection_source"), t),
            "High [+]": _component_label(pair, "high_plus"),
            "Low [+]": _component_label(pair, "low_plus"),
            "High [-]": _component_label(pair, "high_minus"),
            "Low [-]": _component_label(pair, "low_minus"),
            "F0 (N)": _display(pair.get("F0_mean"), 4),
            "F2 (N/(km/h)²)": _display(pair.get("F2_mean"), 6),
            "CV F0 [%]": _display(pair.get("cv_F0_percent"), 2),
            "CV F2 [%]": _display(pair.get("cv_F2_percent"), 2),
            "Energia (MJ/km)": _display(pair.get("energy"), 4),
            "Temperatura (°C)": _display(temperature, 1),
            "Pressão (kPa)": _display(pressure, 2),
            "Vento (m/s)": _display(wind, 1),
            "Alertas": "; ".join(alerts) or "-",
        })
    return rows


def _result_rows(results, t=None):
    """Compatibility projection retained for pure callers and older tests."""
    if t is not None:
        return _pair_rows(results, t)
    return [
        {
            "Index": index,
            "Pair": format_split_pair_label(result),
            "Selection source": result.get("selection_source"),
            "F0 (N)": result.get("F0_mean"),
            "F2 (N/(km/h)^2)": result.get("F2_mean"),
            "Energy (MJ/km)": result.get("energy"),
            "f'0 (N)": result.get("f0_prime_mean"),
            "f'2 (N/(m/s)^2)": result.get("f2_prime_mean"),
            "Warnings": "; ".join(result.get("warnings") or []),
        }
        for index, result in enumerate(results, 1)
    ]


def _render_summary(summary, t):
    st.subheader(t("split_results_consolidated"))
    first = st.columns(4)
    first[0].metric(t("split_selected_pairs"), summary["num_pairs"])
    first[1].metric(t("split_results_final_f0"), _display(summary.get("mean_f0"), 4))
    first[2].metric(t("split_results_final_f2"), _display(summary.get("mean_f2"), 6))
    first[3].metric(t("split_results_mean_energy"), _display(summary.get("mean_energy"), 4))
    second = st.columns(3)
    second[0].metric(t("split_results_cv_f0"), _display(summary.get("cv_f0"), 2))
    second[1].metric(t("split_results_cv_f2"), _display(summary.get("cv_f2"), 2))
    second[2].metric(t("split_results_conformity"), _status_label(summary["conformity_status"], t))


def _render_vehicle(summary, t):
    st.markdown("---")
    st.subheader(f"🚗 {t('vehicle_information')}")
    vehicle = dict(st.session_state.get("vehicle_info") or {})
    mass_data = normalize_split_vehicle_mass_data({
        "vehicle_info": vehicle,
        "total_mass": st.session_state.get("total_mass"),
    })
    references = summary["selected_pairs"][0] if summary["selected_pairs"] else {}
    rows = [
        (t("vehicle_model"), vehicle.get("model")),
        (t("test_date"), vehicle.get("test_date")),
        (t("split_running_order_mass"), _display(mass_data.get("running_order_mass_kg"), 2, " kg")),
        (t("split_test_mass"), _display(mass_data.get("test_mass_kg"), 2, " kg")),
        (t("split_rotational_equivalent_mass"), _display(mass_data.get("rotational_equivalent_mass_kg"), 2, " kg")),
        (t("split_effective_mass"), _display(mass_data.get("effective_mass_kg"), 2, " kg")),
        ("Velocidade alta de referência", _display(references.get("v2_reference_kmh"), 1, " km/h")),
        ("Velocidade baixa de referência", _display(references.get("v1_reference_kmh"), 1, " km/h")),
    ]
    st.dataframe(pd.DataFrame(rows, columns=("Campo", "Valor")), use_container_width=True, hide_index=True)


def _render_coefficients(summary, t):
    st.markdown("---")
    st.subheader(t("split_results_validation"))
    rows = [
        ("F0 [N]", _display(summary.get("mean_f0"), 4), _display(summary.get("cv_f0"), 2), _cv_status(summary.get("cv_f0"), t)),
        ("F2 [N/(km/h)²]", _display(summary.get("mean_f2"), 6), _display(summary.get("cv_f2"), 2), _cv_status(summary.get("cv_f2"), t)),
        ("Energia [MJ/km]", _display(summary.get("mean_energy"), 4), _display(summary.get("cv_energy"), 2), t("split_results_status_not_evaluable")),
    ]
    st.dataframe(pd.DataFrame(rows, columns=("Coeficiente", "Valor médio", "CV [%]", "Status")), use_container_width=True, hide_index=True)
    status = summary["conformity_status"]
    message = _status_label(status, t)
    if status == "conforming": st.success(message)
    elif status in ("nonconforming", "incomplete"): st.error(message)
    else: st.warning(message) if status == "warning" else st.info(message)
    for warning in summary.get("warnings") or []:
        st.warning(str(warning))


def _render_deviation_summary(analysis, selected_pairs, t):
    st.markdown("---")
    st.subheader("Análise de desvios")
    coefficients = analysis["coefficient_summary"]
    times = analysis["time_summary"]
    weather = analysis["weather_summary"]
    cards = st.columns(3)
    cards[0].metric("Coeficientes", _status_label({"approved": "conforming", "failed": "nonconforming", "insufficient_data": "not_evaluable", "warning": "warning"}.get(coefficients["status"], "warning"), t))
    cards[1].metric("Tempos deltaT", _status_label({"approved": "conforming", "failed": "nonconforming", "insufficient_data": "not_evaluable"}.get(times["status"], "warning"), t))
    cards[2].metric("Meteorologia", _status_label({"approved": "conforming", "failed": "nonconforming", "insufficient_data": "not_evaluable"}.get(weather["status"], "warning"), t))
    high_reference, low_reference = get_split_reference_speeds(selected_pairs)
    time_rows = []
    for component, group in times.get("groups", {}).items():
        time_rows.append((format_split_time_group_label(
            component,
            high_reference_speed_kmh=high_reference,
            low_reference_speed_kmh=low_reference,
        ), _display(group.get("cv_pct"), 2), _display(group.get("mean"), 3), _check_status_label(group.get("passed"), t)))
    if time_rows:
        st.dataframe(pd.DataFrame(time_rows, columns=("Grupo", "C.V. Δt [%]", "Média Δt [s]", "Status")), use_container_width=True, hide_index=True)
    st.caption("Detalhes completos permanecem em Comparativo Final > Análise de desvios.")


def _render_traceability(pairs, t):
    with st.expander("🔎 Rastreabilidade", expanded=False):
        rows = []
        for pair in pairs:
            for component in COMPONENTS:
                record = pair.get(component) if isinstance(pair.get(component), dict) else {}
                ambient = (pair.get("ambient_by_component") or {}).get(component) or {}
                rows.append({
                    "Par": format_split_pair_label(pair), "pair_id": pair.get("id"), "Componente": component,
                    t("split_file"): _display(record.get("filename", pair.get(f"{component}_file"))),
                    t("split_run"): _display(record.get("run_id", pair.get(f"{component}_run"))),
                    "Papel da fonte": _display(record.get("source_role")),
                    "Hash": _display(record.get("content_sha256") or record.get("source_sha256")),
                    "Fonte meteo": _display(ambient.get("source") or pair.get("ambient_source")),
                    "Sync meteo": _display(ambient.get("sync_method") or ambient.get("method")),
                    "Warnings": "; ".join([*(pair.get("warnings") or []), *(ambient.get("warnings") or [])]) or "-",
                })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render(t):
    """Render a read-only projection of explicitly selected Split pairs."""
    st.header("📊 " + t("page_split_results"))
    st.caption("Resumo final calculado a partir dos pares selecionados no Comparativo Final.")
    comparison_pairs = st.session_state.get("split_comparison_pairs") or []
    summary = consolidate_split_final_results(comparison_pairs)
    selected_pairs = summary["selected_pairs"]
    if not selected_pairs:
        st.warning(t("split_results_no_pairs_selected"))
        st.info("Volte ao Comparativo Final e selecione os pares desejados.")
        return

    analysis, analysis_cache, _ = get_cached_split_deviation_analysis(
        selected_pairs,
        st.session_state.get("split_deviation_analysis_cache"),
    )
    st.session_state.split_deviation_analysis_cache = analysis_cache
    _render_summary(summary, t)
    _render_vehicle(summary, t)
    _render_coefficients(summary, t)

    st.markdown("---")
    st.subheader(f"📋 {t('split_selected_pairs')}")
    st.dataframe(pd.DataFrame(_pair_rows(selected_pairs, t)), use_container_width=True, hide_index=True)
    _render_deviation_summary(analysis, selected_pairs, t)
    _render_traceability(selected_pairs, t)

    st.markdown("---")
    st.subheader(f"📥 {t('split_results_export')}")
    vehicle_info = dict(st.session_state.get("vehicle_info") or {})
    vehicle_data = {
        **normalize_split_vehicle_mass_data({
            "vehicle_info": vehicle_info,
            "total_mass": st.session_state.get("total_mass"),
        }),
        "model": vehicle_info.get("model"),
        "test_date": vehicle_info.get("test_date"),
    }
    export_signature = build_split_export_signature(
        final_results=summary,
        selected_pairs=selected_pairs,
        vehicle_data=vehicle_data,
        deviation_analysis=analysis,
    )
    export_cache = st.session_state.get("split_results_excel_cache")
    if st.button(
        t("split_results_generate_excel"),
        type="primary",
        use_container_width=True,
    ):
        excel_bytes, export_cache, _ = get_cached_split_export(
            export_signature,
            export_cache,
            builder=lambda: export_split_final_results_to_excel(
                final_results=summary,
                selected_pairs=selected_pairs,
                vehicle_data=vehicle_data,
                deviation_analysis=analysis,
            ),
        )
        st.session_state.split_results_excel_cache = export_cache
    else:
        excel_bytes = (
            export_cache.get("payload")
            if isinstance(export_cache, dict)
            and export_cache.get("signature") == export_signature
            else None
        )
    if excel_bytes is not None:
        st.download_button(
            label="📥 " + t("split_results_export_button"), data=excel_bytes,
            file_name=f"relatorio_resultados_split_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
        )

# coding: utf-8
"""Read-only final report for pairs selected in Split Final Comparison."""

from datetime import datetime
import html
import math

import pandas as pd
import streamlit as st

from core.split_deviation_analysis import get_cached_split_deviation_analysis
from core.split_display import (
    format_run_option_label,
    format_split_opposite_time_label,
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
TIME_GROUP_COMPONENTS = ("high_plus", "high_minus", "low_plus", "low_minus")
OPPOSITE_SPEED_GROUPS = ("high", "low")

CONFORMITY_ICONS = {
    "conforming": "✅",
    "nonconforming": "❌",
    "inconclusive": "⚠️",
}
CONFORMITY_COLORS = {
    "conforming": "#4caf50",
    "nonconforming": "#f44336",
    "inconclusive": "#ff9800",
}
CONFORMITY_LABEL_KEYS = {
    "conforming": "split_results_status_conforming",
    "nonconforming": "split_results_status_nonconforming",
    "inconclusive": "split_results_status_inconclusive",
}

METEO_SYNC_WARNING_PATTERNS = (
    "weather date differs",
    "synchronization used time of day",
    "multiple weather records were equally close",
    "weather record",
    "sync",
)


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


def is_meteo_sync_warning(warning) -> bool:
    """Return True for technical weather-synchronization warnings."""
    text = str(warning or "").lower()
    return any(pattern in text for pattern in METEO_SYNC_WARNING_PATTERNS)


def _split_warnings_by_audience(warnings) -> tuple[list[str], list[str]]:
    """Split warnings into (critical, meteo_sync) for end-user display.

    Meteo-sync warnings stay useful for traceability/Excel but should not
    pollute the results page; they are grouped into a collapsed expander
    instead of one st.warning per item.
    """
    critical = []
    meteo_sync = []
    for warning in warnings or []:
        if warning is None:
            continue
        text = str(warning).strip()
        if not text:
            continue
        (meteo_sync if is_meteo_sync_warning(text) else critical).append(text)
    return critical, meteo_sync


def _conformity_status_from_time_validation(time_validation) -> str:
    """Map a normative time-validation `passed` value to a card status key."""
    passed = time_validation.get("passed") if isinstance(time_validation, dict) else None
    if passed is True:
        return "conforming"
    if passed is False:
        return "nonconforming"
    return "inconclusive"


def _split_summary_card_css() -> str:
    return """
    <style>
        .split-summary-card {
            background-color: #1e1e1e;
            border: 1px solid #3d3d3d;
            border-radius: 8px;
            padding: 20px;
        }
        .split-summary-card .split-summary-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .split-summary-card .split-summary-row + .split-summary-row {
            border-top: 1px solid #3d3d3d;
            margin-top: 14px;
            padding-top: 14px;
        }
        .split-summary-card .split-summary-label {
            color: #a0a0a0;
            font-size: 0.85rem;
        }
        .split-summary-card .split-summary-value {
            color: #ffffff;
            font-size: 1.6rem;
            font-weight: 700;
        }
        .split-summary-card .split-summary-conformity {
            text-align: right;
        }
        .split-summary-card .split-summary-conformity-value {
            font-size: 1.2rem;
            font-weight: 700;
        }
        .split-summary-card .split-summary-conformity-criteria {
            color: #a0a0a0;
            font-size: 0.78rem;
        }
        .split-summary-card .split-summary-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            text-align: center;
            gap: 8px;
            width: 100%;
        }
        .split-summary-card .split-summary-diagnostic-row {
            display: flex;
            justify-content: space-around;
            text-align: center;
            width: 100%;
        }
        .split-summary-card .split-summary-diagnostic-value {
            color: #a0a0a0;
            font-size: 1.2rem;
            font-weight: 700;
        }
    </style>
    """


def _build_consolidated_results_card_html(summary: dict, time_validation, t) -> str:
    """Build the consolidated results card as a single HTML block."""
    status = _conformity_status_from_time_validation(time_validation)
    icon = CONFORMITY_ICONS[status]
    color = CONFORMITY_COLORS[status]
    status_label = html.escape(t(CONFORMITY_LABEL_KEYS[status]))
    criteria_label = html.escape(t("split_results_card_conformity_criteria"))
    pairs_label = html.escape(t("split_selected_pairs"))
    conformity_label = html.escape(t("split_results_card_conformity"))
    diagnostic_label = html.escape(t("split_results_diagnostic_label"))
    pairs_value = html.escape(str(summary.get("num_pairs", 0)))

    return f"""
    {_split_summary_card_css()}
    <div class="split-summary-card">
        <div class="split-summary-row">
            <div>
                <div class="split-summary-label">{pairs_label}</div>
                <div class="split-summary-value">{pairs_value}</div>
            </div>
            <div class="split-summary-conformity">
                <div class="split-summary-label">{conformity_label}</div>
                <div class="split-summary-conformity-value" style="color:{color};">{icon} {status_label}</div>
                <div class="split-summary-conformity-criteria">{criteria_label}</div>
            </div>
        </div>
        <div class="split-summary-row">
            <div class="split-summary-grid">
                <div>
                    <div class="split-summary-label">{html.escape(t("split_results_final_f0"))}</div>
                    <div class="split-summary-value">{html.escape(_display(summary.get("mean_f0"), 4))}</div>
                </div>
                <div>
                    <div class="split-summary-label">{html.escape(t("split_results_final_f2"))}</div>
                    <div class="split-summary-value">{html.escape(_display(summary.get("mean_f2"), 6))}</div>
                </div>
                <div>
                    <div class="split-summary-label">{html.escape(t("split_results_mean_energy"))}</div>
                    <div class="split-summary-value">{html.escape(_display(summary.get("mean_energy"), 4))}</div>
                </div>
            </div>
        </div>
        <div class="split-summary-row split-summary-diagnostic-row">
            <div>
                <div class="split-summary-label">{html.escape(t("split_results_cv_f0"))} {diagnostic_label}</div>
                <div class="split-summary-diagnostic-value">{html.escape(_display(summary.get("cv_f0"), 2))}</div>
            </div>
            <div>
                <div class="split-summary-label">{html.escape(t("split_results_cv_f2"))} {diagnostic_label}</div>
                <div class="split-summary-diagnostic-value">{html.escape(_display(summary.get("cv_f2"), 2))}</div>
            </div>
        </div>
    </div>
    """


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


def _render_summary(summary, time_validation, t):
    st.subheader(t("split_results_consolidated"))
    st.markdown(
        _build_consolidated_results_card_html(summary, time_validation, t),
        unsafe_allow_html=True,
    )


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
    critical_warnings, meteo_sync_warnings = _split_warnings_by_audience(
        summary.get("warnings")
    )
    for warning in critical_warnings:
        st.warning(warning)
    if meteo_sync_warnings:
        with st.expander(
            t("split_results_meteo_sync_expander", count=len(meteo_sync_warnings)),
            expanded=False,
        ):
            for warning in meteo_sync_warnings:
                st.caption(warning)


def _time_normative_metric_rows(times: dict, selected_pairs, t) -> list[dict]:
    """Build the six Split normative Delta-t metric rows (groups + opposite)."""
    high_reference, low_reference = get_split_reference_speeds(selected_pairs)
    cv_limit = times.get("cv_limit_pct", 2.5)
    opposite_limit = times.get("opposite_mean_limit_pct", 10.0)
    groups = times.get("groups") or {}
    opposite_direction = times.get("opposite_direction") or {}

    metric_key = t("split_results_deviation_metric")
    value_key = t("split_results_deviation_value")
    limit_key = t("split_results_deviation_limit")
    status_key = t("split_results_deviation_status")

    rows = []
    for component in TIME_GROUP_COMPONENTS:
        group = groups.get(component) or {}
        rows.append({
            metric_key: format_split_time_group_label(
                component,
                high_reference_speed_kmh=high_reference,
                low_reference_speed_kmh=low_reference,
            ),
            value_key: _display(group.get("cv_pct"), 2, " %"),
            limit_key: _display(cv_limit, 1, " %"),
            status_key: _check_status_label(group.get("passed"), t),
        })
    for speed_group in OPPOSITE_SPEED_GROUPS:
        result = opposite_direction.get(speed_group) or {}
        rows.append({
            metric_key: format_split_opposite_time_label(
                speed_group,
                high_reference_speed_kmh=high_reference,
                low_reference_speed_kmh=low_reference,
            ),
            value_key: _display(result.get("diff_pct"), 2, " %"),
            limit_key: _display(opposite_limit, 1, " %"),
            status_key: _check_status_label(result.get("passed"), t),
        })
    return rows


def _render_deviation_summary(analysis, selected_pairs, t):
    st.markdown("---")
    st.subheader(t("split_results_deviation_title"))
    coefficients = analysis["coefficient_summary"]
    times = analysis["time_summary"]
    weather = analysis["weather_summary"]
    status_map = {
        "approved": "conforming",
        "failed": "nonconforming",
        "insufficient_data": "not_evaluable",
    }
    cards = st.columns(2)
    cards[0].metric(
        t("split_results_deviation_time_overall"),
        _status_label(status_map.get(times["status"], "warning"), t),
    )
    cards[1].metric(
        t("split_results_deviation_weather"),
        _status_label(status_map.get(weather["status"], "warning"), t),
    )

    st.markdown(f"**{t('split_results_deviation_time_criteria_title')}**")
    time_rows = _time_normative_metric_rows(times, selected_pairs, t)
    if time_rows:
        st.dataframe(pd.DataFrame(time_rows), use_container_width=True, hide_index=True)

    st.markdown(f"**{t('split_results_deviation_coefficients_title')}**")
    diagnostic_label = t("split_results_diagnostic_label")
    diagnostic_columns = st.columns(2)
    diagnostic_columns[0].metric(
        f"{t('split_results_cv_f0')} {diagnostic_label}",
        _display(coefficients.get("cv_f0_pct"), 2, " %"),
    )
    diagnostic_columns[1].metric(
        f"{t('split_results_cv_f2')} {diagnostic_label}",
        _display(coefficients.get("cv_f2_pct"), 2, " %"),
    )
    st.caption(t("split_results_deviation_details_note"))


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
    _render_summary(summary, analysis.get("time_summary"), t)
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

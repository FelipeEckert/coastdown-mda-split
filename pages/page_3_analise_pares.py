# coding: utf-8
"""
Página 3: Análise de Pares

Permite ao usuário selecionar pares de runs (ida/volta), aplicar correções
climáticas e calcular coeficientes F0/F2.
"""

import streamlit as st
import pandas as pd
import numpy as np
from statistics import mean, stdev
from datetime import datetime
from html import escape
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculations import (
    calcular_energia,
    calcular_f0_f2_split,
    calculate_single_pair_corrected_data,
    calculate_single_pair_corrected_data2
)
from core.corrections import apply_climate_correction
from data.loaders import find_closest_weather_record
from pages._legacy_method_state import legacy_uses_split_method


def _sync_mode_label(time_only, t):
    """Retorna o rotulo do modo de sincronizacao meteo."""
    return t("meteo_sync_mode_time_only") if time_only else t("meteo_sync_mode_full_datetime")


def _seconds_since_midnight(value):
    """Converte datetime ou texto HH:MM[:SS] em segundos desde meia-noite."""
    if value is None:
        return None

    if isinstance(value, datetime):
        time_obj = value.time()
    else:
        text = str(value).strip().replace(",", ".")
        if not text:
            return None

        time_obj = None
        for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
            try:
                time_obj = datetime.strptime(text, fmt).time()
                break
            except ValueError:
                continue
        if time_obj is None:
            return None

    return (
        time_obj.hour * 3600
        + time_obj.minute * 60
        + time_obj.second
        + time_obj.microsecond / 1_000_000
    )


def _format_sync_time(value):
    """Formata horario/timestamp para exibicao na auditoria."""
    if value is None:
        return "N/A"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M:%S")
    return str(value)


def _format_sync_number(value):
    """Formata numeros da auditoria meteo com uma casa decimal."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "N/A"


def _weather_sync_delta_seconds(run_data, weather_record, time_only):
    """Calcula a diferenca usada apenas para auditoria visual."""
    if not run_data or not weather_record:
        return None

    target_time = run_data.get("start_timestamp") or run_data.get("start_time_str")
    meteo_time = weather_record.get("timestamp")

    if time_only:
        target_seconds = _seconds_since_midnight(target_time)
        meteo_seconds = _seconds_since_midnight(meteo_time)
        if target_seconds is None or meteo_seconds is None:
            return None
        return abs(meteo_seconds - target_seconds)

    target_timestamp = run_data.get("start_timestamp")
    if not isinstance(target_timestamp, datetime) or not isinstance(meteo_time, datetime):
        return None
    return abs((meteo_time - target_timestamp).total_seconds())


def render_weather_sync_audit(run_items, weather_data, time_only, t):
    """Exibe auditoria da sincronizacao meteo sem alterar a escolha dos registros."""
    if not weather_data:
        return

    mode_label = _sync_mode_label(time_only, t)
    wind_col = t("meteo_sync_col_wind")
    high_wind_runs = []

    audit_rows = []
    for run_label, run_data in run_items:
        weather_record = find_closest_weather_record(
            run_data,
            weather_data,
            time_only=time_only
        )
        delta_seconds = _weather_sync_delta_seconds(run_data, weather_record, time_only)
        wind_ms = weather_record.get("wind_ms") if weather_record else None
        wind_display = _format_sync_number(wind_ms)
        if wind_ms is not None and float(wind_ms) > 3.0:
            high_wind_runs.append(f"{run_label}: {float(wind_ms):.2f} m/s")

        audit_rows.append({
            t("meteo_sync_col_run"): run_label,
            t("meteo_sync_col_csv_time"): _format_sync_time(
                run_data.get("start_timestamp") or run_data.get("start_time_str")
            ),
            t("meteo_sync_col_meteo_time"): _format_sync_time(
                weather_record.get("timestamp") if weather_record else None
            ),
            t("meteo_sync_col_delta_s"): (
                _format_sync_number(delta_seconds)
            ),
            t("meteo_sync_col_mode"): mode_label,
            t("meteo_sync_col_temp"): (
                _format_sync_number(weather_record.get("temp_c") if weather_record else None)
            ),
            t("meteo_sync_col_press"): (
                _format_sync_number(weather_record.get("baro_kpa") if weather_record else None)
            ),
            wind_col: wind_display,
        })

    with st.expander(t("meteo_sync_details_expander")):
        if high_wind_runs:
            st.warning(t("meteo_wind_above_limit_warning", runs=", ".join(high_wind_runs)))

        audit_df = pd.DataFrame(audit_rows)

        def highlight_high_wind(row):
            try:
                high_wind = float(row[wind_col]) > 3.0
            except (TypeError, ValueError):
                high_wind = False
            return [
                "background-color: #fff3cd; color: #000000" if high_wind and col == wind_col else ""
                for col in row.index
            ]

        st.dataframe(
            audit_df.style.apply(highlight_high_wind, axis=1),
            use_container_width=True,
            hide_index=True
        )


def _run_sort_key(run_id):
    """Retorna chave estável para ordenar IDs de runs."""
    try:
        return (0, int(run_id))
    except (TypeError, ValueError):
        return (1, str(run_id))


def _format_run_heading(heading, t):
    """Normaliza o heading para rótulo amigável."""
    heading_str = str(heading).strip()
    if heading_str in ["+", "N", "Norte", "North", "ida", "Ida", "IDA"]:
        return t("outbound")
    if heading_str in ["-", "S", "Sul", "South", "volta", "Volta", "VOLTA"]:
        return t("return")
    return heading_str or "N/A"


def _format_run_column_label(run_id, t):
    """Retorna rótulo amigável para coluna da matriz."""
    return t("time_conformity_run_label", run_id=run_id)


def _normalize_interval_times(run_data):
    """
    Normaliza os tempos de uma run para semântica por intervalo.

    Preferência:
    - lista já em formato de intervalo: len(times) == len(velocities) - 1
    - compatibilidade com schema legado acumulado: len(times) == len(velocities)
      e primeiro ponto em zero
    """
    velocities = run_data.get("velocities") or []
    times = run_data.get("times") or []

    if len(velocities) < 2 or not times:
        return [], []

    try:
        velocities = [float(v) for v in velocities]
        times = [float(v) for v in times]
    except (TypeError, ValueError):
        return [], []

    interval_times = []
    if len(times) == len(velocities) - 1:
        interval_times = times
    elif len(times) == len(velocities) and abs(times[0]) < 1e-9:
        interval_times = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    else:
        return [], []

    interval_rows = []
    for idx, interval_time in enumerate(interval_times):
        if idx + 1 >= len(velocities):
            break
        if not np.isfinite(interval_time) or interval_time <= 0:
            continue

        v_start = velocities[idx]
        v_end = velocities[idx + 1]
        if not np.isfinite(v_start) or not np.isfinite(v_end) or v_start <= v_end:
            continue

        start_label = int(round(v_start))
        end_label = int(round(v_end))
        interval_rows.append(
            {
                "interval_start": start_label,
                "interval_end": end_label,
                "interval_label": f"{start_label}-{end_label} km/h",
                "time_s": float(interval_time),
            }
        )

    return velocities, interval_rows


def _resolve_selected_run_id(raw_run_id, all_run_data):
    """Resolve um ID de run vindo do estado dos pares para uma chave existente."""
    if raw_run_id in all_run_data:
        return raw_run_id

    try:
        run_as_int = int(raw_run_id)
        if run_as_int in all_run_data:
            return run_as_int
    except (TypeError, ValueError):
        pass

    run_as_str = str(raw_run_id)
    if run_as_str in all_run_data:
        return run_as_str

    return None


def _get_selected_pair_run_ids():
    """Retorna runs deduplicadas a partir dos pares marcados no Comparativo Final."""
    all_run_data = st.session_state.get("all_run_data", {})
    selected_runs = set()

    for pair in st.session_state.get("calculated_pairs", {}).values():
        if not pair.get("selected", False):
            continue

        for key in ("run1", "run2", "run_ida", "run_volta"):
            resolved_run_id = _resolve_selected_run_id(pair.get(key), all_run_data)
            if resolved_run_id is not None:
                selected_runs.add(resolved_run_id)

    return sorted(selected_runs, key=_run_sort_key)


_TIME_CONFORMITY_LABEL_FALLBACKS = {
    "time_conformity_interval": {
        "pt": "Intervalo",
        "en": "Interval",
    },
    "time_conformity_measured_value": {
        "pt": "Valor medido",
        "en": "Measured value",
    },
    "time_conformity_mean_detail": {
        "pt": "Média do intervalo",
        "en": "Interval mean",
    },
    "time_conformity_std_time": {
        "pt": "Desvio padrão",
        "en": "Standard deviation",
    },
    "time_conformity_difference_s": {
        "pt": "Diferença",
        "en": "Difference",
    },
    "time_conformity_deviation_pct": {
        "pt": "Desvio (%)",
        "en": "Deviation (%)",
    },
    "time_conformity_status": {
        "pt": "Status",
        "en": "Status",
    },
    "time_conformity_status_conforming": {
        "pt": "Conforme",
        "en": "Conforming",
    },
    "time_conformity_status_non_conforming": {
        "pt": "Não conforme",
        "en": "Non-conforming",
    },
    "time_conformity_mean_time": {
        "pt": "Tempo Médio (s)",
        "en": "Mean Time (s)",
    },
    "time_conformity_min_time": {
        "pt": "Tempo Mínimo (s)",
        "en": "Min Time (s)",
    },
    "time_conformity_max_time": {
        "pt": "Tempo Máximo (s)",
        "en": "Max Time (s)",
    },
    "time_conformity_cv_pct": {
        "pt": "CV (%)",
        "en": "CV (%)",
    },
    "time_conformity_max_deviation_pct": {
        "pt": "Maior Desvio (%)",
        "en": "Max Deviation (%)",
    },
    "time_conformity_non_conforming_count": {
        "pt": "Não Conformes",
        "en": "Non-conforming",
    },
}


def _translator_language(t):
    """Infere o idioma capturado pelo tradutor para fallbacks locais."""
    for cell in getattr(t, "__closure__", None) or []:
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if value in ("pt", "en"):
            return value
    return "pt"


def _tc_text(t, key, **kwargs):
    """Traduz label da conformidade sem deixar key interna vazar na UI."""
    text = t(key, **kwargs)
    if text == key:
        language = _translator_language(t)
        fallback = _TIME_CONFORMITY_LABEL_FALLBACKS.get(key, {})
        text = fallback.get(language, fallback.get("pt", key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
    return text


def _format_detail_number(value, decimals=2, suffix=""):
    """Formata numero para detalhes da matriz de conformidade."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if not np.isfinite(number):
        return "N/A"
    return f"{number:.{decimals}f}{suffix}"


def _format_signed_detail_number(value, decimals=2, suffix=""):
    """Formata numero com sinal explicito para diferencas."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if not np.isfinite(number):
        return "N/A"
    return f"{number:+.{decimals}f}{suffix}"


def _build_time_conformity_tooltip_lookup(detailed_df, t):
    """Indexa detalhes por intervalo/run para a tabela HTML."""
    tooltip_lookup = {}
    interval_col = t("time_conformity_interval")
    for _, row in detailed_df.iterrows():
        is_non_conforming = bool(row["_is_non_conforming"])
        status_key = (
            "time_conformity_status_non_conforming"
            if is_non_conforming
            else "time_conformity_status_conforming"
        )
        details = [
            (
                _tc_text(t, "time_conformity_measured_value"),
                _format_detail_number(row["_time_s"], 2, " s"),
            ),
            (
                _tc_text(t, "time_conformity_mean_detail"),
                _format_detail_number(row["_mean_time_s"], 2, " s"),
            ),
            (
                _tc_text(t, "time_conformity_std_time"),
                _format_detail_number(row["_std_time_s"], 2, " s"),
            ),
            (
                _tc_text(t, "time_conformity_difference_s"),
                _format_signed_detail_number(row["_deviation_s"], 2, " s"),
            ),
            (
                _tc_text(t, "time_conformity_deviation_pct"),
                _format_signed_detail_number(row["_deviation_pct"], 1, "%"),
            ),
            (_tc_text(t, "time_conformity_status"), _tc_text(t, status_key)),
        ]
        tooltip_items = "".join(
            (
                '<li>'
                f'<span class="mda-time-conf-tooltip-label">{escape(label)}:</span> '
                f"{escape(value)}"
                "</li>"
            )
            for label, value in details
        )
        tooltip_lookup[
            (
                row[interval_col],
                row["_interval_start"],
                row["_interval_end"],
                row["_run_label"],
            )
        ] = f'<ul class="mda-time-conf-tooltip-list">{tooltip_items}</ul>'

    return tooltip_lookup


def render_time_conformity_html_table(
    matrix_df,
    matrix_status_display,
    ordered_run_columns,
    detailed_df,
    t,
):
    """Renderiza matriz HTML com tooltip CSS por celula."""
    interval_col = t("time_conformity_interval")
    tooltip_lookup = _build_time_conformity_tooltip_lookup(detailed_df, t)
    headers = [_tc_text(t, "time_conformity_interval")] + ordered_run_columns

    header_html = "".join(
        f"<th>{escape(str(column))}</th>" for column in headers
    )
    body_rows = []
    last_right_aligned_index = max(len(ordered_run_columns) - 2, 0)
    row_count = len(matrix_df)
    first_above_row = max(row_count // 2, 1)
    for row_position, (_, row) in enumerate(matrix_df.iterrows()):
        tooltip_direction_class = (
            "mda-time-conf-tooltip-above"
            if row_position >= first_above_row
            else "mda-time-conf-tooltip-below"
        )
        cells = [
            (
                '<td class="mda-time-conf-interval">'
                f"{escape(str(row[interval_col]))}"
                "</td>"
            )
        ]
        for column_index, column in enumerate(ordered_run_columns):
            raw_value = row.get(column)
            value_text = f"{raw_value:.2f} s" if pd.notna(raw_value) else ""
            tooltip_key = (
                row[interval_col],
                row["_interval_start"],
                row["_interval_end"],
                column,
            )
            tooltip_html = tooltip_lookup.get(tooltip_key, "")
            is_non_conforming = (
                bool(matrix_status_display.iloc[row_position][column])
                if column in matrix_status_display.columns
                else False
            )
            cell_classes = "mda-time-conf-cell"
            if is_non_conforming:
                cell_classes += " mda-time-conf-nonconforming"
            if column_index <= 1:
                cell_classes += " mda-time-conf-edge-left"
            elif column_index >= last_right_aligned_index:
                cell_classes += " mda-time-conf-edge-right"
            cell_classes += f" {tooltip_direction_class}"

            tooltip_span = (
                f'<span class="mda-time-conf-tooltip">{tooltip_html}</span>'
                if tooltip_html
                else ""
            )
            cells.append(
                f'<td class="{cell_classes}">'
                f'<span class="mda-time-conf-value">{escape(value_text)}</span>'
                f"{tooltip_span}"
                "</td>"
            )
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f"""
<style>
.mda-time-conf-scroll {{
    width: 100%;
    overflow-x: auto;
    overflow-y: visible;
    max-height: none;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
}}
.mda-time-conf-inner {{
    display: inline-block;
    min-width: 100%;
    overflow: visible;
}}
.mda-time-conf-table {{
    width: max-content;
    min-width: 100%;
    border-collapse: collapse;
    background: #1e1e1e;
    color: #ffffff;
    font-size: 0.9rem;
}}
.mda-time-conf-table th {{
    background: #111827;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    padding: 8px 10px;
    text-align: center;
    white-space: nowrap;
    font-weight: 600;
}}
.mda-time-conf-table td {{
    border: 1px solid #3d3d3d;
    padding: 7px 10px;
    text-align: center;
    white-space: nowrap;
}}
.mda-time-conf-table .mda-time-conf-interval {{
    position: sticky;
    left: 0;
    z-index: 1;
    min-width: 130px;
    background: #151922;
    text-align: left;
    font-weight: 600;
}}
.mda-time-conf-table th:first-child {{
    position: sticky;
    left: 0;
    z-index: 2;
}}
.mda-time-conf-cell {{
    position: relative;
    min-width: 86px;
    background: #1e1e1e;
}}
.mda-time-conf-cell:hover {{
    background: #263247;
}}
.mda-time-conf-nonconforming,
.mda-time-conf-nonconforming:hover {{
    background: #902626;
    color: #ffffff;
}}
.mda-time-conf-tooltip {{
    visibility: hidden;
    opacity: 0;
    position: absolute;
    z-index: 20;
    left: 50%;
    transform: translateX(-50%);
    width: max-content;
    max-width: min(320px, 70vw);
    padding: 10px 12px;
    border: 1px solid #4a9eff;
    border-radius: 6px;
    background: #0e1117;
    color: #ffffff;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    text-align: left;
    line-height: 1.45;
    pointer-events: none;
    white-space: normal;
}}
.mda-time-conf-tooltip-below .mda-time-conf-tooltip {{
    top: calc(100% + 8px);
}}
.mda-time-conf-tooltip-above .mda-time-conf-tooltip {{
    bottom: calc(100% + 8px);
}}
.mda-time-conf-edge-left .mda-time-conf-tooltip {{
    left: 0;
    transform: none;
}}
.mda-time-conf-edge-right .mda-time-conf-tooltip {{
    right: 0;
    left: auto;
    transform: none;
}}
.mda-time-conf-tooltip-list {{
    margin: 0;
    padding-left: 1.1rem;
}}
.mda-time-conf-tooltip-list li {{
    margin: 2px 0;
}}
.mda-time-conf-tooltip-label {{
    font-weight: 700;
    color: #ffffff;
}}
.mda-time-conf-cell:hover .mda-time-conf-tooltip {{
    visibility: visible;
    opacity: 1;
}}
</style>
<div class="mda-time-conf-scroll">
  <div class="mda-time-conf-inner">
    <table class="mda-time-conf-table">
      <thead><tr>{header_html}</tr></thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>
  </div>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)


def render_time_conformity_analysis(t):
    """Renderiza a análise de conformidade dos tempos por intervalo de velocidade."""
    if legacy_uses_split_method(st.session_state):
        st.info(t("time_conformity_split_not_supported"))
        return

    all_run_data = st.session_state.get("all_run_data", {})
    if not all_run_data:
        st.warning(t("error_no_file"))
        return

    st.markdown(f"### {t('time_conformity_title')}")
    st.caption(t("time_conformity_description"))

    control_col1, control_col2 = st.columns([2, 1])
    with control_col1:
        st.markdown(
            (
                "<div style='font-size:1.02rem; font-weight:600; "
                "margin-bottom:0.2rem;'>"
                f"{escape(t('time_conformity_source'))}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        source_mode = st.radio(
            t("time_conformity_source"),
            options=[
                t("time_conformity_all_runs"),
                t("time_conformity_selected_pair_runs"),
            ],
            horizontal=True,
            key="time_conformity_source_mode",
            label_visibility="collapsed",
        )
    with control_col2:
        tolerance_pct = st.number_input(
            t("time_conformity_tolerance_pct"),
            min_value=0.1,
            max_value=100.0,
            value=5.0,
            step=0.1,
            format="%.1f",
            key="time_conformity_tolerance_pct_value",
        )

    if source_mode == t("time_conformity_all_runs"):
        run_ids = sorted(all_run_data.keys(), key=_run_sort_key)
        st.caption(t("time_conformity_all_runs_hint", run_count=len(run_ids)))
    else:
        run_ids = _get_selected_pair_run_ids()
        selected_pair_count = sum(
            1
            for pair in st.session_state.get("calculated_pairs", {}).values()
            if pair.get("selected", False)
        )
        st.caption(
            t(
                "time_conformity_selected_runs_hint",
                pair_count=selected_pair_count,
                run_count=len(run_ids),
            )
        )

    if not run_ids:
        st.info(t("time_conformity_no_selected_runs"))
        return

    detailed_rows = []
    skipped_runs = []

    for run_id in run_ids:
        run_data = all_run_data.get(run_id, {})
        _, interval_rows = _normalize_interval_times(run_data)

        if not interval_rows:
            skipped_runs.append(run_id)
            continue

        heading_label = _format_run_heading(run_data.get("heading", ""), t)
        for interval_row in interval_rows:
            detailed_rows.append(
                {
                    t("run_id"): run_id,
                    "_run_id": run_id,
                    "_run_label": _format_run_column_label(run_id, t),
                    t("heading"): heading_label,
                    t("time_conformity_interval"): interval_row["interval_label"],
                    "_interval_start": interval_row["interval_start"],
                    "_interval_end": interval_row["interval_end"],
                    "_time_s": interval_row["time_s"],
                }
            )

    if not detailed_rows:
        st.warning(t("time_conformity_no_interval_data"))
        return

    detailed_df = pd.DataFrame(detailed_rows)
    interval_stats = (
        detailed_df.groupby(
            [t("time_conformity_interval"), "_interval_start", "_interval_end"],
            as_index=False,
        )["_time_s"]
        .agg(["mean", "min", "max", "count", "std"])
        .reset_index()
        .rename(
            columns={
                "mean": "_mean_time_s",
                "min": "_min_time_s",
                "max": "_max_time_s",
                "count": "_run_count",
                "std": "_std_time_s",
            }
        )
    )
    interval_stats["_std_time_s"] = interval_stats["_std_time_s"].fillna(0.0)
    interval_stats["_spread_s"] = (
        interval_stats["_max_time_s"] - interval_stats["_min_time_s"]
    )

    detailed_df = detailed_df.merge(
        interval_stats[
            [
                t("time_conformity_interval"),
                "_interval_start",
                "_interval_end",
                "_mean_time_s",
                "_std_time_s",
            ]
        ],
        on=[t("time_conformity_interval"), "_interval_start", "_interval_end"],
        how="left",
    )
    detailed_df["_deviation_s"] = detailed_df["_time_s"] - detailed_df["_mean_time_s"]
    detailed_df["_deviation_pct"] = np.where(
        np.abs(detailed_df["_mean_time_s"]) > 1e-9,
        (detailed_df["_deviation_s"] / detailed_df["_mean_time_s"]) * 100.0,
        np.nan,
    )
    detailed_df["_is_non_conforming"] = (
        np.abs(detailed_df["_deviation_pct"]) > float(tolerance_pct)
    )

    interval_stats = interval_stats.sort_values(
        by=["_interval_start", "_interval_end"],
        ascending=[False, False],
    )
    detailed_df = detailed_df.sort_values(
        by=["_interval_start", "_interval_end", t("run_id")],
        ascending=[False, False, True],
        key=lambda col: col.map(_run_sort_key) if col.name == t("run_id") else col,
    )

    interval_non_conforming = (
        detailed_df.groupby(
            [t("time_conformity_interval"), "_interval_start", "_interval_end"],
            as_index=False,
        )
        .agg(
            _max_deviation_pct=("_deviation_pct", lambda values: float(np.nanmax(np.abs(values))) if len(values) else np.nan),
            _non_conforming_count=("_is_non_conforming", "sum"),
        )
    )
    interval_cv = (
        detailed_df.groupby(
            [t("time_conformity_interval"), "_interval_start", "_interval_end"],
            as_index=False,
        )["_time_s"]
        .agg(lambda values: float((np.std(values, ddof=1) / np.mean(values)) * 100.0) if len(values) > 1 and abs(np.mean(values)) > 1e-9 else 0.0)
        .rename(columns={"_time_s": "_cv_pct"})
    )

    interval_stats = interval_stats.merge(
        interval_cv,
        on=[t("time_conformity_interval"), "_interval_start", "_interval_end"],
        how="left",
    ).merge(
        interval_non_conforming,
        on=[t("time_conformity_interval"), "_interval_start", "_interval_end"],
        how="left",
    )

    interval_stats["_non_conforming_count"] = (
        interval_stats["_non_conforming_count"].fillna(0).astype(int)
    )

    run_labels = {
        run_id: _format_run_column_label(run_id, t)
        for run_id in sorted(run_ids, key=_run_sort_key)
    }
    matrix_df = (
        detailed_df.pivot_table(
            index=[t("time_conformity_interval"), "_interval_start", "_interval_end"],
            columns="_run_label",
            values="_time_s",
            aggfunc="first",
        )
        .reset_index()
        .sort_values(by=["_interval_start", "_interval_end"], ascending=[False, False])
    )
    matrix_status_df = (
        detailed_df.pivot_table(
            index=[t("time_conformity_interval"), "_interval_start", "_interval_end"],
            columns="_run_label",
            values="_is_non_conforming",
            aggfunc="first",
        )
        .reset_index()
        .sort_values(by=["_interval_start", "_interval_end"], ascending=[False, False])
    )
    ordered_run_columns = [
        run_labels[run_id]
        for run_id in sorted(run_ids, key=_run_sort_key)
        if run_labels[run_id] in matrix_df.columns
    ]
    matrix_status_display = matrix_status_df[
        [t("time_conformity_interval")] + ordered_run_columns
    ].copy()
    for column in ordered_run_columns:
        matrix_status_display[column] = (
            matrix_status_display[column].fillna(False).astype(bool)
        )

    total_non_conforming = int(detailed_df["_is_non_conforming"].sum())
    intervals_with_non_conforming = int(
        (interval_stats["_non_conforming_count"] > 0).sum()
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric(t("runs_detected"), len(run_ids))
    with metric_col2:
        st.metric(t("time_conformity_intervals_count"), len(interval_stats))
    with metric_col3:
        st.metric(t("time_conformity_non_conforming_runs"), total_non_conforming)

    metric_col4, metric_col5 = st.columns(2)
    with metric_col4:
        st.metric(t("time_conformity_records_count"), len(detailed_df))
    with metric_col5:
        st.metric(
            t("time_conformity_non_conforming_intervals"),
            intervals_with_non_conforming,
        )

    if skipped_runs:
        skipped_str = ", ".join(
            str(run_id) for run_id in sorted(skipped_runs, key=_run_sort_key)
        )
        st.caption(t("time_conformity_skipped_runs", runs=skipped_str))

    st.markdown("---")
    st.subheader(t("time_conformity_matrix"))
    render_time_conformity_html_table(
        matrix_df,
        matrix_status_display,
        ordered_run_columns,
        detailed_df,
        t,
    )

    st.markdown("---")
    st.subheader(t("time_conformity_summary"))

    summary_interval_col = t("time_conformity_interval")
    summary_interval_label = _tc_text(t, "time_conformity_interval")
    summary_mean_label = _tc_text(t, "time_conformity_mean_time")
    summary_std_label = _tc_text(t, "time_conformity_std_time")
    summary_min_label = _tc_text(t, "time_conformity_min_time")
    summary_max_label = _tc_text(t, "time_conformity_max_time")
    summary_cv_label = _tc_text(t, "time_conformity_cv_pct")
    summary_max_dev_label = _tc_text(t, "time_conformity_max_deviation_pct")
    summary_non_conforming_label = _tc_text(
        t,
        "time_conformity_non_conforming_count",
    )
    summary_display = interval_stats[
        [
            summary_interval_col,
            "_mean_time_s",
            "_std_time_s",
            "_min_time_s",
            "_max_time_s",
            "_cv_pct",
            "_max_deviation_pct",
            "_non_conforming_count",
        ]
    ].rename(
        columns={
            summary_interval_col: summary_interval_label,
            "_mean_time_s": summary_mean_label,
            "_std_time_s": summary_std_label,
            "_min_time_s": summary_min_label,
            "_max_time_s": summary_max_label,
            "_cv_pct": summary_cv_label,
            "_max_deviation_pct": summary_max_dev_label,
            "_non_conforming_count": summary_non_conforming_label,
        }
    ).copy()

    for column in (
        summary_mean_label,
        summary_std_label,
        summary_min_label,
        summary_max_label,
        summary_cv_label,
        summary_max_dev_label,
    ):
        summary_display[column] = summary_display[column].map(
            lambda value: _format_detail_number(value, 2)
        )

    st.dataframe(summary_display, use_container_width=True, hide_index=True)


def render(t):
    """Renderiza a página de análise de pares."""

    # Verifica pré-requisito
    if not st.session_state.vehicle_data_complete:
        st.warning(t("error_no_mass"))
        return

    report_plot_mode = st.checkbox(
        t("report_plot_mode"),
        key="pair_analysis_report_plot_mode",
    )

    subtab_calc, subtab_graf, subtab_sim, subtab_conf = st.tabs([
        t('pair_calculations'),
        t("pair_analysis_graphs"),
        t("pair_analysis_simulation"),
        t("pair_time_conformity_tab"),
    ])

    with subtab_calc:
        st.markdown("### 🔗 Seleção de Pares")

        if legacy_uses_split_method(st.session_state):
            render_split_pair_selection(t)
        else:
            render_traditional_pair_selection(t)

        st.markdown("---")

        if st.session_state.calculated_pairs:
            render_calculated_pairs_table(t)

    with subtab_graf:
        if st.session_state.all_run_data:
            render_deceleration_graphs(t, report_plot_mode)
        else:
            st.info("💡 Carregue os dados do teste para visualizar os gráficos de desaceleração.")

    with subtab_sim:
        render_simulation(t, report_plot_mode)

    with subtab_conf:
        render_time_conformity_analysis(t)


def render_traditional_pair_selection(t):
    """Renderiza seleção de pares para método tradicional."""
    
    # Separa runs por direção (heading)
    runs_ida = []
    runs_volta = []
    
    for run_id, run_info in st.session_state.all_run_data.items():
        heading = run_info.get("heading", "")
        if heading in ["+", "N", "Norte", "North", "ida", "Ida", "IDA"]:
            runs_ida.append(run_id)
        elif heading in ["-", "S", "Sul", "South", "volta", "Volta", "VOLTA"]:
            runs_volta.append(run_id)
    
    # Se não conseguiu separar por heading, divide pela metade
    if not runs_ida or not runs_volta:
        all_runs = list(st.session_state.all_run_data.keys())
        mid = len(all_runs) // 2
        runs_ida = all_runs[:mid]
        runs_volta = all_runs[mid:]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_ida = st.selectbox(
            t("select_outbound_run"),
            options=runs_ida,
            key="selected_ida"
        )
    
    with col2:
        selected_volta = st.selectbox(
            t("select_return_run"),
            options=runs_volta,
            key="selected_volta"
        )
    
    st.markdown("---")
    
    # ===== CONDIÇÕES AMBIENTAIS =====
    st.subheader(f"🌡️ Correção Climática")
    
    # Opções de fonte de dados meteorológicos
    correction_mode = st.radio(
        "Fonte dos Dados Meteorológicos:",
        ["Sem Correção", "Manual (por passada)", "Arquivo Meteorológico"],
        horizontal=True
    )
    
    temp_ida = temp_volta = press_ida = press_volta = None
    wind_ida = wind_volta = None
    
    if correction_mode == "Manual (por passada)":
        st.markdown("#### 📊 Dados por Passada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔼 Passada IDA (+)**")
            temp_ida = st.number_input(
                "Temperatura Ida (°C)",
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="temp_ida"
            )
            press_ida = st.number_input(
                "Pressão Ida (kPa)",
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="press_ida"
            )
            wind_ida = st.number_input(
                "Vento Ida (m/s)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="wind_ida_manual"
            )
        
        with col2:
            st.markdown("**🔽 Passada VOLTA (-)**")
            temp_volta = st.number_input(
                "Temperatura Volta (°C)",
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="temp_volta"
            )
            press_volta = st.number_input(
                "Pressão Volta (kPa)",
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="press_volta"
            )
            wind_volta = st.number_input(
                "Vento Volta (m/s)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="wind_volta_manual"
            )
    
    elif correction_mode == "Arquivo Meteorológico":
        if st.session_state.weather_data:
            st.success(f"✅ Arquivo meteorológico carregado com {len(st.session_state.weather_data)} registros")
        else:
            st.warning("⚠️ Nenhum arquivo meteorológico foi carregado. Volte para a Página 1 para carregar.")
            correction_mode = "Sem Correção"

    if st.session_state.weather_data:
        sync_by_time_only = bool(st.session_state.get("sync_meteo_by_time_only", False))
        render_weather_sync_audit(
            [
                (f"{selected_ida} (+)", st.session_state.all_run_data.get(selected_ida, {})),
                (f"{selected_volta} (-)", st.session_state.all_run_data.get(selected_volta, {})),
            ],
            st.session_state.weather_data,
            sync_by_time_only,
            t
        )
    
    st.markdown("---")
    
    # ===== BOTÃO CALCULAR PAR =====
    if st.button(f"🔢 Calcular Par", type="primary", use_container_width=True):
        with st.spinner("Calculando par..."):
            try:
                # Obtém dados dos runs selecionados
                run_ida_info = st.session_state.all_run_data.get(selected_ida)
                run_volta_info = st.session_state.all_run_data.get(selected_volta)
                
                if not run_ida_info or not run_volta_info:
                    st.error("Erro: Runs selecionadas não encontradas!")
                    st.stop()
                
                # Obtém coeficientes individuais NÃO CORRIGIDOS
                coeffs_ida = st.session_state.individual_coeffs.get(selected_ida, {})
                coeffs_volta = st.session_state.individual_coeffs.get(selected_volta, {})
                
                f0_ida_raw = coeffs_ida.get("f0", 0)
                f2_ida_raw = coeffs_ida.get("f2", 0)
                f0_volta_raw = coeffs_volta.get("f0", 0)
                f2_volta_raw = coeffs_volta.get("f2", 0)
                
                # Calcula médias e CVs NÃO CORRIGIDOS
                from statistics import mean, stdev
                f0_mean = mean([f0_ida_raw, f0_volta_raw])
                f2_mean = mean([f2_ida_raw, f2_volta_raw])
                cv_f0 = (stdev([f0_ida_raw, f0_volta_raw]) / f0_mean) * 100 if f0_mean != 0 else 0
                cv_f2 = (stdev([f2_ida_raw, f2_volta_raw]) / f2_mean) * 100 if f2_mean != 0 else 0
                
                # Variáveis para valores corrigidos
                f0_ida_corr = f0_volta_corr = None
                f2_ida_corr = f2_volta_corr = None
                f0corr_mean = f2corr_mean = "N/A"
                cv_f0_corr = cv_f2_corr = "N/A"
                energy = "N/A"
                corrected = False
                
                temp_ida_used = temp_volta_used = "N/A"
                press_ida_used = press_volta_used = "N/A"
                wind_ida_ms = wind_volta_ms = wind_avg_ms = None
                
                # Aplica correção climática se necessário
                if correction_mode == "Manual (por passada)":
                    if temp_ida and press_ida and temp_volta and press_volta:
                        # Aplica correção POR PASSADA
                        f0_ida_corr, f2_ida_corr = apply_climate_correction(
                            f0_ida_raw, f2_ida_raw, temp_ida, press_ida
                        )
                        f0_volta_corr, f2_volta_corr = apply_climate_correction(
                            f0_volta_raw, f2_volta_raw, temp_volta, press_volta
                        )
                        
                        # Calcula médias e CVs CORRIGIDOS
                        f0corr_mean = mean([f0_ida_corr, f0_volta_corr])
                        f2corr_mean = mean([f2_ida_corr, f2_volta_corr])
                        cv_f0_corr = (stdev([f0_ida_corr, f0_volta_corr]) / f0corr_mean) * 100 if f0corr_mean != 0 else 0
                        cv_f2_corr = (stdev([f2_ida_corr, f2_volta_corr]) / f2corr_mean) * 100 if f2corr_mean != 0 else 0
                        
                        energy = calcular_energia(f0corr_mean, f2corr_mean)
                        corrected = True
                        
                        temp_ida_used = temp_ida
                        press_ida_used = press_ida
                        temp_volta_used = temp_volta
                        press_volta_used = press_volta
                        
                        # Vento manual
                        wind_ida_ms = wind_ida if wind_ida is not None and wind_ida > 0 else None
                        wind_volta_ms = wind_volta if wind_volta is not None and wind_volta > 0 else None
                        wind_vals = [w for w in [wind_ida_ms, wind_volta_ms] if w is not None]
                        wind_avg_ms = mean(wind_vals) if wind_vals else None
                        
                        # Aviso se vento > 3 m/s
                        if wind_avg_ms and wind_avg_ms > 3.0:
                            st.warning(f"⚠️ Vento médio ({wind_avg_ms:.2f} m/s) acima do recomendado pela norma (3.0 m/s)!")
                    else:
                        st.warning("⚠️ Preencha T/P para IDA e VOLTA para aplicar correção!")
                
                elif correction_mode == "Arquivo Meteorológico":
                    # Busca dados meteo mais próximos do timestamp de cada run
                    if st.session_state.weather_data:
                        sync_by_time_only = bool(st.session_state.get("sync_meteo_by_time_only", False))
                        has_valid_time = (
                            run_ida_info.get("start_timestamp") or run_ida_info.get("start_time_str")
                        ) and (
                            run_volta_info.get("start_timestamp") or run_volta_info.get("start_time_str")
                        )

                        if has_valid_time:
                            # Busca registro meteo mais próximo para cada run
                            weather_ida = find_closest_weather_record(
                                run_ida_info,
                                st.session_state.weather_data,
                                time_only=sync_by_time_only
                            )
                            weather_volta = find_closest_weather_record(
                                run_volta_info,
                                st.session_state.weather_data,
                                time_only=sync_by_time_only
                            )
                            
                            if weather_ida and weather_volta:
                                temp_ida_used = weather_ida.get('temp_c')
                                press_ida_used = weather_ida.get('baro_kpa')
                                wind_ida_ms = weather_ida.get('wind_ms')
                                
                                temp_volta_used = weather_volta.get('temp_c')
                                press_volta_used = weather_volta.get('baro_kpa')
                                wind_volta_ms = weather_volta.get('wind_ms')
                                
                                # Aplica correção POR PASSADA
                                f0_ida_corr, f2_ida_corr = apply_climate_correction(
                                    f0_ida_raw, f2_ida_raw, temp_ida_used, press_ida_used
                                )
                                f0_volta_corr, f2_volta_corr = apply_climate_correction(
                                    f0_volta_raw, f2_volta_raw, temp_volta_used, press_volta_used
                                )
                                
                                # Calcula médias e CVs CORRIGIDOS
                                f0corr_mean = mean([f0_ida_corr, f0_volta_corr])
                                f2corr_mean = mean([f2_ida_corr, f2_volta_corr])
                                cv_f0_corr = (stdev([f0_ida_corr, f0_volta_corr]) / f0corr_mean) * 100 if f0corr_mean != 0 else 0
                                cv_f2_corr = (stdev([f2_ida_corr, f2_volta_corr]) / f2corr_mean) * 100 if f2corr_mean != 0 else 0
                                
                                energy = calcular_energia(f0corr_mean, f2corr_mean)
                                corrected = True
                                
                                # Calcula vento médio
                                wind_vals = [w for w in [wind_ida_ms, wind_volta_ms] if w is not None]
                                wind_avg_ms = mean(wind_vals) if wind_vals else None
                                
                                # Aviso se vento > 3 m/s
                                if wind_avg_ms and wind_avg_ms > 3.0:
                                    st.warning(f"⚠️ Vento médio ({wind_avg_ms:.2f} m/s) acima do recomendado pela norma (3.0 m/s)!")
                            else:
                                st.warning("⚠️ Não foi possível encontrar dados meteorológicos para as runs selecionadas!")
                        else:
                            st.warning("⚠️ Runs não possuem timestamp para buscar dados meteorológicos!")
                
                # Monta current_pair_results (estrutura COMPLETA como no PyQt5)
                st.session_state.current_pair_results = {
                    "run_ida": selected_ida,
                    "run_volta": selected_volta,
                    
                    # Médias NÃO corrigidas
                    "f0_mean": f0_mean,
                    "f2_mean": f2_mean,
                    
                    # Médias CORRIGIDAS
                    "f0corr_mean": f0corr_mean,
                    "f2corr_mean": f2corr_mean,
                    
                    # Condições médias
                    "temp": (temp_ida_used + temp_volta_used) / 2 if corrected and temp_ida_used != "N/A" else "N/A",
                    "press": (press_ida_used + press_volta_used) / 2 if corrected and press_ida_used != "N/A" else "N/A",
                    
                    # Condições por passada
                    "temp_ida_used": temp_ida_used,
                    "press_ida_used": press_ida_used,
                    "temp_volta_used": temp_volta_used,
                    "press_volta_used": press_volta_used,
                    
                    # Coeficientes por passada (corrigidos se houver correção, senão brutos)
                    "f0_ida": f0_ida_corr if corrected else f0_ida_raw,
                    "f2_ida": f2_ida_corr if corrected else f2_ida_raw,
                    "f0_volta": f0_volta_corr if corrected else f0_volta_raw,
                    "f2_volta": f2_volta_corr if corrected else f2_volta_raw,
                    
                    # Coeficientes BRUTOS por passada
                    "f0_ida_raw": f0_ida_raw,
                    "f2_ida_raw": f2_ida_raw,
                    "f0_volta_raw": f0_volta_raw,
                    "f2_volta_raw": f2_volta_raw,
                    
                    # Coeficientes CORRIGIDOS por passada
                    "f0_ida_corr": f0_ida_corr,
                    "f2_ida_corr": f2_ida_corr,
                    "f0_volta_corr": f0_volta_corr,
                    "f2_volta_corr": f2_volta_corr,
                    
                    # CVs
                    "cv_f0": cv_f0,
                    "cv_f2": cv_f2,
                    "cv_f0_corr": cv_f0_corr,
                    "cv_f2_corr": cv_f2_corr,
                    
                    # Energia
                    "energy": energy,
                    
                    # Flags
                    "corrected": corrected,
                    
                    # Vento
                    "wind_ida_ms": wind_ida_ms,
                    "wind_volta_ms": wind_volta_ms,
                    "wind_avg_ms": wind_avg_ms,
                }
                
                st.success(f"✅ Par {selected_ida}/{selected_volta} calculado com sucesso!")
                
                # Mostra resultados
                st.markdown("---")
                st.subheader(f"📊 Resultados do Par")
                
                # Tabela de coeficientes NÃO CORRIGIDOS - com HTML para melhor visualização
                st.markdown("#### Coeficientes NÃO Corrigidos")
                
                # Cria HTML customizado para merge de células dos CVs
                html_uncorr = f"""
                <style>
                    .results-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 10px 0;
                    }}
                    .results-table th, .results-table td {{
                        border: 1px solid #444;
                        padding: 12px 8px;
                        text-align: center;
                    }}
                    .results-table th {{
                        background-color: #1f1f1f;
                        font-weight: bold;
                    }}
                    .results-table tr:nth-child(even) {{
                        background-color: #2a2a2a;
                    }}
                    .cv-cell {{
                        vertical-align: middle;
                        font-weight: bold;
                        background-color: #1a1a1a;
                    }}
                    .warning-cv {{
                        background-color: #ff6b6b;
                        color: #000;
                    }}
                    .warning-wind {{
                        background-color: #fff3cd;
                        color: #000;
                        font-weight: bold;
                    }}
                </style>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Run</th>
                            <th>f'0 (N)</th>
                            <th>f'2 (N/(m/s)²)</th>
                            <th>CV f'0 (%)</th>
                            <th>CV f'2 (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{selected_ida} ↑ [+]</td>
                            <td>{f0_ida_raw:.4f}</td>
                            <td>{f2_ida_raw:.6f}</td>
                            <td rowspan="3" class="cv-cell {'warning-cv' if cv_f0 > 10 else ''}">{cv_f0:.2f}</td>
                            <td rowspan="3" class="cv-cell {'warning-cv' if cv_f2 > 10 else ''}">{cv_f2:.2f}</td>
                        </tr>
                        <tr>
                            <td>{selected_volta} ↓ [-]</td>
                            <td>{f0_volta_raw:.4f}</td>
                            <td>{f2_volta_raw:.6f}</td>
                        </tr>
                        <tr>
                            <td><strong>Média</strong></td>
                            <td><strong>{f0_mean:.4f}</strong></td>
                            <td><strong>{f2_mean:.6f}</strong></td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(html_uncorr, unsafe_allow_html=True)
                
                # Tabela de coeficientes CORRIGIDOS (se houver)
                if corrected:
                    st.markdown("#### Coeficientes CORRIGIDOS")

                    def _format_optional_float(value, decimals=1):
                        try:
                            if value is None or pd.isna(value):
                                return "N/A"
                            return f"{float(value):.{decimals}f}"
                        except (TypeError, ValueError):
                            return "N/A"

                    wind_vals_corr = [
                        w for w in (wind_ida_ms, wind_volta_ms)
                        if w is not None and not pd.isna(w)
                    ]
                    wind_mean_corr = mean(wind_vals_corr) if wind_vals_corr else None
                    wind_ida_class = "warning-wind" if wind_ida_ms is not None and float(wind_ida_ms) > 3.0 else ""
                    wind_volta_class = "warning-wind" if wind_volta_ms is not None and float(wind_volta_ms) > 3.0 else ""
                    wind_mean_class = "warning-wind" if wind_mean_corr is not None and float(wind_mean_corr) > 3.0 else ""
                    energy_display = _format_optional_float(energy, 2)
                    
                    html_corr = f"""
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Run</th>
                                <th>T (°C)</th>
                                <th>P (kPa)</th>
                                <th>Vento (m/s)</th>
                                <th>f0 (N)</th>
                                <th>f2 (N/(km/h)²)</th>
                                <th>CV f0 (%)</th>
                                <th>CV f2 (%)</th>
                                <th>Energia</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{selected_ida} ↑ [+]</td>
                                <td>{temp_ida_used:.1f}</td>
                                <td>{press_ida_used:.1f}</td>
                                <td class="{wind_ida_class}">{_format_optional_float(wind_ida_ms, 1)}</td>
                                <td>{f0_ida_corr:.4f}</td>
                                <td>{f2_ida_corr:.6f}</td>
                                <td rowspan="3" class="cv-cell {'warning-cv' if cv_f0_corr > 10 else ''}">{cv_f0_corr:.2f}</td>
                                <td rowspan="3" class="cv-cell {'warning-cv' if cv_f2_corr > 10 else ''}">{cv_f2_corr:.2f}</td>
                                <td rowspan="3" class="cv-cell">{energy_display}</td>
                            </tr>
                            <tr>
                                <td>{selected_volta} ↓ [-]</td>
                                <td>{temp_volta_used:.1f}</td>
                                <td>{press_volta_used:.1f}</td>
                                <td class="{wind_volta_class}">{_format_optional_float(wind_volta_ms, 1)}</td>
                                <td>{f0_volta_corr:.4f}</td>
                                <td>{f2_volta_corr:.6f}</td>
                            </tr>
                            <tr>
                                <td><strong>Média</strong></td>
                                <td><strong>{(temp_ida_used + temp_volta_used)/2:.1f}</strong></td>
                                <td><strong>{(press_ida_used + press_volta_used)/2:.1f}</strong></td>
                                <td class="{wind_mean_class}"><strong>{_format_optional_float(wind_mean_corr, 1)}</strong></td>
                                <td><strong>{f0corr_mean:.4f}</strong></td>
                                <td><strong>{f2corr_mean:.6f}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                    """
                    st.markdown(html_corr, unsafe_allow_html=True)
                    
                    
                    # Avisos de CV alto
                    if cv_f0_corr > 10.0:
                        st.warning(f"⚠️ CV de f0 ({cv_f0_corr:.2f}%) está acima de 10%!")
                    if cv_f2_corr > 10.0:
                        st.warning(f"⚠️ CV de f2 ({cv_f2_corr:.2f}%) está acima de 10%!")
                
                # Botão para adicionar ao comparativo - SEMPRE VISÍVEL após cálculo
                st.markdown("---")
                
            except Exception as e:
                st.error(f"Erro ao calcular par: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Botão "Adicionar ao Comparativo" - FORA do try/except e do spinner
    # Só aparece se current_pair_results existe
    if st.session_state.get("current_pair_results"):
        if st.button("➕ Adicionar ao Comparativo", type="primary", use_container_width=True, key="add_to_comp"):
            try:
                pair_data = st.session_state.current_pair_results
                selected_ida = pair_data["run_ida"]
                selected_volta = pair_data["run_volta"]
                pair_id = f"{selected_ida}/{selected_volta}"
                
                # Adiciona ao calculated_pairs
                st.session_state.calculated_pairs[pair_id] = {
                    **pair_data,
                    "pair_id": pair_id,
                    "run1": selected_ida,
                    "run2": selected_volta,
                    "f0_corr": pair_data["f0corr_mean"],
                    "f2_corr": pair_data["f2corr_mean"],
                    "selected": False,
                }
                
                st.session_state.pairs_calculated = True
                st.success(f"✅ Par {pair_id} adicionado ao comparativo!")
                
                # Limpa current_pair_results para permitir novo cálculo
                st.session_state.current_pair_results = None
                
                # Pequeno delay para usuário ver a mensagem
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao adicionar par: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_split_pair_selection(t):
    """Renderiza seleção de pares para método split."""
    
    st.info("🔀 Método Split: Selecione runs de alta e baixa velocidade")
    
    # Runs de alta velocidade
    runs_alta = list(st.session_state.all_run_data_alta.keys()) if st.session_state.all_run_data_alta else []
    runs_baixa = list(st.session_state.all_run_data_baixa.keys()) if st.session_state.all_run_data_baixa else []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Alta Velocidade**")
        selected_alta_ida = st.selectbox(
            f"{t('select_outbound_run')} (Alta)",
            options=runs_alta[:len(runs_alta)//2] if runs_alta else [],
            key="selected_alta_ida"
        )
        selected_alta_volta = st.selectbox(
            f"{t('select_return_run')} (Alta)",
            options=runs_alta[len(runs_alta)//2:] if runs_alta else [],
            key="selected_alta_volta"
        )
    
    with col2:
        st.markdown("**Baixa Velocidade**")
        selected_baixa_ida = st.selectbox(
            f"{t('select_outbound_run')} (Baixa)",
            options=runs_baixa[:len(runs_baixa)//2] if runs_baixa else [],
            key="selected_baixa_ida"
        )
        selected_baixa_volta = st.selectbox(
            f"{t('select_return_run')} (Baixa)",
            options=runs_baixa[len(runs_baixa)//2:] if runs_baixa else [],
            key="selected_baixa_volta"
        )
    
    st.markdown("---")
    
    # ===== CONDIÇÕES AMBIENTAIS =====
    st.subheader(f"🌡️ {t('environmental_conditions')}")
    
    apply_correction = st.checkbox(t("apply_climate_correction"), value=True, key="split_correction")
    
    if apply_correction:
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.number_input(
                t("temperature"),
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="split_temp"
            )
        
        with col2:
            pressure = st.number_input(
                t("pressure"),
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="split_pressure"
            )
    else:
        temperature = 25.0
        pressure = 101.325
    
    st.markdown("---")
    
    # ===== BOTÃO CALCULAR PAR SPLIT =====
    if st.button(f"🔢 {t('calculate_pair')} (Split)", type="primary", use_container_width=True):
        with st.spinner("Calculando par split..."):
            try:
                # Obtém dados dos runs selecionados
                times_alta_ida, vels_alta_ida, _ = st.session_state.all_run_data_alta.get(selected_alta_ida, ([], [], ""))
                times_alta_volta, vels_alta_volta, _ = st.session_state.all_run_data_alta.get(selected_alta_volta, ([], [], ""))
                times_baixa_ida, vels_baixa_ida, _ = st.session_state.all_run_data_baixa.get(selected_baixa_ida, ([], [], ""))
                times_baixa_volta, vels_baixa_volta, _ = st.session_state.all_run_data_baixa.get(selected_baixa_volta, ([], [], ""))
                
                # Calcula F0/F2 usando método split
                f0, f2 = calcular_f0_f2_split(
                    times_alta_ida, vels_alta_ida,
                    times_alta_volta, vels_alta_volta,
                    times_baixa_ida, vels_baixa_ida,
                    times_baixa_volta, vels_baixa_volta,
                    st.session_state.total_mass,
                    st.session_state.ref_vel_alta,
                    st.session_state.ref_vel_baixa
                )
                
                # Aplica correção climática se solicitado
                if apply_correction:
                    f0_corrigido, f2_corrigido = apply_climate_correction(
                        f0, f2, temperature, pressure
                    )
                else:
                    f0_corrigido = f0
                    f2_corrigido = f2
                
                # Calcula energia
                energia = calcular_energia(f0_corrigido, f2_corrigido, 
                                          st.session_state.total_mass)
                
                # Cria ID do par
                pair_id = f"split_{selected_alta_ida}_{selected_baixa_ida}"
                
                # Armazena o par calculado
                pair_data = {
                    "pair_id": pair_id,
                    "run_alta_ida": selected_alta_ida,
                    "run_alta_volta": selected_alta_volta,
                    "run_baixa_ida": selected_baixa_ida,
                    "run_baixa_volta": selected_baixa_volta,
                    "f0_par": f0,
                    "f2_par": f2,
                    "f0_corrigido": f0_corrigido,
                    "f2_corrigido": f2_corrigido,
                    "energia": energia,
                    "temperature": temperature,
                    "pressure": pressure,
                    "apply_correction": apply_correction,
                    "method": "split",
                    "selected": False
                }
                
                st.session_state.calculated_pairs[pair_id] = pair_data
                st.session_state.pairs_calculated = True
                
                st.success(f"✅ Par Split {pair_id} calculado com sucesso!")
                
                # Mostra resultados
                st.markdown("---")
                st.subheader(f"📈 {t('pair_results')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(t("f0_coefficient"), f"{f0_corrigido:.4f} N")
                with col2:
                    st.metric(t("f2_coefficient"), f"{f2_corrigido:.6f} N/(km/h)²")
                with col3:
                    st.metric(t("energy"), f"{energia:.2f} J")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"{t('error_calculation')}: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_calculated_pairs_table(t):
    """Renderiza cards com prévia dos pares calculados."""
    
    if not st.session_state.calculated_pairs:
        st.info("Nenhum par adicionado ao comparativo ainda")
        return
    
    st.markdown("### 📊 Pares Adicionados ao Comparativo")
    
    # Para cada par, cria um card compacto com prévia
    for pair_id, pair in st.session_state.calculated_pairs.items():
        # Extrai dados
        temp_ida = pair.get("temp_ida_used", "N/A")
        temp_volta = pair.get("temp_volta_used", "N/A")
        press_ida = pair.get("press_ida_used", "N/A")
        press_volta = pair.get("press_volta_used", "N/A")
        wind_ida = pair.get("wind_ida_ms")
        wind_volta = pair.get("wind_volta_ms")
        
        # Formata T/P
        temp_str = f"{temp_ida:.1f}/{temp_volta:.1f}" if isinstance(temp_ida, (int, float)) else f"{temp_ida}/{temp_volta}"
        press_str = f"{press_ida:.2f}/{press_volta:.2f}" if isinstance(press_ida, (int, float)) else f"{press_ida}/{press_volta}"
        
        # Formata Vento
        if wind_ida is not None and wind_volta is not None:
            wind_str = f"{wind_ida:.2f}/{wind_volta:.2f}"
        elif wind_ida is not None:
            wind_str = f"{wind_ida:.2f}/N/A"
        elif wind_volta is not None:
            wind_str = f"N/A/{wind_volta:.2f}"
        else:
            wind_str = "N/A"
        
        # Coeficientes
        f0_corr = pair.get("f0_corr", pair.get("f0corr_mean", 0))
        f2_corr = pair.get("f2_corr", pair.get("f2corr_mean", 0))
        cv_f0 = pair.get("cv_f0_corr", pair.get("cv_f0", 0))
        cv_f2 = pair.get("cv_f2_corr", pair.get("cv_f2", 0))
        energy = pair.get("energy", 0)
        
        # Card compacto
        with st.expander(f"**Par {pair_id}**", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🌡️ Condições Ambientais**")
                st.write(f"Temp: {temp_str} °C")
                st.write(f"Press: {press_str} kPa")
                st.write(f"Vento: {wind_str} m/s")
            
            with col2:
                st.markdown("**📊 Coeficientes Corrigidos**")
                f0_str = f"{f0_corr:.4f}" if isinstance(f0_corr, (int, float)) else str(f0_corr)
                f2_str = f"{f2_corr:.6f}" if isinstance(f2_corr, (int, float)) else str(f2_corr)
                st.write(f"f0: {f0_str} N")
                st.write(f"f2: {f2_str} N/(km/h)²")
            
            with col3:
                st.markdown("**📈 Variações**")
                cv_f0_str = f"{cv_f0:.2f}%" if isinstance(cv_f0, (int, float)) else str(cv_f0)
                cv_f2_str = f"{cv_f2:.2f}%" if isinstance(cv_f2, (int, float)) else str(cv_f2)
                
                if isinstance(cv_f0, (int, float)) and cv_f0 > 10:
                    st.write(f"CV f0: :red[{cv_f0_str}] ⚠️")
                else:
                    st.write(f"CV f0: {cv_f0_str}")
                
                if isinstance(cv_f2, (int, float)) and cv_f2 > 10:
                    st.write(f"CV f2: :red[{cv_f2_str}] ⚠️")
                else:
                    st.write(f"CV f2: {cv_f2_str}")
            
            with col4:
                st.markdown("**⚡ Energia**")
                energy_str = f"{energy:.2f}" if isinstance(energy, (int, float)) else str(energy)
                # Aumenta a fonte do valor
                st.markdown(
                    f"<h2 class='mda-pair-energy-value'>{energy_str}</h2>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    "<p class='mda-pair-energy-unit'>MJ/km</p>",
                    unsafe_allow_html=True
                )
    
    st.markdown("---")
    st.info("💡 Vá para **Comparativo Final** para selecionar e comparar os pares")


def apply_report_plot_theme(fig):
    """Aplica tema claro aos gráficos Plotly para relatório/print."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black"),
        title_font=dict(color="black"),
        legend=dict(
            font=dict(color="black"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#cccccc",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#333333",
            font=dict(color="black"),
        ),
    )
    fig.update_xaxes(
        title_font=dict(color="black"),
        tickfont=dict(color="black"),
        color="black",
        linecolor="#333333",
        gridcolor="#dddddd",
        zerolinecolor="#cccccc",
        showgrid=True,
    )
    fig.update_yaxes(
        title_font=dict(color="black"),
        tickfont=dict(color="black"),
        color="black",
        linecolor="#333333",
        gridcolor="#dddddd",
        zerolinecolor="#cccccc",
        showgrid=True,
    )
    return fig


def render_deceleration_graphs(t, report_plot_mode=False):
    """Renderiza gráfico interativo de desaceleração (Velocidade × Tempo) com Plotly."""
    import re
    import plotly.graph_objects as go

    all_data = st.session_state.all_run_data
    if not all_data:
        st.warning("Dados das runs não disponíveis.")
        return

    pair_data = st.session_state.get("current_pair_results") or {}
    run_ida   = pair_data.get("run_ida")
    run_volta = pair_data.get("run_volta")

    # ===== SELEÇÃO DE RUNS =====
    available_runs = sorted(all_data.keys())
    run_labels = [f"Run {r} ({all_data[r].get('heading', 'N/A')})" for r in available_runs]

    # Default: runs do par ativo se existir, senão as 4 primeiras
    default_indices = [
        i for i, r in enumerate(available_runs) if r in (run_ida, run_volta)
    ] or list(range(min(4, len(available_runs))))

    selected_labels = st.multiselect(
        "Runs para plotar:",
        options=run_labels,
        default=[run_labels[i] for i in default_indices],
        key="graph_runs_select"
    )

    selected_run_ids = []
    for label in selected_labels:
        m = re.search(r"Run (\d+)", label)
        if m:
            selected_run_ids.append(int(m.group(1)))

    if not selected_run_ids:
        st.info("Selecione pelo menos uma run para visualizar o gráfico.")
        return

    # ===== CORES =====
    # Par ativo: ida = azul destacado, volta = laranja destacado
    # Restante: paleta discreta em cinza-colorido, mais fina e transparente
    COLOR_IDA   = "#4a9eff"   # azul (coincide com cor de destaque da UI)
    COLOR_VOLTA = "#ff9800"   # laranja
    COLORS_OTHER = [
        "#a0c4ff", "#b9fbc0", "#ffd6a5", "#ffadad",
        "#caffbf", "#9bf6ff", "#bdb2ff", "#ffc6ff",
    ]

    # ===== LEGENDA DO PAR ATIVO =====
    if run_ida or run_volta:
        ida_label   = f"Run {run_ida}"   if run_ida   else "—"
        volta_label = f"Run {run_volta}" if run_volta else "—"
        st.markdown(
            f"<div style='font-size:var(--mda-font-small); color:#a0a0a0; margin-bottom:6px'>"
            f"Par ativo: "
            f"<span style='color:{COLOR_IDA}; font-weight:600'>● {ida_label} (IDA)</span>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{COLOR_VOLTA}; font-weight:600'>● {volta_label} (VOLTA)</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # ===== GRÁFICO PLOTLY =====
    fig = go.Figure()

    other_color_idx = 0
    for run_id in selected_run_ids:
        if run_id not in all_data:
            continue

        data    = all_data[run_id]
        times   = data["times"]
        vels    = data["velocities"]
        heading = data.get("heading", "N/A")

        is_ida   = (run_id == run_ida)
        is_volta = (run_id == run_volta)
        is_pair  = is_ida or is_volta

        if is_ida:
            color = COLOR_IDA
            name  = f"Run {run_id} ★ IDA ({heading})"
        elif is_volta:
            color = COLOR_VOLTA
            name  = f"Run {run_id} ★ VOLTA ({heading})"
        else:
            color = COLORS_OTHER[other_color_idx % len(COLORS_OTHER)]
            name  = f"Run {run_id} ({heading})"
            other_color_idx += 1

        fig.add_trace(go.Scatter(
            x=times,
            y=vels,
            mode="lines",
            name=name,
            line=dict(
                color=color,
                width=3 if is_pair else 1.5,
            ),
            opacity=1.0 if is_pair else 0.6,
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Tempo: %{x:.2f} s<br>"
                "Velocidade: %{y:.2f} km/h<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(
            text="Curvas de Desaceleração — Velocidade × Tempo",
            font=dict(size=15, color="white"),
        ),
        xaxis=dict(
            title="Tempo (s)",
            color="white",
            gridcolor="#2a2a2a",
            showgrid=True,
        ),
        yaxis=dict(
            title="Velocidade (km/h)",
            color="white",
            gridcolor="#2a2a2a",
            showgrid=True,
        ),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#0e1117",
        font=dict(color="white"),
        legend=dict(
            bgcolor="#1e1e2e",
            bordercolor="#3d3d3d",
            borderwidth=1,
            font=dict(size=11),
        ),
        hovermode="x unified",
        height=500,
        margin=dict(l=60, r=20, t=50, b=50),
    )

    if report_plot_mode:
        apply_report_plot_theme(fig)

    st.plotly_chart(fig, use_container_width=True)


def _resolve_coeff(pair, keys):
    """Retorna o primeiro valor numérico encontrado nas chaves do par."""
    for k in keys:
        v = pair.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def render_simulation(t, report_plot_mode=False):
    """Renderiza a aba de simulação: Força Resistiva e Validação Simulado vs Real."""
    import plotly.graph_objects as go
    import numpy as np

    all_data   = st.session_state.get("all_run_data", {})
    total_mass = st.session_state.get("total_mass", 0.0)
    calc_pairs = st.session_state.get("calculated_pairs", {})
    current    = st.session_state.get("current_pair_results") or {}

    # ===== FONTE DOS COEFICIENTES =====
    st.subheader("⚙️ Coeficientes para Simulação")

    source_options = ["Inserir manualmente"]
    if current:
        source_options.insert(0, "Par calculado atualmente")
    if calc_pairs:
        source_options.insert(0 if not current else 1, "Selecionar par calculado")

    coeff_source = st.radio(
        "Fonte dos coeficientes F0 e F2:",
        source_options,
        horizontal=True,
        key="sim_coeff_source"
    )

    f0, f2 = None, None

    if coeff_source == "Par calculado atualmente":
        f0 = _resolve_coeff(current, ("f0corr_mean", "f0_corr", "f0_mean"))
        f2 = _resolve_coeff(current, ("f2corr_mean", "f2_corr", "f2_mean"))
        if f0 is not None:
            st.caption(f"F0 = {f0:.4f} N  |  F2 = {f2:.6f} N/(km/h)²")

    elif coeff_source == "Selecionar par calculado":
        pair_ids = list(calc_pairs.keys())
        chosen = st.selectbox("Par:", pair_ids, key="sim_pair_select")
        if chosen:
            p  = calc_pairs[chosen]
            f0 = _resolve_coeff(p, ("f0_corr", "mean_f0_corrected", "f0corr_mean"))
            f2 = _resolve_coeff(p, ("f2_corr", "mean_f2_corrected", "f2corr_mean"))
            if f0 is not None:
                st.caption(f"Par {chosen}  →  F0 = {f0:.4f} N  |  F2 = {f2:.6f} N/(km/h)²")

    if coeff_source == "Inserir manualmente" or f0 is None:
        col1, col2 = st.columns(2)
        with col1:
            f0 = st.number_input(
                "F0 (N)", min_value=0.0, max_value=5000.0,
                value=float(f0) if f0 else 100.0,
                step=0.1, format="%.4f", key="sim_f0_input"
            )
        with col2:
            f2 = st.number_input(
                "F2 (N/(km/h)²)", min_value=0.0, max_value=1.0,
                value=float(f2) if f2 else 0.04,
                step=0.0001, format="%.6f", key="sim_f2_input"
            )

    if f0 is None or f2 is None:
        st.info("Defina os coeficientes acima para continuar.")
        return

    st.markdown("---")

    # ===== SIMULAÇÃO 1: FORÇA RESISTIVA =====
    st.subheader("📈 Força Resistiva  F = F0 + F2 · V²")

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_min = st.number_input("Velocidade mínima (km/h)", 0.0, 100.0, 0.0,  5.0, key="sim_vmin")
    with col_v2:
        v_max = st.number_input("Velocidade máxima (km/h)", 10.0, 250.0, 120.0, 5.0, key="sim_vmax")

    v_kmh  = np.linspace(v_min, v_max, 300)
    v_ms   = v_kmh / 3.6
    F_vals = f0 + f2 * (v_ms ** 2)

    # Velocidade de destaque (slider)
    v_highlight = st.slider(
        "Inspecionar velocidade (km/h)",
        float(v_min), float(v_max), min(80.0, float(v_max)),
        step=1.0, key="sim_v_slider"
    )
    v_h_ms    = v_highlight / 3.6
    F_h       = f0 + f2 * (v_h_ms ** 2)

    fig_f = go.Figure()

    fig_f.add_trace(go.Scatter(
        x=v_kmh, y=F_vals,
        mode="lines",
        name=f"F = {f0:.4f} + {f2:.6f}·V²",
        line=dict(color="#4a9eff", width=2.5),
        fill="tozeroy", fillcolor="rgba(74,158,255,0.10)",
        hovertemplate="V = %{x:.1f} km/h<br>F = %{y:.2f} N<extra></extra>",
    ))

    # Ponto de destaque
    fig_f.add_trace(go.Scatter(
        x=[v_highlight], y=[F_h],
        mode="markers+text",
        name=f"{v_highlight:.0f} km/h",
        marker=dict(color="#ff9800", size=12, symbol="circle"),
        text=[f"  {F_h:.2f} N"],
        textposition="middle right",
        textfont=dict(color="#ff9800", size=12),
        hovertemplate=f"V = {v_highlight:.1f} km/h<br>F = {F_h:.2f} N<extra></extra>",
    ))

    fig_f.update_layout(
        xaxis=dict(title="Velocidade (km/h)", color="white", gridcolor="#2a2a2a"),
        yaxis=dict(title="Força Resistiva (N)", color="white", gridcolor="#2a2a2a"),
        plot_bgcolor="#1a1a2e", paper_bgcolor="#0e1117",
        font=dict(color="white"),
        legend=dict(bgcolor="#1e1e2e", bordercolor="#3d3d3d", borderwidth=1),
        hovermode="x unified", height=400,
        margin=dict(l=60, r=20, t=30, b=50),
    )
    if report_plot_mode:
        apply_report_plot_theme(fig_f)

    st.plotly_chart(fig_f, use_container_width=True)

    # Métricas pontuais
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("F0 (atrito constante)", f"{f0:.4f} N")
    mc2.metric("F2 (aerodinâmica)", f"{f2:.6f} N/(km/h)²")
    mc3.metric(f"F a {v_highlight:.0f} km/h", f"{F_h:.2f} N")

    # Contribuições percentuais
    F_aero = f2 * (v_h_ms ** 2)
    pct_f0  = f0  / F_h * 100 if F_h > 0 else 0
    pct_f2  = F_aero / F_h * 100 if F_h > 0 else 0
    st.caption(
        f"A {v_highlight:.0f} km/h: atrito constante = **{pct_f0:.1f}%**  |  "
        f"resistência aerodinâmica = **{pct_f2:.1f}%** da força total"
    )

    st.markdown("---")

    # ===== SIMULAÇÃO 2: DESACELERAÇÃO SIMULADA vs REAL =====
    st.subheader("🔬 Desaceleração Simulada × Real")

    if not all_data:
        st.info("💡 Carregue um arquivo de teste para comparar a desaceleração simulada com a real.")
        return

    if total_mass <= 0:
        st.info("💡 Preencha a massa do veículo na página 'Dados do Veículo' para simular a desaceleração.")
        return

    # Seleção de run para comparação
    available_runs = sorted(all_data.keys())

    # Default: run ida do par atual, se existir
    default_run = current.get("run_ida", available_runs[0]) if current else available_runs[0]
    if default_run not in available_runs:
        default_run = available_runs[0]

    run_labels = [f"Run {r} ({all_data[r].get('heading', 'N/A')})" for r in available_runs]
    default_idx = available_runs.index(default_run)

    selected_label = st.selectbox(
        "Run real para comparar:",
        run_labels,
        index=default_idx,
        key="sim_run_compare"
    )
    import re
    m = re.search(r"Run (\d+)", selected_label)
    selected_run_id = int(m.group(1)) if m else available_runs[0]

    run_data   = all_data[selected_run_id]
    times_real = np.array(run_data["times"])
    vels_real  = np.array(run_data["velocities"])   # km/h

    # ===== INTEGRAÇÃO NUMÉRICA (Euler) =====
    # dV/dt = -F/m = -(f0 + f2·V²) / m   [V em m/s, F em N, m em kg]
    v0_ms  = vels_real[0] / 3.6
    t_end  = times_real[-1] - times_real[0]
    dt     = 0.05   # passo de integração (s)
    t_sim  = [0.0]
    v_sim  = [v0_ms]

    v = v0_ms
    while t_sim[-1] < t_end:
        dv = -(f0 + f2 * v**2) / total_mass * dt
        v  = max(v + dv, 0.0)
        t_sim.append(t_sim[-1] + dt)
        v_sim.append(v)
        if v <= 0:
            break

    t_sim_arr = np.array(t_sim) + times_real[0]
    v_sim_kmh = np.array(v_sim) * 3.6

    # ===== GRÁFICO =====
    fig_d = go.Figure()

    fig_d.add_trace(go.Scatter(
        x=times_real, y=vels_real,
        mode="lines",
        name=f"Real — Run {selected_run_id}",
        line=dict(color="#4a9eff", width=2.5),
        hovertemplate="t = %{x:.2f} s<br>V real = %{y:.2f} km/h<extra></extra>",
    ))

    fig_d.add_trace(go.Scatter(
        x=t_sim_arr, y=v_sim_kmh,
        mode="lines",
        name="Simulado (F0, F2, massa)",
        line=dict(color="#ff9800", width=2, dash="dash"),
        hovertemplate="t = %{x:.2f} s<br>V sim = %{y:.2f} km/h<extra></extra>",
    ))

    fig_d.update_layout(
        title=dict(
            text=f"Run {selected_run_id} — Desaceleração Real vs Simulada",
            font=dict(size=14, color="white"),
        ),
        xaxis=dict(title="Tempo (s)", color="white", gridcolor="#2a2a2a"),
        yaxis=dict(title="Velocidade (km/h)", color="white", gridcolor="#2a2a2a"),
        plot_bgcolor="#1a1a2e", paper_bgcolor="#0e1117",
        font=dict(color="white"),
        legend=dict(bgcolor="#1e1e2e", bordercolor="#3d3d3d", borderwidth=1),
        hovermode="x unified", height=450,
        margin=dict(l=60, r=20, t=50, b=50),
    )
    if report_plot_mode:
        apply_report_plot_theme(fig_d)

    st.plotly_chart(fig_d, use_container_width=True)

    # ===== ERRO MÉDIO =====
    # Interpola simulado nos instantes reais para calcular RMSE
    v_sim_interp = np.interp(times_real - times_real[0], t_sim, v_sim) * 3.6
    residuals    = vels_real - v_sim_interp
    rmse         = float(np.sqrt(np.mean(residuals ** 2)))
    max_err      = float(np.max(np.abs(residuals)))

    ec1, ec2 = st.columns(2)
    ec1.metric("RMSE (km/h)", f"{rmse:.3f}")
    ec2.metric("Erro máximo (km/h)", f"{max_err:.3f}")

    if rmse < 1.0:
        st.success("✅ Boa aderência: os coeficientes representam bem a desaceleração real.")
    elif rmse < 3.0:
        st.warning("⚠️ Aderência moderada: possível influência de vento, inclinação ou variação de massa.")
    else:
        st.error("❌ Baixa aderência: verifique os coeficientes e as condições do ensaio.")

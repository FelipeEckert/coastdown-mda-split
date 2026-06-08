# coding: utf-8
"""Manual Split high/low run selection and coefficient calculation."""

import pandas as pd
import streamlit as st

from core.split_comparison import (
    add_split_comparison_pair,
    build_split_comparison_pair,
    clear_split_comparison_pairs,
    remove_split_comparison_pair,
)
from core.split_calculations import calculate_split_result
from data.loaders import find_closest_weather_record
from data.split_parser import default_split_interval_config


def _effective_mass():
    vehicle_info = st.session_state.get("vehicle_info") or {}
    value = vehicle_info.get("effective_mass") or st.session_state.get("total_mass")
    try:
        mass = float(value)
    except (TypeError, ValueError):
        return None
    return mass if mass > 0 else None


def _record_label(record: dict) -> str:
    parts = [
        str(record.get("filename") or "N/A"),
        f"run {record.get('run_id', 'N/A')}",
    ]
    heading = record.get("heading")
    if heading and heading != "N/A":
        parts.append(f"dir {heading}")
    start_time = record.get("start_time_str")
    if start_time:
        parts.append(str(start_time))
    parts.append(f"dt={float(record.get('delta_t_s') or 0):.3f}s")
    return " | ".join(parts)


def _record_summary(prefix: str, record: dict) -> dict:
    return {
        f"{prefix} file": record.get("filename"),
        f"{prefix} run": record.get("run_id"),
        f"{prefix} direction": record.get("heading"),
        f"{prefix} timestamp": record.get("start_time_str") or record.get("start_timestamp"),
        f"{prefix} Delta t (s)": record.get("delta_t_s"),
        f"{prefix} Delta V (km/h)": record.get("delta_v_kmh"),
        f"{prefix} subintervals": ", ".join(record.get("subintervals", [])),
    }


def _input_summary(high_record: dict, low_record: dict, effective_mass: float, config: dict) -> pd.DataFrame:
    rows = []
    high_cfg = config["high"]
    low_cfg = config["low"]
    values = {}
    values.update(_record_summary("High", high_record))
    values.update(_record_summary("Low", low_record))
    values.update(
        {
            "Effective mass (kg)": effective_mass,
            "V1 low reference (km/h)": low_cfg["reference"],
            "V2 high reference (km/h)": high_cfg["reference"],
            "Delta V1 low (km/h)": low_record.get("delta_v_kmh"),
            "Delta V2 high (km/h)": high_record.get("delta_v_kmh"),
        }
    )
    for item, value in values.items():
        rows.append({"Input": item, "Value": value})
    return pd.DataFrame(rows)


def _render_meteo_status(t):
    weather_data = st.session_state.get("weather_data")
    if not weather_data:
        st.warning(t("split_meteo_not_available_warning"))
        return

    mode_key = (
        "meteo_sync_mode_time_only"
        if st.session_state.get("sync_meteo_by_time_only")
        else "meteo_sync_mode_full_datetime"
    )
    st.info(t("split_meteo_loaded_not_applied_warning", mode=t(mode_key)))


def _synced_weather(record: dict):
    weather_data = st.session_state.get("weather_data")
    if not weather_data:
        return None
    return find_closest_weather_record(
        record,
        weather_data,
        time_only=bool(st.session_state.get("sync_meteo_by_time_only")),
    )


def _fmt(value, precision=3):
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    return "N/A" if value in (None, "") else str(value)


def _comparison_rows(pairs: list[dict]) -> list[dict]:
    rows = []
    for pair in pairs:
        rows.append(
            {
                "ID": pair.get("id"),
                "High run": pair.get("high_run"),
                "Low run": pair.get("low_run"),
                "f'0 (N)": pair.get("f0_prime"),
                "f'2 (N/(m/s)^2)": pair.get("f2_prime"),
                "Mass (kg)": pair.get("effective_mass"),
                "Temp (C)": pair.get("temp_c"),
                "Pressure (kPa)": pair.get("baro_kpa"),
                "Wind (m/s)": pair.get("wind_ms"),
                "Energy": pair.get("energy_status") if pair.get("energy") is None else pair.get("energy"),
            }
        )
    return rows


def _render_pair_card(pair: dict, t):
    label = (
        f"{pair.get('id')} | high {pair.get('high_run')} + low {pair.get('low_run')} | "
        f"f'0={_fmt(pair.get('f0_prime'), 4)} N"
    )
    with st.expander(label, expanded=False):
        col_high, col_low = st.columns(2)
        with col_high:
            st.markdown(f"**{t('split_card_high_source')}**")
            st.write(f"{t('split_file')}: {_fmt(pair.get('high_file'))}")
            st.write(f"{t('split_run')}: {_fmt(pair.get('high_run'))}")
            st.write(f"{t('split_direction')}: {_fmt(pair.get('high_direction'))}")
            st.write(f"{t('split_timestamp')}: {_fmt(pair.get('high_timestamp'))}")
            st.write(f"Delta t: {_fmt(pair.get('high_delta_t_s'))} s")
        with col_low:
            st.markdown(f"**{t('split_card_low_source')}**")
            st.write(f"{t('split_file')}: {_fmt(pair.get('low_file'))}")
            st.write(f"{t('split_run')}: {_fmt(pair.get('low_run'))}")
            st.write(f"{t('split_direction')}: {_fmt(pair.get('low_direction'))}")
            st.write(f"{t('split_timestamp')}: {_fmt(pair.get('low_timestamp'))}")
            st.write(f"Delta t: {_fmt(pair.get('low_delta_t_s'))} s")

        st.markdown(f"**{t('split_card_coefficients')}**")
        st.write(f"f'0: {_fmt(pair.get('f0_prime'), 6)} N")
        st.write(f"f'2: {_fmt(pair.get('f2_prime'), 9)} N/(m/s)^2")
        st.write(f"{t('split_effective_mass_available')}: {_fmt(pair.get('effective_mass'))} kg")
        st.write(f"V1/V2: {_fmt(pair.get('v1_reference_kmh'))} / {_fmt(pair.get('v2_reference_kmh'))} km/h")
        st.write(f"Delta V1/V2: {_fmt(pair.get('delta_v1_kmh'))} / {_fmt(pair.get('delta_v2_kmh'))} km/h")

        st.markdown(f"**{t('split_card_meteo')}**")
        if pair.get("temp_c") is None and pair.get("baro_kpa") is None and pair.get("wind_ms") is None:
            st.write(t("split_meteo_not_synced_for_pair"))
        else:
            st.write(f"{t('temperature')}: {_fmt(pair.get('temp_c'))} C")
            st.write(f"{t('pressure')}: {_fmt(pair.get('baro_kpa'))} kPa")
            st.write(f"{t('meteo_sync_col_wind')}: {_fmt(pair.get('wind_ms'))} m/s")
            st.caption(t("split_meteo_display_only_warning"))

        st.markdown(f"**{t('split_card_energy')}**")
        st.write(pair.get("energy_status") or _fmt(pair.get("energy")))

        warnings = pair.get("warnings") or []
        if warnings:
            st.warning("; ".join(warnings))

        if st.button(t("split_remove_pair"), key=f"remove_{pair.get('id')}"):
            st.session_state.split_comparison_pairs = remove_split_comparison_pair(
                st.session_state.get("split_comparison_pairs") or [],
                pair.get("id"),
            )
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None
            st.rerun()


def _render_comparison_area(t):
    pairs = st.session_state.get("split_comparison_pairs") or []
    st.markdown("---")
    st.subheader(t("split_final_comparison_table"))

    last_result = st.session_state.get("split_last_calculated_result")
    if last_result:
        if st.button(t("split_add_to_final_comparison"), use_container_width=True):
            pair = build_split_comparison_pair(
                last_result,
                high_weather=_synced_weather(last_result.get("high_record") or {}),
                low_weather=_synced_weather(last_result.get("low_record") or {}),
            )
            st.session_state.split_comparison_pairs = add_split_comparison_pair(pairs, pair)
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None
            st.success(t("split_pair_added_to_comparison"))
            st.rerun()
    else:
        st.info(t("split_no_calculated_pair_to_add"))

    pairs = st.session_state.get("split_comparison_pairs") or []
    if not pairs:
        st.info(t("split_comparison_empty"))
        return

    st.dataframe(pd.DataFrame(_comparison_rows(pairs)), use_container_width=True, hide_index=True)

    if st.button(t("split_clear_final_comparison"), type="secondary", use_container_width=True):
        st.session_state.split_comparison_pairs = clear_split_comparison_pairs()
        st.session_state.split_final_results = {}
        st.session_state.excel_buffer = None
        st.rerun()

    st.subheader(t("split_comparison_pair_cards"))
    for pair in pairs:
        _render_pair_card(pair, t)


def render(t):
    """Render manual Split coefficient calculation."""
    st.header(t("page_split_coefficient_calculation"))

    if not st.session_state.get("data_loaded"):
        st.warning(t("error_no_file"))
        return

    parsed = st.session_state.get("split_parsed_runs") or {}
    input_sources = st.session_state.get("split_input_sources") or []
    high_records = parsed.get("high") or []
    low_records = parsed.get("low") or []
    effective_mass = _effective_mass()
    config = st.session_state.get("split_interval_config") or default_split_interval_config()
    st.session_state.split_interval_config = config

    col_high, col_low, col_mass = st.columns(3)
    col_high.metric(t("split_high_records_available"), str(len(high_records)))
    col_low.metric(t("split_low_records_available"), str(len(low_records)))
    col_mass.metric(
        t("split_effective_mass_available"),
        t("yes") if effective_mass else t("no"),
    )
    source_files = ", ".join(
        source.get("filename", "N/A")
        for source in input_sources
        if source.get("filename")
    ) or "N/A"
    st.caption(t("split_input_sources_summary", files=source_files))

    if not high_records and not low_records:
        st.warning(t("split_no_parsed_records_for_calculation"))
        return
    if not high_records:
        st.warning(t("split_no_high_records_for_calculation"))
        return
    if not low_records:
        st.warning(t("split_no_low_records_for_calculation"))
        return
    if effective_mass is None:
        st.warning(t("split_effective_mass_required_for_calculation"))
        return

    selection_key_suffix = (
        f"{st.session_state.get('active_test_id', 'test')}_"
        f"{st.session_state.get('split_input_version', 0)}"
    )

    st.subheader(t("split_manual_pair_selection"))
    high_index = st.selectbox(
        t("split_select_high_run"),
        options=list(range(len(high_records))),
        format_func=lambda idx: _record_label(high_records[idx]),
        key=f"split_calc_high_record_select_{selection_key_suffix}",
    )
    low_index = st.selectbox(
        t("split_select_low_run"),
        options=list(range(len(low_records))),
        format_func=lambda idx: _record_label(low_records[idx]),
        key=f"split_calc_low_record_select_{selection_key_suffix}",
    )

    high_record = high_records[high_index]
    low_record = low_records[low_index]

    st.subheader(t("split_selected_pair_inputs"))
    st.dataframe(
        _input_summary(high_record, low_record, effective_mass, config),
        use_container_width=True,
        hide_index=True,
    )

    _render_meteo_status(t)

    if st.button(t("split_calculate_selected_pair"), type="primary", use_container_width=True):
        try:
            result = calculate_split_result(high_record, low_record, effective_mass, config)
            st.session_state.split_results.append(result)
            st.session_state.split_last_calculated_result = result
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None

            st.success(t("split_selected_pair_calculated"))
            col_f0, col_f2 = st.columns(2)
            col_f0.metric("f'0", f"{result['f0_prime']:.6f} N")
            col_f2.metric("f'2", f"{result['f2_prime']:.9f} N/(m/s)^2")
            if result.get("warnings"):
                st.warning("; ".join(result["warnings"]))
        except ValueError as exc:
            st.error(str(exc))

    if st.session_state.get("split_results"):
        st.info(t("split_saved_results_count", count=len(st.session_state.split_results)))

    _render_comparison_area(t)

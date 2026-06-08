# coding: utf-8
"""Manual Split ida/volta run selection and coefficient calculation."""

import pandas as pd
import streamlit as st

from core.split_comparison import (
    add_split_comparison_pair,
    build_split_comparison_pair,
    calculate_complete_split_pair,
    clear_split_comparison_pairs,
    group_split_records_by_direction,
    remove_split_comparison_pair,
)
from data.loaders import find_closest_weather_record
from data.split_parser import default_split_interval_config


COMPONENT_LABEL_KEYS = {
    "high_plus": "split_high_speed_ida",
    "low_plus": "split_low_speed_ida",
    "high_minus": "split_high_speed_volta",
    "low_minus": "split_low_speed_volta",
}


def _record_direction(record: dict):
    for key in ("heading", "Heading", "direction", "Direction"):
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


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
    heading = _record_direction(record)
    if heading and heading != "N/A":
        parts.append(f"dir {heading}")
    start_time = record.get("start_time_str") or record.get("start_timestamp")
    if start_time:
        parts.append(str(start_time))
    parts.append(f"dt={float(record.get('delta_t_s') or 0):.3f}s")
    return " | ".join(parts)


def _record_summary(component: str, record: dict, t) -> dict:
    return {
        "Component": t(COMPONENT_LABEL_KEYS[component]),
        "File": record.get("filename"),
        "Run": record.get("run_id"),
        "Direction": _record_direction(record),
        "Timestamp": record.get("start_time_str") or record.get("start_timestamp"),
        "Delta t (s)": record.get("delta_t_s"),
        "Delta V (km/h)": record.get("delta_v_kmh"),
        "Subintervals": ", ".join(record.get("subintervals", [])),
    }


def _input_summary(selection: dict, effective_mass: float, config: dict, t) -> pd.DataFrame:
    rows = [
        _record_summary("high_plus", selection["high_plus"], t),
        _record_summary("low_plus", selection["low_plus"], t),
        _record_summary("high_minus", selection["high_minus"], t),
        _record_summary("low_minus", selection["low_minus"], t),
    ]
    high_cfg = config["high"]
    low_cfg = config["low"]
    rows.extend(
        [
            {"Component": "Me", "File": "Effective mass (kg)", "Run": effective_mass},
            {"Component": "V1", "File": "Low reference (km/h)", "Run": low_cfg["reference"]},
            {"Component": "V2", "File": "High reference (km/h)", "Run": high_cfg["reference"]},
            {
                "Component": "Delta V1",
                "File": "Low interval amplitude (km/h)",
                "Run": selection["low_plus"].get("delta_v_kmh"),
            },
            {
                "Component": "Delta V2",
                "File": "High interval amplitude (km/h)",
                "Run": selection["high_plus"].get("delta_v_kmh"),
            },
        ]
    )
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


def _weather_records_for_result(result: dict) -> dict:
    return {
        "high_plus": _synced_weather(result.get("high_plus") or {}),
        "low_plus": _synced_weather(result.get("low_plus") or {}),
        "high_minus": _synced_weather(result.get("high_minus") or {}),
        "low_minus": _synced_weather(result.get("low_minus") or {}),
    }


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
                "High +": pair.get("high_plus_run"),
                "Low +": pair.get("low_plus_run"),
                "High -": pair.get("high_minus_run"),
                "Low -": pair.get("low_minus_run"),
                "f'0 avg (N)": pair.get("f0_prime"),
                "f'2 avg (N/(m/s)^2)": pair.get("f2_prime"),
                "Mass (kg)": pair.get("effective_mass"),
                "Temp (C)": pair.get("temp_c"),
                "Pressure (kPa)": pair.get("baro_kpa"),
                "Wind (m/s)": pair.get("wind_ms"),
                "Energy": pair.get("energy_status") if pair.get("energy") is None else pair.get("energy"),
            }
        )
    return rows


def _pair_component_rows(pair: dict, t) -> list[dict]:
    rows = []
    for component in ("high_plus", "low_plus", "high_minus", "low_minus"):
        rows.append(
            {
                "Component": t(COMPONENT_LABEL_KEYS[component]),
                "File": pair.get(f"{component}_file"),
                "Run": pair.get(f"{component}_run"),
                "Direction": pair.get(f"{component}_direction"),
                "Timestamp": pair.get(f"{component}_timestamp"),
                "Delta t (s)": pair.get(f"{component}_delta_t_s"),
            }
        )
    return rows


def _result_rows(result: dict, t) -> list[dict]:
    result_plus = result.get("result_plus") or {}
    result_minus = result.get("result_minus") or {}
    result_mean = result.get("result_pair_mean") or {}
    return [
        {
            "Result": t("split_direction_plus_result"),
            "f'0 (N)": result_plus.get("f0_prime"),
            "f'2 (N/(m/s)^2)": result_plus.get("f2_prime"),
        },
        {
            "Result": t("split_direction_minus_result"),
            "f'0 (N)": result_minus.get("f0_prime"),
            "f'2 (N/(m/s)^2)": result_minus.get("f2_prime"),
        },
        {
            "Result": t("split_pair_average"),
            "f'0 (N)": result_mean.get("f0_prime"),
            "f'2 (N/(m/s)^2)": result_mean.get("f2_prime"),
        },
    ]


def _render_result_summary(result: dict, t):
    st.subheader(t("split_selected_pair_results"))
    result_mean = result.get("result_pair_mean") or {}
    col_f0, col_f2 = st.columns(2)
    col_f0.metric("f'0", f"{result_mean.get('f0_prime', 0):.6f} N")
    col_f2.metric("f'2", f"{result_mean.get('f2_prime', 0):.9f} N/(m/s)^2")
    st.dataframe(pd.DataFrame(_result_rows(result, t)), use_container_width=True, hide_index=True)
    if result.get("warnings"):
        st.warning("; ".join(result["warnings"]))


def _render_pair_card(pair: dict, t):
    label = (
        f"{pair.get('id')} | + {pair.get('high_plus_run')}/{pair.get('low_plus_run')} | "
        f"- {pair.get('high_minus_run')}/{pair.get('low_minus_run')} | "
        f"f'0={_fmt(pair.get('f0_prime'), 4)} N"
    )
    with st.expander(label, expanded=False):
        st.markdown(f"**{t('split_complete_pair_components')}**")
        st.dataframe(pd.DataFrame(_pair_component_rows(pair, t)), use_container_width=True, hide_index=True)

        st.markdown(f"**{t('split_card_coefficients')}**")
        results_df = pd.DataFrame(
            [
                {
                    "Result": t("split_direction_plus_result"),
                    "f'0 (N)": pair.get("f0_plus"),
                    "f'2 (N/(m/s)^2)": pair.get("f2_plus"),
                },
                {
                    "Result": t("split_direction_minus_result"),
                    "f'0 (N)": pair.get("f0_minus"),
                    "f'2 (N/(m/s)^2)": pair.get("f2_minus"),
                },
                {
                    "Result": t("split_pair_average"),
                    "f'0 (N)": pair.get("f0_prime"),
                    "f'2 (N/(m/s)^2)": pair.get("f2_prime"),
                },
            ]
        )
        st.dataframe(results_df, use_container_width=True, hide_index=True)
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
                weather_records=_weather_records_for_result(last_result),
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


def _selected_from_group(grouped: dict, component: str, label_key: str, selection_key_suffix: str):
    records = grouped[component]
    selected_index = st.selectbox(
        label_key,
        options=list(range(len(records))),
        format_func=lambda idx: _record_label(records[idx]),
        key=f"split_calc_{component}_select_{selection_key_suffix}",
    )
    return records[selected_index]


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
    grouped = group_split_records_by_direction(high_records, low_records)
    effective_mass = _effective_mass()
    config = st.session_state.get("split_interval_config") or default_split_interval_config()
    st.session_state.split_interval_config = config

    metric_cols = st.columns(5)
    metric_cols[0].metric(t("split_high_plus_records_available"), str(len(grouped["high_plus"])))
    metric_cols[1].metric(t("split_low_plus_records_available"), str(len(grouped["low_plus"])))
    metric_cols[2].metric(t("split_high_minus_records_available"), str(len(grouped["high_minus"])))
    metric_cols[3].metric(t("split_low_minus_records_available"), str(len(grouped["low_minus"])))
    metric_cols[4].metric(
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
    if grouped["invalid"]:
        st.warning(t("split_invalid_direction_records_warning", count=len(grouped["invalid"])))
        st.dataframe(
            pd.DataFrame(
                {
                    "Record": [_record_label(record) for record in grouped["invalid"]],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.warning(t("split_complete_ida_volta_pair_required"))
        return

    missing_components = [
        t(COMPONENT_LABEL_KEYS[component])
        for component in ("high_plus", "low_plus", "high_minus", "low_minus")
        if not grouped[component]
    ]
    if missing_components:
        st.warning(t("split_complete_pair_missing_components", components=", ".join(missing_components)))
        st.warning(t("split_complete_ida_volta_pair_required"))
        if effective_mass is None:
            st.warning(t("split_effective_mass_required_for_calculation"))
        _render_comparison_area(t)
        return
    if effective_mass is None:
        st.warning(t("split_effective_mass_required_for_calculation"))
        _render_comparison_area(t)
        return

    selection_key_suffix = (
        f"{st.session_state.get('active_test_id', 'test')}_"
        f"{st.session_state.get('split_input_version', 0)}"
    )

    st.subheader(t("split_manual_pair_selection"))
    col_plus, col_minus = st.columns(2)
    with col_plus:
        st.markdown(f"**{t('split_ida_plus')}**")
        high_plus = _selected_from_group(
            grouped,
            "high_plus",
            t("split_select_high_plus_run"),
            selection_key_suffix,
        )
        low_plus = _selected_from_group(
            grouped,
            "low_plus",
            t("split_select_low_plus_run"),
            selection_key_suffix,
        )
    with col_minus:
        st.markdown(f"**{t('split_volta_minus')}**")
        high_minus = _selected_from_group(
            grouped,
            "high_minus",
            t("split_select_high_minus_run"),
            selection_key_suffix,
        )
        low_minus = _selected_from_group(
            grouped,
            "low_minus",
            t("split_select_low_minus_run"),
            selection_key_suffix,
        )

    selection = {
        "high_plus": high_plus,
        "low_plus": low_plus,
        "high_minus": high_minus,
        "low_minus": low_minus,
    }

    st.subheader(t("split_selected_pair_inputs"))
    st.dataframe(
        _input_summary(selection, effective_mass, config, t),
        use_container_width=True,
        hide_index=True,
    )

    _render_meteo_status(t)

    if st.button(t("split_calculate_selected_pair"), type="primary", use_container_width=True):
        try:
            result = calculate_complete_split_pair(
                high_plus=high_plus,
                low_plus=low_plus,
                high_minus=high_minus,
                low_minus=low_minus,
                effective_mass=effective_mass,
                config=config,
            )
            st.session_state.setdefault("split_results", [])
            st.session_state.split_results.append(result)
            st.session_state.split_last_calculated_result = result
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None

            st.success(t("split_selected_pair_calculated"))
            _render_result_summary(result, t)
        except ValueError as exc:
            st.error(str(exc))

    if st.session_state.get("split_results"):
        st.info(t("split_saved_results_count", count=len(st.session_state.split_results)))

    _render_comparison_area(t)

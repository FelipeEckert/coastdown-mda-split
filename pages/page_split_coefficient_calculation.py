# coding: utf-8
"""Manual Split ida/volta run selection and coefficient calculation."""

import pandas as pd
import streamlit as st

from core.split_comparison import (
    add_split_comparison_pair,
    build_split_comparison_pair,
    calculate_complete_split_pair,
    clear_split_comparison_pairs,
    coefficient_variation_percent,
    group_split_records_by_direction,
    remove_split_comparison_pair,
)
from core.split_corrections import (
    apply_split_pair_correction,
    fixed_ambient_conditions,
    weather_sync_ambient_conditions,
)
from core.weather_sync import (
    DEFAULT_MAX_TIME_DELTA_SECONDS,
    sync_weather_to_run,
)
from core.split_state import invalidate_split_ambient_state
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


def _sync_weather(record: dict) -> dict:
    weather_data = st.session_state.get("weather_data")
    return sync_weather_to_run(
        record,
        weather_data,
        max_time_delta_seconds=DEFAULT_MAX_TIME_DELTA_SECONDS,
        allow_time_only_fallback=bool(st.session_state.get("sync_meteo_by_time_only")),
    )


def _weather_sync_for_selection(selection: dict) -> dict:
    return {
        component: _sync_weather(record)
        for component, record in selection.items()
    }


def _weather_sync_rows(weather_sync: dict, t) -> list[dict]:
    rows = []
    for component in ("high_plus", "low_plus", "high_minus", "low_minus"):
        sync = weather_sync.get(component) or {}
        rows.append(
            {
                t("split_meteo_component"): t(COMPONENT_LABEL_KEYS[component]),
                t("split_meteo_status"): (
                    t("split_meteo_matched")
                    if sync.get("matched")
                    else t("split_meteo_not_matched")
                ),
                t("split_meteo_method"): t(
                    f"split_meteo_method_{sync.get('sync_method', 'not_found')}"
                ),
                t("split_meteo_run_datetime"): sync.get("run_datetime"),
                t("split_meteo_weather_datetime"): sync.get("weather_datetime"),
                t("split_meteo_delta_seconds"): sync.get("time_delta_seconds"),
                t("split_meteo_temperature"): sync.get("temperature"),
                t("split_meteo_pressure"): sync.get("pressure"),
                t("split_meteo_wind_speed"): sync.get("wind_speed"),
                t("split_meteo_wind_direction"): sync.get("wind_direction"),
            }
        )
    return rows


def _render_weather_sync(selection: dict, t) -> dict:
    weather_sync = _weather_sync_for_selection(selection)
    weather_data = st.session_state.get("weather_data")
    if not weather_data:
        st.warning(t("split_meteo_not_available_warning"))
        return weather_sync

    mode_key = (
        "meteo_sync_mode_time_only"
        if st.session_state.get("sync_meteo_by_time_only")
        else "meteo_sync_mode_full_datetime"
    )
    st.info(t("split_meteo_loaded_for_correction", mode=t(mode_key)))
    st.caption(
        t(
            "split_meteo_sync_limit",
            seconds=DEFAULT_MAX_TIME_DELTA_SECONDS,
        )
    )
    st.dataframe(
        pd.DataFrame(_weather_sync_rows(weather_sync, t)),
        use_container_width=True,
        hide_index=True,
    )
    sync_warnings = []
    for sync in weather_sync.values():
        sync_warnings.extend(sync.get("warnings") or [])
    if sync_warnings:
        st.warning("\n".join(dict.fromkeys(sync_warnings)))
    return weather_sync


def _render_ambient_conditions(selection: dict, t) -> dict:
    st.subheader(t("split_ambient_conditions_title"))
    test_key = st.session_state.get("active_test_id", "test")
    mode_labels = {
        t("split_ambient_mode_fixed"): "fixed",
        t("split_ambient_mode_weather_sync"): "weather_sync",
    }
    current_mode = st.session_state.get("split_ambient_mode", "fixed")
    current_label = next(
        label
        for label, mode in mode_labels.items()
        if mode == current_mode
    )
    selected_label = st.radio(
        t("split_ambient_mode_label"),
        options=list(mode_labels.keys()),
        index=list(mode_labels.keys()).index(current_label),
        horizontal=True,
        key=f"split_ambient_mode_selector_{test_key}",
    )
    ambient_mode = mode_labels[selected_label]
    st.session_state.split_ambient_mode = ambient_mode

    if ambient_mode == "fixed":
        col_temp, col_press = st.columns(2)
        with col_temp:
            temperature = st.number_input(
                t("split_fixed_temperature"),
                value=float(st.session_state.get("split_fixed_temperature", 20.0)),
                min_value=-273.14,
                step=0.1,
                format="%.2f",
                key=f"split_fixed_temperature_input_{test_key}",
            )
        with col_press:
            pressure = st.number_input(
                t("split_fixed_pressure"),
                value=float(st.session_state.get("split_fixed_pressure", 101.325)),
                min_value=0.001,
                step=0.1,
                format="%.3f",
                key=f"split_fixed_pressure_input_{test_key}",
            )
        st.session_state.split_fixed_temperature = temperature
        st.session_state.split_fixed_pressure = pressure
        _apply_ambient_signature(
            ("fixed", round(float(temperature), 6), round(float(pressure), 6)),
            t,
        )
        st.info(t("split_fixed_conditions_apply_all"))
        return fixed_ambient_conditions(temperature, pressure)

    weather_sync = _render_weather_sync(selection, t)
    _apply_ambient_signature(
        (
            "weather_sync",
            st.session_state.get("split_meteo_csv_path"),
            bool(st.session_state.get("sync_meteo_by_time_only")),
        ),
        t,
    )
    conditions = weather_sync_ambient_conditions(weather_sync)
    if not conditions.get("available"):
        st.warning(t("split_weather_correction_unavailable"))
    return conditions


def _apply_ambient_signature(signature: tuple, t):
    previous = st.session_state.get("split_ambient_signature")
    changed = previous is not None and previous != signature
    if changed:
        invalidate_split_ambient_state(st.session_state)
        st.info(t("split_ambient_change_invalidated"))

    st.session_state.split_ambient_signature = signature
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        test_data = tests[active_test_id]
        for key in (
            "split_ambient_mode",
            "split_fixed_temperature",
            "split_fixed_pressure",
            "split_ambient_signature",
            "split_ambient_version",
            "split_results",
            "split_comparison_pairs",
            "split_last_calculated_result",
            "split_final_results",
            "excel_buffer",
        ):
            test_data[key] = st.session_state.get(key)


def _fmt(value, precision=3):
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    return "N/A" if value in (None, "") else str(value)


def _first_value(data: dict, *keys):
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def _ambient_mode_label(pair: dict, t) -> str:
    mode = pair.get("ambient_mode")
    if mode == "fixed":
        return t("split_ambient_mode_fixed_short")
    if mode == "weather_sync":
        return t("split_ambient_mode_weather_sync_short")
    return "N/A"


def _pair_warnings(pair: dict) -> str:
    warnings = list(pair.get("warnings") or [])
    if (pair.get("cv_F0_percent") or 0) > 10:
        warnings.append("CV F0 > 10%")
    if (pair.get("cv_F2_percent") or 0) > 10:
        warnings.append("CV F2 > 10%")
    return "; ".join(dict.fromkeys(warnings))


def _comparison_rows(pairs: list[dict], t) -> list[dict]:
    rows = []
    for pair in pairs:
        rows.append(
            {
                "ID": pair.get("id"),
                "High +": pair.get("high_plus_run"),
                "Low +": pair.get("low_plus_run"),
                "High -": pair.get("high_minus_run"),
                "Low -": pair.get("low_minus_run"),
                "f'0 avg (N)": _first_value(
                    pair,
                    "f0_prime_mean",
                    "f0_prime",
                ),
                "f'2 avg (N/(m/s)^2)": _first_value(
                    pair,
                    "f2_prime_mean",
                    "f2_prime",
                ),
                "F0 avg (N)": _first_value(pair, "F0_mean", "F0"),
                "F2 avg (N/(km/h)^2)": _first_value(pair, "F2_mean", "F2"),
                "Temp + / - (C)": (
                    f"{_fmt(pair.get('temp_plus_used'), 1)} / "
                    f"{_fmt(pair.get('temp_minus_used'), 1)}"
                ),
                "Pressure + / - (kPa)": (
                    f"{_fmt(pair.get('press_plus_used'), 2)} / "
                    f"{_fmt(pair.get('press_minus_used'), 2)}"
                ),
                t("split_ambient_mode_label"): _ambient_mode_label(pair, t),
                "Energy (MJ/km)": (
                    pair.get("energy")
                    if pair.get("energy") is not None
                    else "N/A"
                ),
                t("split_card_warnings"): _pair_warnings(pair),
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


def _pair_weather_rows(pair: dict, t) -> list[dict]:
    return _weather_sync_rows(pair.get("weather_sync") or {}, t)


def _result_rows(result: dict, t) -> list[dict]:
    return [
        {
            "Result": t("split_direction_plus_result"),
            "f'0 (N)": result.get("f0_prime_plus"),
            "f'2 (N/(m/s)^2)": result.get("f2_prime_plus"),
        },
        {
            "Result": t("split_direction_minus_result"),
            "f'0 (N)": result.get("f0_prime_minus"),
            "f'2 (N/(m/s)^2)": result.get("f2_prime_minus"),
        },
        {
            "Result": t("split_pair_average"),
            "f'0 (N)": _first_value(
                result,
                "f0_prime_mean",
                "f0_prime",
            ),
            "f'2 (N/(m/s)^2)": _first_value(
                result,
                "f2_prime_mean",
                "f2_prime",
            ),
        },
    ]


def _corrected_result_rows(result: dict, t) -> list[dict]:
    return [
        {
            "Result": t("split_direction_plus_result"),
            "F0 (N)": result.get("F0_plus"),
            "F2 (N/(km/h)^2)": result.get("F2_plus"),
            t("split_meteo_temperature"): result.get("temp_plus_used"),
            t("split_meteo_pressure"): result.get("press_plus_used"),
        },
        {
            "Result": t("split_direction_minus_result"),
            "F0 (N)": result.get("F0_minus"),
            "F2 (N/(km/h)^2)": result.get("F2_minus"),
            t("split_meteo_temperature"): result.get("temp_minus_used"),
            t("split_meteo_pressure"): result.get("press_minus_used"),
        },
        {
            "Result": t("split_pair_average"),
            "F0 (N)": _first_value(result, "F0_mean", "F0"),
            "F2 (N/(km/h)^2)": _first_value(result, "F2_mean", "F2"),
            t("split_meteo_temperature"): None,
            t("split_meteo_pressure"): None,
        },
    ]


def _render_result_summary(result: dict, t):
    st.subheader(t("split_uncorrected_results"))
    col_f0, col_f2 = st.columns(2)
    col_f0.metric(
        "f'0",
        f"{_first_value(result, 'f0_prime_mean', 'f0_prime'):.6f} N",
    )
    col_f2.metric(
        "f'2",
        f"{_first_value(result, 'f2_prime_mean', 'f2_prime'):.9f} N/(m/s)^2",
    )
    st.dataframe(pd.DataFrame(_result_rows(result, t)), use_container_width=True, hide_index=True)
    st.subheader(t("split_corrected_results"))
    if result.get("correction_available"):
        col_f0_corr, col_f2_corr = st.columns(2)
        col_f0_corr.metric(
            "F0",
            f"{_first_value(result, 'F0_mean', 'F0'):.6f} N",
        )
        col_f2_corr.metric(
            "F2",
            f"{_first_value(result, 'F2_mean', 'F2'):.9f} N/(km/h)^2",
        )
        st.dataframe(
            pd.DataFrame(_corrected_result_rows(result, t)),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            t(
                "split_ambient_source_summary",
                source=t(f"split_ambient_source_{result.get('ambient_source')}"),
            )
        )
    else:
        st.warning(t("split_corrected_results_unavailable"))
    st.write(
        f"{t('split_ambient_mode_label')}: "
        f"{_ambient_mode_label(result, t)}"
    )
    st.write(
        f"{t('split_card_temp_ida_volta')}: "
        f"{_fmt(result.get('temp_plus_used'), 1)} / "
        f"{_fmt(result.get('temp_minus_used'), 1)} C"
    )
    st.write(
        f"{t('split_card_pressure_ida_volta')}: "
        f"{_fmt(result.get('press_plus_used'), 2)} / "
        f"{_fmt(result.get('press_minus_used'), 2)} kPa"
    )
    st.write(
        f"{t('split_card_energy')}: "
        f"{_fmt(result.get('energy'), 4)}"
    )
    if result.get("energy") is None:
        st.caption(t("split_energy_unavailable_contract"))
    if result.get("warnings"):
        st.warning("; ".join(result["warnings"]))


def _render_pair_card(pair: dict, t, pair_number: int):
    label = (
        f"{t('split_pair')} {pair_number} | "
        f"+ {pair.get('high_plus_run')}/{pair.get('low_plus_run')} | "
        f"- {pair.get('high_minus_run')}/{pair.get('low_minus_run')} | "
        f"F0={_fmt(_first_value(pair, 'F0_mean', 'F0'), 2)} N"
    )
    with st.expander(label, expanded=False):
        ambient_col, coefficients_col, variation_col, energy_col = st.columns(4)

        with ambient_col:
            st.markdown(f"##### {t('split_card_ambient_conditions')}")
            st.write(
                f"{t('split_card_temp_ida_volta')}: "
                f"{_fmt(pair.get('temp_plus_used'), 1)} / "
                f"{_fmt(pair.get('temp_minus_used'), 1)} C"
            )
            st.write(
                f"{t('split_card_pressure_ida_volta')}: "
                f"{_fmt(pair.get('press_plus_used'), 2)} / "
                f"{_fmt(pair.get('press_minus_used'), 2)} kPa"
            )
            st.write(
                f"{t('split_card_wind_ida_volta')}: "
                f"{_fmt(pair.get('wind_plus_ms'), 2)} / "
                f"{_fmt(pair.get('wind_minus_ms'), 2)} m/s"
            )
            st.caption(
                f"{t('split_ambient_mode_label')}: "
                f"{_ambient_mode_label(pair, t)}"
            )

        with coefficients_col:
            st.markdown(f"##### {t('split_corrected_results')}")
            if pair.get("correction_available"):
                st.metric(
                    "F0",
                    f"{_fmt(_first_value(pair, 'F0_mean', 'F0'), 3)} N",
                )
                st.metric(
                    "F2",
                    f"{_fmt(_first_value(pair, 'F2_mean', 'F2'), 6)} "
                    "N/(km/h)^2",
                )
                st.caption(t("split_f2_explicit_conversion_note"))
            else:
                st.write(t("split_corrected_results_unavailable"))
            st.caption(
                f"f'0: {_fmt(_first_value(pair, 'f0_prime_mean', 'f0_prime'), 3)} N | "
                f"f'2: {_fmt(_first_value(pair, 'f2_prime_mean', 'f2_prime'), 6)} "
                "N/(m/s)^2"
            )

        with variation_col:
            st.markdown(f"##### {t('split_card_variations')}")
            for coefficient, value in (
                ("F0", pair.get("cv_F0_percent")),
                ("F2", pair.get("cv_F2_percent")),
            ):
                if value is None:
                    st.write(f"CV {coefficient}: N/A")
                elif value > 10:
                    st.warning(f"CV {coefficient}: {value:.2f}%")
                else:
                    st.write(f"CV {coefficient}: {value:.2f}%")

        with energy_col:
            st.markdown(f"##### {t('split_card_energy')}")
            if pair.get("energy") is None:
                st.metric(t("split_card_energy"), "N/A")
                st.caption(t("split_energy_unavailable_contract"))
            else:
                unit = pair.get("energy_unit") or "MJ/km"
                st.metric(t("split_card_energy"), f"{_fmt(pair.get('energy'), 4)} {unit}")
                if pair.get("energy_profile"):
                    st.caption(str(pair["energy_profile"]))

        st.caption(
            f"{t('split_effective_mass_available')}: "
            f"{_fmt(pair.get('effective_mass'))} kg | "
            f"V1/V2: {_fmt(pair.get('v1_reference_kmh'))} / "
            f"{_fmt(pair.get('v2_reference_kmh'))} km/h | "
            f"Delta V1/V2: {_fmt(pair.get('delta_v1_kmh'))} / "
            f"{_fmt(pair.get('delta_v2_kmh'))} km/h"
        )

        st.markdown(f"**{t('split_card_traceability')}**")
        st.dataframe(
            pd.DataFrame(_pair_component_rows(pair, t)),
            use_container_width=True,
            hide_index=True,
        )
        weather_sync = pair.get("weather_sync") or {}
        if weather_sync:
            st.dataframe(
                pd.DataFrame(_pair_weather_rows(pair, t)),
                use_container_width=True,
                hide_index=True,
            )

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
            pair = build_split_comparison_pair(last_result)
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

    st.dataframe(
        pd.DataFrame(_comparison_rows(pairs, t)),
        use_container_width=True,
        hide_index=True,
    )

    if st.button(t("split_clear_final_comparison"), type="secondary", use_container_width=True):
        st.session_state.split_comparison_pairs = clear_split_comparison_pairs()
        st.session_state.split_final_results = {}
        st.session_state.excel_buffer = None
        st.rerun()

    st.subheader(t("split_comparison_pair_cards"))
    for pair_number, pair in enumerate(pairs, start=1):
        if pair.get("cv_F0_percent") is None:
            pair["cv_F0_percent"] = coefficient_variation_percent(
                pair.get("F0_plus"),
                pair.get("F0_minus"),
            )
        if pair.get("cv_F2_percent") is None:
            pair["cv_F2_percent"] = coefficient_variation_percent(
                pair.get("F2_plus"),
                pair.get("F2_minus"),
            )
        _render_pair_card(pair, t, pair_number)


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

    ambient_conditions = _render_ambient_conditions(selection, t)

    if st.button(t("split_calculate_coefficients"), type="primary", use_container_width=True):
        try:
            result = calculate_complete_split_pair(
                high_plus=high_plus,
                low_plus=low_plus,
                high_minus=high_minus,
                low_minus=low_minus,
                effective_mass=effective_mass,
                config=config,
            )
            result = apply_split_pair_correction(result, ambient_conditions)
            st.session_state.setdefault("split_results", [])
            st.session_state.split_results.append(result)
            st.session_state.split_last_calculated_result = result
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None

            st.success(t("split_selected_pair_calculated"))
        except ValueError as exc:
            st.error(str(exc))

    last_result = st.session_state.get("split_last_calculated_result")
    if last_result:
        _render_result_summary(last_result, t)

    if st.session_state.get("split_results"):
        st.info(t("split_saved_results_count", count=len(st.session_state.split_results)))

    _render_comparison_area(t)

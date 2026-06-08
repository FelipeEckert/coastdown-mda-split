# coding: utf-8
"""Split workflow page: interval configuration, parsing review, and calculation."""

import pandas as pd
import streamlit as st

from core.split_calculations import calculate_split_result
from data.split_parser import default_split_interval_config, parse_split_sources


def _get_config() -> dict:
    config = st.session_state.get("split_interval_config") or default_split_interval_config()
    st.session_state.split_interval_config = config
    return config


def _record_label(record: dict) -> str:
    return (
        f"{record.get('filename')} | run {record.get('run_id')} | "
        f"{record.get('heading')} | dt={record.get('delta_t_s', 0):.3f}s"
    )


def _records_dataframe(records: list[dict]) -> pd.DataFrame:
    rows = []
    for record in records:
        rows.append(
            {
                "File": record.get("filename"),
                "Run": record.get("run_id"),
                "Direction": record.get("heading"),
                "Interval": f"{record.get('start_kmh'):g}-{record.get('end_kmh'):g}",
                "Reference": record.get("reference_kmh"),
                "Delta V": record.get("delta_v_kmh"),
                "Delta t": record.get("delta_t_s"),
                "Subintervals": ", ".join(record.get("subintervals", [])),
                "Warnings": "; ".join(record.get("warnings", [])),
            }
        )
    return pd.DataFrame(rows)


def _render_interval_config():
    config = _get_config()
    st.subheader("Split interval configuration")
    st.caption("Norm values are defaults only. Adjust them when the test setup requires different intervals.")

    high = config["high"]
    low = config["low"]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**High interval**")
        high["start"] = st.number_input("High start (km/h)", value=float(high["start"]), step=5.0)
        high["reference"] = st.number_input("High reference V2 (km/h)", value=float(high["reference"]), step=5.0)
        high["end"] = st.number_input("High end (km/h)", value=float(high["end"]), step=5.0)
    with col2:
        st.markdown("**Low interval**")
        low["start"] = st.number_input("Low start (km/h)", value=float(low["start"]), step=5.0)
        low["reference"] = st.number_input("Low reference V1 (km/h)", value=float(low["reference"]), step=5.0)
        low["end"] = st.number_input("Low end (km/h)", value=float(low["end"]), step=5.0)

    st.session_state.split_interval_config = config


def _ensure_parsed():
    sources = st.session_state.get("split_input_sources") or []
    config = _get_config()
    st.session_state.split_parsed_runs = parse_split_sources(sources, config)


def _split_input_mode_key(parsed: dict) -> str:
    """Resolve the input-mode message from actual parsed intervals."""
    input_mode = st.session_state.get("split_input_mode")
    if input_mode in {"single_combined", "full_or_combined"}:
        input_mode = "combined"
    if input_mode not in {"separate", "combined"}:
        input_mode = "separate"
    has_high = bool(parsed.get("high"))
    has_low = bool(parsed.get("low"))

    prefix = f"split_input_mode_{input_mode}"
    if has_high and has_low:
        return f"{prefix}_complete"
    if has_high:
        return f"{prefix}_high_only"
    if has_low:
        return f"{prefix}_low_only"
    return f"{prefix}_none"


def _render_split_input_mode(parsed: dict, t):
    message_key = _split_input_mode_key(parsed)
    if parsed.get("high") and parsed.get("low"):
        st.info(t(message_key))
    else:
        st.warning(t(message_key))


def render(t):
    """Render the Split workflow."""
    st.header(t("page_split_workflow"))

    if not st.session_state.get("data_loaded"):
        st.warning(t("error_no_file"))
        return
    if not st.session_state.get("vehicle_data_complete"):
        st.warning(t("split_vehicle_data_required"))
        return

    _render_interval_config()

    col_parse, col_reset = st.columns([0.7, 0.3])
    with col_parse:
        if st.button("Parse Split intervals", type="primary", use_container_width=True):
            _ensure_parsed()
    with col_reset:
        if st.button("Reset intervals", use_container_width=True):
            st.session_state.split_interval_config = default_split_interval_config()
            st.session_state.split_parsed_runs = {}
            st.rerun()

    if not st.session_state.get("split_parsed_runs"):
        _ensure_parsed()

    parsed = st.session_state.get("split_parsed_runs") or {}
    for warning in parsed.get("warnings", []):
        st.warning(warning)

    high_records = parsed.get("high", [])
    low_records = parsed.get("low", [])
    _render_split_input_mode(parsed, t)

    st.markdown("---")
    st.subheader("Parser review")
    high_tab, low_tab = st.tabs(["High interval", "Low interval"])
    with high_tab:
        if high_records:
            st.dataframe(_records_dataframe(high_records), use_container_width=True, hide_index=True)
        else:
            st.info("No high interval records found.")
    with low_tab:
        if low_records:
            st.dataframe(_records_dataframe(low_records), use_container_width=True, hide_index=True)
        else:
            st.info("No low interval records found.")

    st.markdown("---")
    st.subheader("Split calculation")
    if not high_records or not low_records:
        st.info("At least one high interval and one low interval are required.")
        return

    selection_key_suffix = (
        f"{st.session_state.get('active_test_id', 'test')}_"
        f"{st.session_state.get('split_input_version', 0)}"
    )
    high_index = st.selectbox(
        "High interval record",
        options=list(range(len(high_records))),
        format_func=lambda idx: _record_label(high_records[idx]),
        key=f"split_high_record_select_{selection_key_suffix}",
    )
    low_index = st.selectbox(
        "Low interval record",
        options=list(range(len(low_records))),
        format_func=lambda idx: _record_label(low_records[idx]),
        key=f"split_low_record_select_{selection_key_suffix}",
    )

    effective_mass = float(st.session_state.vehicle_info.get("effective_mass") or st.session_state.total_mass)
    st.caption(f"Effective mass used: {effective_mass:.1f} kg")

    if st.button("Calculate and save Split result", type="primary", use_container_width=True):
        try:
            result = calculate_split_result(
                high_records[high_index],
                low_records[low_index],
                effective_mass,
                _get_config(),
            )
            st.session_state.split_results.append(result)
            st.session_state.split_final_results = {}
            st.session_state.excel_buffer = None
            st.success("Split result saved.")
        except ValueError as exc:
            st.error(str(exc))

    if st.session_state.get("split_results"):
        st.info(f"{len(st.session_state.split_results)} Split result(s) saved. Open the results tab to aggregate/export.")

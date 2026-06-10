# coding: utf-8
"""Split workflow page: interval configuration, parsing review, and calculation."""

import pandas as pd
import streamlit as st

from core.split_state import invalidate_split_input_state, update_split_interval_config
from data.split_parser import (
    default_split_interval_config,
    normalize_split_interval_config,
    parse_split_sources,
    validate_split_interval_config,
)


def _get_config() -> dict:
    config = normalize_split_interval_config(
        st.session_state.get("split_interval_config")
    )
    st.session_state.split_interval_config = config
    return config


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


def _config_issue_text(issue: dict, t) -> str:
    if issue["code"] == "invalid_step":
        return t("split_interval_step_invalid")
    interval_name = t(f"split_interval_{issue.get('interval')}").lower()
    if issue["code"] == "incompatible_step":
        return t(
            "split_interval_step_incompatible",
            interval=interval_name,
            span=issue["span_kmh"],
            step=issue["step_kmh"],
        )
    if issue["code"] == "invalid_interval_order":
        return t("split_interval_order_invalid", interval=interval_name)
    if issue["code"] == "invalid_reference":
        return t("split_interval_reference_invalid", interval=interval_name)
    return t("split_interval_values_invalid", interval=interval_name)


def _render_interval_config(t) -> bool:
    config = _get_config()
    st.subheader(t("split_interval_configuration"))
    st.caption(t("split_interval_defaults_note"))

    high = config["high"]
    low = config["low"]
    widget_suffix = (
        f"{st.session_state.get('active_test_id', 'test')}_"
        f"{st.session_state.get('split_input_version', 0)}"
    )
    step_kmh = st.number_input(
        t("split_interval_step_kmh"),
        value=float(config["step_kmh"]),
        step=1.0,
        key=f"split_interval_step_{widget_suffix}",
    )
    input_step = step_kmh if step_kmh > 0 else 1.0
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t('split_interval_high')}**")
        high_start = st.number_input(
            t("split_high_start_kmh"),
            value=float(high["start"]),
            step=input_step,
            key=f"split_high_start_{widget_suffix}",
        )
        high_reference = st.number_input(
            t("split_high_reference_kmh"),
            value=float(high["reference"]),
            step=input_step,
            key=f"split_high_reference_{widget_suffix}",
        )
        high_end = st.number_input(
            t("split_high_end_kmh"),
            value=float(high["end"]),
            step=input_step,
            key=f"split_high_end_{widget_suffix}",
        )
    with col2:
        st.markdown(f"**{t('split_interval_low')}**")
        low_start = st.number_input(
            t("split_low_start_kmh"),
            value=float(low["start"]),
            step=input_step,
            key=f"split_low_start_{widget_suffix}",
        )
        low_reference = st.number_input(
            t("split_low_reference_kmh"),
            value=float(low["reference"]),
            step=input_step,
            key=f"split_low_reference_{widget_suffix}",
        )
        low_end = st.number_input(
            t("split_low_end_kmh"),
            value=float(low["end"]),
            step=input_step,
            key=f"split_low_end_{widget_suffix}",
        )

    new_config = {
        "step_kmh": float(step_kmh),
        "high": {
            "start": float(high_start),
            "reference": float(high_reference),
            "end": float(high_end),
        },
        "low": {
            "start": float(low_start),
            "reference": float(low_reference),
            "end": float(low_end),
        },
    }
    update_split_interval_config(st.session_state, new_config)

    issues = validate_split_interval_config(new_config)
    for issue in issues:
        st.warning(_config_issue_text(issue, t))
    return not issues


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

    config_is_valid = _render_interval_config(t)

    col_parse, col_reset = st.columns([0.7, 0.3])
    with col_parse:
        if st.button(
            t("split_parse_intervals"),
            type="primary",
            use_container_width=True,
            disabled=not config_is_valid,
        ):
            _ensure_parsed()
    with col_reset:
        if st.button(t("split_reset_intervals"), use_container_width=True):
            st.session_state.split_interval_config = default_split_interval_config()
            invalidate_split_input_state(st.session_state)
            st.rerun()

    if config_is_valid and not st.session_state.get("split_parsed_runs"):
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

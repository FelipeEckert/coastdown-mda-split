# coding: utf-8
"""Split workflow page: interval configuration, parsing review, and calculation."""

import pandas as pd
import streamlit as st

from core.split_state import (
    get_processed_split_review_state,
    initialize_split_parse_state,
    record_split_parse_failure,
    should_show_split_parse_details,
    store_processed_split_intervals,
    update_split_interval_draft,
)
from data.split_parser import (
    default_split_interval_config,
    normalize_split_interval_config,
    parse_split_sources,
    validate_split_interval_config,
)

DRAFT_WIDGET_PATHS = {
    "split_draft_step_kmh": ("step_kmh",),
    "split_draft_high_start_kmh": ("high", "start"),
    "split_draft_high_ref_kmh": ("high", "reference"),
    "split_draft_high_end_kmh": ("high", "end"),
    "split_draft_low_start_kmh": ("low", "start"),
    "split_draft_low_ref_kmh": ("low", "reference"),
    "split_draft_low_end_kmh": ("low", "end"),
}


def _get_config() -> dict:
    return normalize_split_interval_config(
        st.session_state.get("split_interval_config")
    )


def _get_draft_config() -> dict:
    processed_config = _get_config()
    initialize_split_parse_state(st.session_state, processed_config)
    draft_config = normalize_split_interval_config(
        st.session_state.get("split_interval_draft_config")
    )
    st.session_state.split_interval_draft_config = draft_config
    return draft_config


def _draft_widget_key(base_key: str) -> str:
    test_id = st.session_state.get("active_test_id") or "test"
    return f"{base_key}_{test_id}"


def _config_value(config: dict, path: tuple[str, ...]) -> float:
    value = config
    for part in path:
        value = value[part]
    return float(value)


def _initialize_draft_widgets(config: dict) -> None:
    for base_key, path in DRAFT_WIDGET_PATHS.items():
        widget_key = _draft_widget_key(base_key)
        if widget_key not in st.session_state:
            st.session_state[widget_key] = _config_value(config, path)


def _set_draft_widgets(config: dict) -> None:
    for base_key, path in DRAFT_WIDGET_PATHS.items():
        st.session_state[_draft_widget_key(base_key)] = _config_value(config, path)


def _reset_interval_draft() -> None:
    defaults = default_split_interval_config()
    _set_draft_widgets(defaults)
    update_split_interval_draft(st.session_state, defaults)


def _draft_config_from_widgets() -> dict:
    return {
        "step_kmh": float(st.session_state[_draft_widget_key("split_draft_step_kmh")]),
        "high": {
            "start": float(
                st.session_state[_draft_widget_key("split_draft_high_start_kmh")]
            ),
            "reference": float(
                st.session_state[_draft_widget_key("split_draft_high_ref_kmh")]
            ),
            "end": float(
                st.session_state[_draft_widget_key("split_draft_high_end_kmh")]
            ),
        },
        "low": {
            "start": float(
                st.session_state[_draft_widget_key("split_draft_low_start_kmh")]
            ),
            "reference": float(
                st.session_state[_draft_widget_key("split_draft_low_ref_kmh")]
            ),
            "end": float(
                st.session_state[_draft_widget_key("split_draft_low_end_kmh")]
            ),
        },
    }


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


def _render_interval_config(t) -> dict:
    config = _get_draft_config()
    _initialize_draft_widgets(config)
    st.subheader(t("split_interval_configuration"))
    st.caption(t("split_interval_defaults_note"))

    st.number_input(
        t("split_interval_step_kmh"),
        step=1.0,
        key=_draft_widget_key("split_draft_step_kmh"),
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t('split_interval_high')}**")
        st.number_input(
            t("split_high_start_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_high_start_kmh"),
        )
        st.number_input(
            t("split_high_reference_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_high_ref_kmh"),
        )
        st.number_input(
            t("split_high_end_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_high_end_kmh"),
        )
    with col2:
        st.markdown(f"**{t('split_interval_low')}**")
        st.number_input(
            t("split_low_start_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_low_start_kmh"),
        )
        st.number_input(
            t("split_low_reference_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_low_ref_kmh"),
        )
        st.number_input(
            t("split_low_end_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_low_end_kmh"),
        )

    new_config = _draft_config_from_widgets()
    update_split_interval_draft(st.session_state, new_config)
    return new_config


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

    draft_config = _render_interval_config(t)

    col_parse, col_reset = st.columns([0.7, 0.3])
    with col_parse:
        process_requested = st.button(
            t("split_parse_intervals"),
            type="primary",
            use_container_width=True,
        )
    with col_reset:
        st.button(
            t("split_reset_intervals"),
            use_container_width=True,
            on_click=_reset_interval_draft,
        )

    if process_requested:
        issues = validate_split_interval_config(draft_config)
        if issues:
            record_split_parse_failure(st.session_state, issues)
        else:
            sources = st.session_state.get("split_input_sources") or []
            parsed_runs = parse_split_sources(sources, draft_config)
            store_processed_split_intervals(
                st.session_state,
                draft_config,
                parsed_runs,
            )

    review_state = get_processed_split_review_state(st.session_state)
    processed_config = normalize_split_interval_config(review_state["config"])
    parsed = review_state["parsed_runs"]
    parse_dirty = bool(st.session_state.get("split_parse_dirty"))
    show_details = should_show_split_parse_details(st.session_state)
    validation_issues = st.session_state.get("split_parse_validation_issues") or []

    if parse_dirty:
        if parsed:
            st.warning(t("split_interval_config_dirty"))
        else:
            st.info(t("split_interval_edit_instruction"))
    elif not show_details:
        st.info(t("split_interval_edit_instruction"))

    if show_details:
        for issue in validation_issues:
            st.warning(_config_issue_text(issue, t))
        if not validation_issues:
            for warning in parsed.get("warnings", []):
                st.warning(warning)

    high_records = parsed.get("high", [])
    low_records = parsed.get("low", [])
    if show_details and not parse_dirty and not validation_issues:
        _render_split_input_mode(parsed, t)

    if parsed and (show_details or parse_dirty):
        st.markdown("---")
        st.subheader("Parser review")
        st.caption(
            t(
                "split_processed_interval_summary",
                high_start=processed_config["high"]["start"],
                high_end=processed_config["high"]["end"],
                high_reference=processed_config["high"]["reference"],
                low_start=processed_config["low"]["start"],
                low_end=processed_config["low"]["end"],
                low_reference=processed_config["low"]["reference"],
                step=processed_config["step_kmh"],
            )
        )
        if parse_dirty:
            st.caption(t("split_interval_preview_stale"))
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

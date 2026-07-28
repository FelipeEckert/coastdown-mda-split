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
    with st.container(border=True):
        st.subheader(
            f":material/tune: {t('split_interval_configuration')}"
        )
        st.caption(t("split_interval_defaults_note"))

        st.number_input(
            t("split_interval_step_kmh"),
            step=1.0,
            key=_draft_widget_key("split_draft_step_kmh"),
        )
        with st.container(horizontal=True, gap="small"):
            with st.container(border=True):
                st.markdown(
                    f"#### :material/speed: {t('split_interval_high')}"
                )
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
            with st.container(border=True):
                st.markdown(
                    f"#### :material/speed: {t('split_interval_low')}"
                )
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


def _render_input_sources(t) -> None:
    sources = st.session_state.get("split_input_sources") or []
    filenames = {
        source.get("role"): source.get("filename")
        for source in sources
        if source.get("filename")
    }
    input_mode = st.session_state.get("split_input_mode")
    if input_mode in {"single_combined", "full_or_combined"}:
        input_mode = "combined"
    if input_mode not in {"separate", "combined"}:
        input_mode = "separate"

    if input_mode == "combined":
        source_items = [
            (
                t("split_current_combined_file"),
                filenames.get("full_or_combined")
                or st.session_state.get("coastdown_csv_path"),
                "N/A",
                "description",
            ),
        ]
    else:
        source_items = [
            (
                t("split_current_high_file"),
                filenames.get("high")
                or st.session_state.get("split_alta_csv_path")
                or st.session_state.get("coastdown_csv_path"),
                "N/A",
                "speed",
            ),
            (
                t("split_current_low_file"),
                filenames.get("low")
                or st.session_state.get("split_baixa_csv_path"),
                t("split_no_low_file"),
                "speed",
            ),
        ]
    source_items.append(
        (
            t("split_current_weather_file"),
            st.session_state.get("split_meteo_csv_path")
            or st.session_state.get("meteo_csv_path"),
            t("no_meteo_file"),
            "cloud",
        )
    )

    with st.container(border=True):
        st.subheader(f":material/folder_open: {t('split_upload_sources')}")
        st.badge(
            t(f"split_input_mode_{input_mode}"),
            icon=":material/file_copy:" if input_mode == "combined" else ":material/folder:",
            color="blue",
        )
        with st.container(horizontal=True, gap="small"):
            for label, filename, empty_label, icon in source_items:
                with st.container(border=True):
                    st.markdown(f"**:material/{icon}: {label}**")
                    st.badge(
                        filename or empty_label,
                        icon=(
                            ":material/check_circle:"
                            if filename
                            else ":material/block:"
                        ),
                        color="green" if filename else "gray",
                    )


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
        st.success(t(message_key), icon=":material/check_circle:")
    else:
        st.warning(t(message_key), icon=":material/warning:")


def render(t):
    """Render the Split workflow."""
    st.header(t("page_split_workflow"))

    if not st.session_state.get("data_loaded"):
        st.warning(t("error_no_file"), icon=":material/upload_file:")
        return
    if not st.session_state.get("vehicle_data_complete"):
        st.warning(
            t("split_vehicle_data_required"),
            icon=":material/directions_car:",
        )
        return

    _render_input_sources(t)
    st.space("small")
    draft_config = _render_interval_config(t)

    with st.container(horizontal=True, gap="small"):
        process_requested = st.button(
            t("split_parse_intervals"),
            type="primary",
            width="stretch",
        )
        st.button(
            t("split_reset_intervals"),
            width="stretch",
            on_click=_reset_interval_draft,
        )

    if process_requested:
        with st.spinner(
            t("split_parse_intervals"),
            show_time=True,
            width="stretch",
        ):
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
            st.warning(
                t("split_interval_config_dirty"),
                icon=":material/edit_note:",
            )
        else:
            st.info(
                t("split_interval_edit_instruction"),
                icon=":material/info:",
            )
    elif not show_details:
        st.info(
            t("split_interval_edit_instruction"),
            icon=":material/info:",
        )

    if show_details:
        for issue in validation_issues:
            st.warning(
                _config_issue_text(issue, t),
                icon=":material/warning:",
            )
        if not validation_issues:
            for warning in parsed.get("warnings", []):
                st.warning(warning, icon=":material/warning:")

    high_records = parsed.get("high", [])
    low_records = parsed.get("low", [])
    if show_details and not parse_dirty and not validation_issues:
        _render_split_input_mode(parsed, t)

    if parsed and (show_details or parse_dirty):
        st.space("small")
        with st.container(border=True):
            st.subheader(":material/table_view: Parser review")
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
            with st.container(horizontal=True, gap="small"):
                st.badge(
                    f"{t('split_interval_high')}: {len(high_records)}",
                    icon=":material/speed:",
                    color="blue",
                )
                st.badge(
                    f"{t('split_interval_low')}: {len(low_records)}",
                    icon=":material/speed:",
                    color="blue",
                )
            if parse_dirty:
                st.caption(t("split_interval_preview_stale"))
            tab_labels = ["High interval", "Low interval"]
            tab_key = (
                f"split_workflow_review_tabs_{st.session_state.active_test_id}_"
                f"{st.session_state.language}"
            )
            if st.session_state.get(tab_key) not in tab_labels:
                st.session_state[tab_key] = tab_labels[0]
            high_tab, low_tab = st.tabs(
                tab_labels,
                default=st.session_state[tab_key],
                key=tab_key,
                on_change="rerun",
            )
            if high_tab.open:
                with high_tab:
                    if high_records:
                        st.dataframe(
                            _records_dataframe(high_records),
                            width="stretch",
                            hide_index=True,
                        )
                    else:
                        st.info("No high interval records found.")
            elif low_tab.open:
                with low_tab:
                    if low_records:
                        st.dataframe(
                            _records_dataframe(low_records),
                            width="stretch",
                            hide_index=True,
                        )
                    else:
                        st.info("No low interval records found.")

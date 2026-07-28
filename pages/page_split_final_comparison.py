# coding: utf-8
"""Final comparison page for calculated Coastdown Split pairs."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from core.split_comparison import (
    clear_split_comparison_pairs,
    format_split_comparison_display_value,
    is_split_pair_corrected,
    normalize_split_comparison_pairs,
    normalize_split_pair_for_comparison,
    remove_split_comparison_pair,
    selected_corrected_split_comparison_pairs,
    set_split_comparison_selected_ids,
    split_comparison_cv_warning,
)
from core.split_deviation_analysis import get_cached_split_deviation_analysis
from core.split_display import (
    format_split_opposite_time_label,
    format_split_time_group_label,
    get_split_reference_speeds,
)
from core.split_results import consolidate_split_final_results
from core.split_state import (
    clear_split_final_results_compatibility,
    clear_split_comparison_state,
    normalize_split_comparison_selection_state,
    reset_split_final_outputs,
)


ROW_RATIOS = [0.5, 2.2, 0.9, 0.9, 1.0, 1.1, 1.1, 0.8, 0.8, 1.0, 0.5]
SELECTED_ROW_BG = "rgba(18,100,200,0.32)"
SELECTED_ROW_TEXT = "#F4F8FC"
DEFAULT_ROW_BG = "#0D1B2B"
DEFAULT_ROW_TEXT = "#F4F8FC"
ENERGY_ROW_BG = "rgba(45,211,111,0.18)"
ENERGY_ROW_TEXT = "#B7F7CC"
TARGET_ROW_BG = "rgba(58,156,255,0.18)"
TARGET_ROW_TEXT = "#B9DCFF"
ENERGY_TARGET_ROW_BG = "rgba(179,157,255,0.20)"
ENERGY_TARGET_ROW_TEXT = "#DED5FF"
REFERENCE_ROW_BG = "rgba(245,184,46,0.12)"
REFERENCE_ROW_TEXT = "#FFD978"
CV_WARNING_TEXT = "#FF8A8A"
TABLE_CELL_HEIGHT = "50px"


def _selection_source_label(source: str, t) -> str:
    if source == "manual":
        return t("split_selection_source_manual")
    if source == "algorithm":
        return t("split_selection_source_algorithm")
    return t("split_selection_source_unknown")


def get_pair_origin_visual_state(pair: dict) -> str:
    """Return the row's visual origin without changing final selection state."""
    if not is_split_pair_corrected(pair):
        return "uncorrected"

    sources = pair.get("algorithm_sources") or []
    if isinstance(sources, str):
        sources = [sources]
    normalized_sources = {
        str(source).strip().lower()
        for source in sources
        if str(source).strip()
    }
    algorithm_source = str(pair.get("algorithm_source") or "").strip().lower()
    if algorithm_source in {"energy", "target"}:
        normalized_sources.add(algorithm_source)
    if pair.get("selected_by_energy_algo"):
        normalized_sources.add("energy")
    if pair.get("selected_by_target_algo"):
        normalized_sources.add("target")

    if {"energy", "target"}.issubset(normalized_sources):
        return "energy_and_target"
    if "energy" in normalized_sources:
        return "energy"
    if "target" in normalized_sources:
        return "target"
    if str(pair.get("selection_source") or "").strip().lower() == "manual":
        return "manual"
    if pair.get("selected", False):
        return "selected_final"
    return "unknown"


def _comparison_rows(pairs: list[dict], t) -> list[dict]:
    """Translate normalized Split comparison rows for tests/export previews."""
    rows = []
    for index, pair in enumerate(normalize_split_comparison_pairs(pairs), start=1):
        normalized = normalize_split_pair_for_comparison(pair, index)
        rows.append(
            {
                t("split_selected"): normalized["_selected"],
                t("split_pair"): normalized["_pair_label"],
                t("split_selection_source"): _selection_source_label(
                    normalized.get("selection_source"),
                    t,
                ),
                t("split_corrected_f0_mean"): normalized["_F0"],
                t("split_corrected_f2_mean"): normalized["_F2"],
                t("split_energy_with_unit"): normalized["_energy"],
                t("split_temperature_plus_minus"): normalized["_temp"],
                t("split_pressure_plus_minus"): normalized["_press"],
            }
        )
    return rows


def _split_selection_widget_key(pair_id: str) -> str:
    """Return the Streamlit checkbox key for a Split comparison pair."""
    return f"split_final_pair_selected_{pair_id}"


def _reset_split_final_outputs() -> None:
    """Invalidate Split final outputs derived from comparison selection."""
    reset_split_final_outputs(st.session_state)


def _current_pairs() -> list[dict]:
    """Return session comparison pairs as a list and repair old selected flags."""
    return normalize_split_comparison_selection_state(st.session_state)


def get_selected_split_comparison_pairs() -> list[dict]:
    """Return selected corrected Split pairs from the current comparison table."""
    return selected_corrected_split_comparison_pairs(
        st.session_state.get("split_comparison_pairs") or []
    )


def _set_split_pair_selected_data_only(pair_id: str, selected: bool) -> None:
    """Synchronize one Split pair selection without touching widget state."""
    pairs = _current_pairs()
    selected_ids = []
    for pair in pairs:
        item_id = pair.get("id")
        if item_id == pair_id:
            item_selected = selected and is_split_pair_corrected(pair)
        else:
            item_selected = bool(pair.get("selected", False))
        if item_selected and item_id:
            selected_ids.append(item_id)

    st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
        pairs,
        selected_ids,
    )
    _reset_split_final_outputs()


def _clear_split_pair_widget_state(pair_ids) -> None:
    """Remove widget state for comparison pairs that left the table."""
    for pair_id in pair_ids:
        st.session_state.pop(_split_selection_widget_key(pair_id), None)


def _clear_all_split_comparison_pairs() -> None:
    """Clear only the Split final comparison table and derived outputs."""
    pairs = _current_pairs()
    _clear_split_pair_widget_state(pair.get("id") for pair in pairs if pair.get("id"))
    clear_split_comparison_state(st.session_state)
    st.session_state.split_comparison_pairs = clear_split_comparison_pairs()


def _remove_split_pair(pair_id: str) -> None:
    """Remove one Split comparison pair without touching parsed runs."""
    pairs = _current_pairs()
    st.session_state.split_comparison_pairs = remove_split_comparison_pair(
        pairs,
        pair_id,
    )
    _clear_split_pair_widget_state([pair_id])
    _reset_split_final_outputs()


def _render_actions(t) -> None:
    actions = st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        gap="small",
    )
    if actions.button(
        t("split_select_all_pairs"),
        icon=":material/select_all:",
        width="stretch",
    ):
        selected_ids = [
            pair["id"]
            for pair in _current_pairs()
            if pair.get("id") and is_split_pair_corrected(pair)
        ]
        st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
            _current_pairs(),
            selected_ids,
        )
        for pair in _current_pairs():
            st.session_state[_split_selection_widget_key(pair["id"])] = (
                pair.get("id") in selected_ids
            )
        _reset_split_final_outputs()
        st.rerun()

    if actions.button(
        t("split_deselect_all_pairs"),
        icon=":material/deselect:",
        width="stretch",
    ):
        st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
            _current_pairs(),
            [],
        )
        for pair in _current_pairs():
            st.session_state[_split_selection_widget_key(pair["id"])] = False
        _reset_split_final_outputs()
        st.rerun()

    if actions.button(
        t("split_clear_final_comparison"),
        icon=":material/delete_sweep:",
        width="stretch",
    ):
        _clear_all_split_comparison_pairs()
        st.rerun()


def _row_colors(
    visual_state: str = "unknown",
    *,
    selected: bool = False,
    reference: bool = False,
) -> tuple[str, str]:
    if reference:
        visual_state = "uncorrected"
    elif selected:
        visual_state = "selected_final"
    return {
        "manual": (DEFAULT_ROW_BG, DEFAULT_ROW_TEXT),
        "energy": (ENERGY_ROW_BG, ENERGY_ROW_TEXT),
        "target": (TARGET_ROW_BG, TARGET_ROW_TEXT),
        "energy_and_target": (ENERGY_TARGET_ROW_BG, ENERGY_TARGET_ROW_TEXT),
        "uncorrected": (REFERENCE_ROW_BG, REFERENCE_ROW_TEXT),
        "selected_final": (SELECTED_ROW_BG, SELECTED_ROW_TEXT),
        "unknown": (DEFAULT_ROW_BG, DEFAULT_ROW_TEXT),
    }.get(visual_state, (DEFAULT_ROW_BG, DEFAULT_ROW_TEXT))


def _cell_style(
    *,
    visual_state: str = "unknown",
    selected: bool = False,
    reference: bool = False,
    warning: bool = False,
    pair: bool = False,
) -> str:
    bg_color, text_color = _row_colors(
        visual_state,
        selected=selected,
        reference=reference,
    )
    font_size = (
        "calc(var(--mda-font-table) * 0.95)"
        if pair
        else "var(--mda-font-table)"
    )
    border = (
        "1px solid rgba(255,107,107,0.35)"
        if warning
        else "1px solid rgba(255,255,255,0.06)"
    )
    if warning:
        text_color = CV_WARNING_TEXT
    return (
        f"text-align:center;background-color:{bg_color};color:{text_color};"
        "padding:8px;border-radius:4px;"
        f"font-size:{font_size};border:{border};height:{TABLE_CELL_HEIGHT};"
        "width:100%;box-sizing:border-box;display:flex;"
        "align-items:center;justify-content:center;line-height:1.45;"
        f"font-weight:{'bold' if warning else 'normal'};"
    )


def _cell_html(
    value,
    *,
    warning: bool = False,
    visual_state: str = "unknown",
    pair: bool = False,
) -> str:
    cell = _cell_style(
        warning=warning,
        visual_state=visual_state,
        pair=pair,
    )
    escaped_value = html.escape(str(value)).replace("\n", "<br>")
    return f"<div style='{cell}'>{escaped_value}</div>"


def _stacked_display_value(value, precision: int) -> str:
    """Format ida/volta display values on separate visual lines."""
    return format_split_comparison_display_value(value, precision).replace(" / ", "\n")


def _render_header(labels: list[str], *, reference: bool = False) -> None:
    color = "#ffcf8a" if reference else "#ffffff"
    for column, header in zip(st.columns(ROW_RATIOS), labels):
        column.markdown(
            (
                "<div style='text-align:center;font-size:var(--mda-font-table);"
                f"color:{color};'>"
                f"<strong>{html.escape(str(header))}</strong></div>"
            ),
            unsafe_allow_html=True,
        )


def _render_legend(t) -> None:
    st.markdown(f"**{t('split_comparison_legend')}:**")
    legend = st.container(horizontal=True, gap="small")
    legend.badge(t("split_legend_manual_pair"), color="gray")
    legend.badge(t("split_legend_energy_pair"), color="green")
    legend.badge(t("split_legend_target_pair"), color="blue")
    legend.badge(t("split_legend_energy_target_pair"), color="violet")
    legend.badge(t("split_legend_uncorrected_pair"), color="orange")
    legend.badge(t("split_legend_cv_warning"), color="red")


def _render_remove_button(column, pair_id: str, label: str, t) -> None:
    if column.button(
        ":material/delete:",
        key=f"rem_split_{pair_id}",
        help=f"{t('split_remove_pair')}: {label}",
        width="stretch",
    ):
        _remove_split_pair(pair_id)
        st.rerun()


def _render_pair_row(pair: dict, normalized: dict, t) -> None:
    pair_id = normalized["_pair_id"]
    selected_key = _split_selection_widget_key(pair_id)
    previous = bool(pair.get("selected", False))
    if selected_key not in st.session_state:
        st.session_state[selected_key] = previous

    columns = st.columns(ROW_RATIOS, vertical_alignment="center")
    selected = columns[0].checkbox(
        t("split_selected"),
        key=selected_key,
        label_visibility="collapsed",
    )
    if selected != previous:
        _set_split_pair_selected_data_only(pair_id, selected)
    visual_state = get_pair_origin_visual_state(pair)

    values = [
        normalized["_pair_label"].replace(" | ", "\n"),
        _stacked_display_value(normalized["_temp"], 1),
        _stacked_display_value(normalized["_press"], 2),
        _stacked_display_value(normalized["_wind"], 2),
        format_split_comparison_display_value(normalized["_F0"], 2),
        format_split_comparison_display_value(normalized["_F2"], 4),
        format_split_comparison_display_value(normalized["_cv_F0"], 2),
        format_split_comparison_display_value(normalized["_cv_F2"], 2),
        format_split_comparison_display_value(normalized["_energy"], 4),
    ]
    warnings = [
        False,
        False,
        False,
        False,
        False,
        False,
        split_comparison_cv_warning(normalized["_cv_F0"]),
        split_comparison_cv_warning(normalized["_cv_F2"]),
        False,
    ]
    for index, (column, value, warning) in enumerate(
        zip(columns[1:10], values, warnings)
    ):
        column.markdown(
            _cell_html(
                value,
                warning=warning,
                visual_state=visual_state,
                pair=index == 0,
            ),
            unsafe_allow_html=True,
        )
    _render_remove_button(columns[10], pair_id, normalized["_pair_label"], t)


def _render_reference_row(pair: dict, normalized: dict, t) -> None:
    pair_id = normalized["_pair_id"]
    if pair.get("selected", False):
        _set_split_pair_selected_data_only(pair_id, False)
    st.session_state.pop(_split_selection_widget_key(pair_id), None)

    columns = st.columns(ROW_RATIOS, vertical_alignment="center")
    columns[0].markdown(
        _cell_html("⚠️", visual_state="uncorrected"),
        unsafe_allow_html=True,
    )
    values = [
        normalized["_pair_label"].replace(" | ", "\n"),
        _stacked_display_value(normalized["_temp"], 1),
        _stacked_display_value(normalized["_press"], 2),
        _stacked_display_value(normalized["_wind"], 2),
        format_split_comparison_display_value(normalized["_f0_prime"], 2),
        format_split_comparison_display_value(normalized["_f2_prime"], 4),
        format_split_comparison_display_value(normalized["_cv_f0_prime"], 2),
        format_split_comparison_display_value(normalized["_cv_f2_prime"], 2),
        format_split_comparison_display_value(normalized["_energy"], 4),
    ]
    warnings = [
        False,
        False,
        False,
        False,
        False,
        False,
        split_comparison_cv_warning(normalized["_cv_f0_prime"]),
        split_comparison_cv_warning(normalized["_cv_f2_prime"]),
        False,
    ]
    for index, (column, value, warning) in enumerate(
        zip(columns[1:10], values, warnings)
    ):
        column.markdown(
            _cell_html(
                value,
                warning=warning,
                visual_state="uncorrected",
                pair=index == 0,
            ),
            unsafe_allow_html=True,
        )
    _render_remove_button(columns[10], pair_id, normalized["_pair_label"], t)


def _render_corrected_pairs(pairs: list[tuple[dict, dict]], t) -> None:
    st.subheader(
        f":material/task_alt: {t('split_corrected_pairs_section')}"
    )
    if not pairs:
        st.info(t("split_no_corrected_pairs"), icon=":material/info:")
        return

    _render_header(
        [
            t("split_selected_short"),
            t("split_pair"),
            t("split_temp_short"),
            t("split_press_short"),
            t("split_wind_short"),
            "F0 [N]",
            "F2 [N/(km/h)²]",
            "CV F0 [%]",
            "CV F2 [%]",
            t("split_energy_with_unit"),
            "❌",
        ]
    )
    st.markdown(
        "<hr style='margin:4px 0;border-color:rgba(128,128,128,0.18);'>",
        unsafe_allow_html=True,
    )
    for pair, normalized in pairs:
        _render_pair_row(pair, normalized, t)
        st.markdown(
            "<hr style='margin:2px 0;border-color:rgba(128,128,128,0.18);'>",
            unsafe_allow_html=True,
        )


def _render_reference_pairs(pairs: list[tuple[dict, dict]], t) -> None:
    if not pairs:
        return

    st.subheader(
        f":material/science: {t('split_uncorrected_pairs_reference_section')}"
    )
    st.caption(t("split_uncorrected_pairs_reference_caption"))
    _render_header(
        [
            "-",
            t("split_pair"),
            t("split_temp_short"),
            t("split_press_short"),
            t("split_wind_short"),
            "f'0 (N)",
            "f'2 (N/(m/s)^2)",
            "CV f'0 (%)",
            "CV f'2 (%)",
            t("split_energy_with_unit"),
            "❌",
        ],
        reference=True,
    )
    st.markdown(
        "<hr style='margin:4px 0;border-color:rgba(245,158,11,0.28);'>",
        unsafe_allow_html=True,
    )
    for pair, normalized in pairs:
        _render_reference_row(pair, normalized, t)
        st.markdown(
            "<hr style='margin:2px 0;border-color:rgba(245,158,11,0.18);'>",
            unsafe_allow_html=True,
        )


def _metric_value(value, precision: int, suffix: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(number):
        return "N/A"
    return f"{number:.{precision}f}{suffix}"


def _render_final_results_action(t) -> None:
    if st.button(
        t("split_calculate_final_results"),
        type="primary",
        icon=":material/calculate:",
        width="stretch",
    ):
        stored_summary = consolidate_split_final_results(
            st.session_state.get("split_comparison_pairs") or []
        )
        if stored_summary.get("selected_pairs"):
            clear_split_final_results_compatibility(st.session_state)
            st.session_state.navigate_to_results = True
            st.rerun()
        else:
            st.warning(t("split_select_pairs_for_final_hint"))


def _diagnostic_status(status: str, t) -> str:
    icons = {
        "approved": "✅",
        "warning": "⚠️",
        "failed": "❌",
        "insufficient_data": "ℹ️",
    }
    return f"{icons.get(status, 'ℹ️')} {t(f'split_deviation_status_{status}')}"


def _render_table_tab(pairs: list[dict], t) -> None:
    """Render only persisted comparison data and selection controls."""
    if not pairs:
        st.info(t("split_comparison_empty"), icon=":material/info:")
        return

    normalized_pairs = [
        (pair, normalize_split_pair_for_comparison(pair, index))
        for index, pair in enumerate(pairs, start=1)
    ]
    corrected = [
        (pair, normalized)
        for pair, normalized in normalized_pairs
        if normalized["_is_corrected"]
    ]
    reference = [
        (pair, normalized)
        for pair, normalized in normalized_pairs
        if not normalized["_is_corrected"]
    ]

    with st.container(border=True):
        st.subheader(
            f":material/checklist: {t('split_comparison_pair_cards')}"
        )
        _render_actions(t)
        selection_status = st.empty()
        _render_legend(t)

    st.space("small")
    with st.container(border=True):
        _render_corrected_pairs(corrected, t)
    if reference:
        st.space("small")
        with st.container(border=True):
            _render_reference_pairs(reference, t)

    selected_count = sum(
        1 for pair in st.session_state.get("split_comparison_pairs", [])
        if pair.get("selected", False) and is_split_pair_corrected(pair)
    )
    selection_status.badge(
        t(
            "split_selected_pairs_count",
            selected=selected_count,
            total=len(st.session_state.get("split_comparison_pairs", [])),
        ),
        icon=":material/check_circle:",
        color="green" if selected_count else "gray",
    )

    if selected_count == 0:
        st.info(
            t("split_select_pairs_for_final_hint"),
            icon=":material/info:",
        )
        return
    _render_final_results_action(t)


def _render_deviation_analysis(t) -> None:
    selected_pairs = [
        pair
        for pair in st.session_state.get("split_comparison_pairs", [])
        if isinstance(pair, dict) and pair.get("selected") is True
    ]
    if not selected_pairs:
        st.warning(
            t("split_deviation_select_pairs_hint"),
            icon=":material/warning:",
        )
        return

    analysis, cache, _ = get_cached_split_deviation_analysis(
        selected_pairs,
        st.session_state.get("split_deviation_analysis_cache"),
    )
    st.session_state.split_deviation_analysis_cache = cache
    coefficients = analysis["coefficient_summary"]
    times = analysis["time_summary"]
    weather = analysis["weather_summary"]

    overview = st.container(horizontal=True, gap="small")
    overview.metric(
        t("split_deviation_selected_count"),
        analysis["pair_count"],
        border=True,
    )
    overview.metric(
        "CV F0",
        _metric_value(coefficients["cv_f0_pct"], 2, "%"),
        border=True,
    )
    overview.metric(
        "CV F2",
        _metric_value(coefficients["cv_f2_pct"], 2, "%"),
        border=True,
    )
    overview.metric(
        t("split_deviation_coefficients_status"),
        _diagnostic_status(coefficients["status"], t),
        border=True,
    )
    overview.metric(
        t("split_deviation_times_status"),
        _diagnostic_status(times["status"], t),
        border=True,
    )
    overview.metric(
        t("split_deviation_weather_status"),
        _diagnostic_status(weather["status"], t),
        border=True,
    )

    coefficient_section = st.container(border=True)
    coefficient_section.subheader(
        f":material/functions: {t('split_deviation_coefficients_title')}"
    )
    coefficient_rows = [
        {
            t("split_deviation_coefficient"): "F0",
            t("split_deviation_mean"): coefficients["mean_f0"],
            t("split_deviation_sample_stdev"): coefficients["stdev_f0"],
            "CV [%]": coefficients["cv_f0_pct"],
            t("split_deviation_limit"): coefficients["limit_pct"],
            t("split_deviation_status"): _diagnostic_status(coefficients["status"], t),
        },
        {
            t("split_deviation_coefficient"): "F2",
            t("split_deviation_mean"): coefficients["mean_f2"],
            t("split_deviation_sample_stdev"): coefficients["stdev_f2"],
            "CV [%]": coefficients["cv_f2_pct"],
            t("split_deviation_limit"): coefficients["limit_pct"],
            t("split_deviation_status"): _diagnostic_status(coefficients["status"], t),
        },
    ]
    coefficient_section.dataframe(
        pd.DataFrame(coefficient_rows),
        width="stretch",
        hide_index=True,
    )

    time_section = st.container(border=True)
    time_section.subheader(
        f":material/timer: {t('split_deviation_times_title')}"
    )
    high_reference, low_reference = get_split_reference_speeds(selected_pairs)
    time_rows = []
    for component, group in times["groups"].items():
        status = "insufficient_data" if group["passed"] is None else ("approved" if group["passed"] else "failed")
        time_rows.append({
            t("split_deviation_group"): format_split_time_group_label(
                component,
                high_reference_speed_kmh=high_reference,
                low_reference_speed_kmh=low_reference,
            ),
            "n": group["count"],
            t("split_deviation_mean_time"): group["mean"],
            t("split_deviation_sample_stdev"): group["stdev"],
            "C.V. Δt [%]": group["cv_pct"],
            t("split_deviation_limit"): times["cv_limit_pct"],
            t("split_deviation_status"): _diagnostic_status(status, t),
        })
    time_section.dataframe(
        pd.DataFrame(time_rows),
        width="stretch",
        hide_index=True,
    )
    opposite_rows = []
    for interval, result in times["opposite_direction"].items():
        status = "insufficient_data" if result["passed"] is None else ("approved" if result["passed"] else "failed")
        opposite_rows.append({
            t("split_deviation_speed"): format_split_opposite_time_label(
                interval,
                high_reference_speed_kmh=high_reference,
                low_reference_speed_kmh=low_reference,
            ),
            t("split_deviation_mean_plus"): result["mean_plus"],
            t("split_deviation_mean_minus"): result["mean_minus"],
            t("split_deviation_difference_pct"): result["diff_pct"],
            t("split_deviation_limit"): times["opposite_mean_limit_pct"],
            t("split_deviation_status"): _diagnostic_status(status, t),
        })
    time_section.dataframe(
        pd.DataFrame(opposite_rows),
        width="stretch",
        hide_index=True,
    )

    pair_section = st.container(border=True)
    pair_section.subheader(
        f":material/compare_arrows: {t('split_deviation_pairs_title')}"
    )
    deviation_rows = []
    for row in analysis["pair_deviations"]:
        deviation_rows.append({
            t("split_pair"): row["pair"], "F0": row["f0"],
            t("split_deviation_f0_abs"): row["f0_deviation_abs"],
            t("split_deviation_f0_pct"): row["f0_deviation_pct"], "F2": row["f2"],
            t("split_deviation_f2_abs"): row["f2_deviation_abs"],
            t("split_deviation_f2_pct"): row["f2_deviation_pct"],
            t("split_energy_with_unit"): row["energy"],
            t("split_deviation_alert"): "; ".join(row["alerts"]),
        })
    pair_section.dataframe(
        pd.DataFrame(deviation_rows),
        width="stretch",
        hide_index=True,
    )

    weather_section = st.container(border=True)
    weather_section.subheader(
        f":material/cloud: {t('split_deviation_weather_title')}"
    )
    weather_rows = [{
        t("split_pair"): row["pair"], t("split_temp_short"): row["temperature_c"],
        t("split_press_short"): row["pressure_kpa"], t("split_wind_short"): row["wind_speed_mps"],
        t("split_deviation_status"): _diagnostic_status(row["status"], t),
        t("split_deviation_alert"): "; ".join(row["alerts"]) or "-",
    } for row in weather["pairs"]]
    weather_section.dataframe(
        pd.DataFrame(weather_rows),
        width="stretch",
        hide_index=True,
    )
    weather_section.caption(t("split_deviation_weather_note"))

    leave_section = st.container(border=True)
    leave_section.subheader(
        f":material/troubleshoot: {t('split_deviation_leave_one_out_title')}"
    )
    if not analysis["leave_one_out"]:
        leave_section.info(
            t("split_deviation_leave_one_out_minimum"),
            icon=":material/info:",
        )
    else:
        leave_rows = []
        for row in analysis["leave_one_out"]:
            interpretations = []
            if row["largest_f0_improvement"]:
                interpretations.append(t("split_deviation_best_f0"))
            if row["largest_f2_improvement"]:
                interpretations.append(t("split_deviation_best_f2"))
            leave_rows.append({
                t("split_deviation_remove_pair"): row["pair"],
                "CV F0": f"{_metric_value(row['current_cv_f0_pct'], 2)} → {_metric_value(row['new_cv_f0_pct'], 2)}",
                "CV F2": f"{_metric_value(row['current_cv_f2_pct'], 2)} → {_metric_value(row['new_cv_f2_pct'], 2)}",
                t("split_deviation_interpretation"): "; ".join(interpretations) or t("split_deviation_diagnostic_only"),
            })
        leave_section.dataframe(
            pd.DataFrame(leave_rows),
            width="stretch",
            hide_index=True,
        )


def _render_selected_section(section: str, pairs: list[dict], t) -> None:
    """Render exactly one Final Comparison section per Streamlit run."""
    if section == "deviation":
        _render_deviation_analysis(t)
    else:
        _render_table_tab(pairs, t)


def render(t) -> None:
    """Render Final Comparison with conditional, lazy section execution."""
    st.header(
        f":material/compare: {t('page_split_final_comparison')}"
    )
    pairs = _current_pairs()
    labels = {
        t("split_final_comparison_tab_table"): "table",
        t("split_final_comparison_tab_deviation"): "deviation",
    }
    selector = st.container(border=True)
    selected_label = selector.radio(
        t("split_final_comparison_section"),
        options=list(labels),
        horizontal=True,
        key="split_final_comparison_section",
        label_visibility="collapsed",
    )
    _render_selected_section(labels[selected_label], pairs, t)

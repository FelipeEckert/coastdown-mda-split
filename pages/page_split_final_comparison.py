# coding: utf-8
"""Final comparison page for calculated Coastdown Split pairs."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from core.split_comparison import (
    clear_split_comparison_pairs,
    coefficient_variation_percent,
    force_uncorrected_split_pairs_unselected,
    format_split_comparison_display_value,
    is_split_pair_corrected,
    normalize_split_comparison_pairs,
    normalize_split_pair_for_comparison,
    remove_split_comparison_pair,
    selected_corrected_split_comparison_pairs,
    set_split_comparison_selected_ids,
    split_comparison_cv_warning,
)
from core.split_display import format_split_pair_label
from core.split_results import consolidate_split_final_results
from core.split_state import clear_split_comparison_state, reset_split_final_outputs


ROW_RATIOS = [0.5, 2.2, 0.9, 0.9, 1.0, 1.1, 1.1, 0.8, 0.8, 1.0, 0.5]


def _selection_source_label(source: str, t) -> str:
    if source == "manual":
        return t("split_selection_source_manual")
    if source == "algorithm":
        return t("split_selection_source_algorithm")
    return t("split_selection_source_unknown")


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
    pairs, changed = force_uncorrected_split_pairs_unselected(
        st.session_state.get("split_comparison_pairs") or []
    )
    if changed:
        st.session_state.split_comparison_pairs = pairs
        _reset_split_final_outputs()
    return pairs


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
    select_col, deselect_col, clear_col = st.columns(3)
    if select_col.button(
        t("split_select_all_pairs"),
        use_container_width=True,
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

    if deselect_col.button(
        t("split_deselect_all_pairs"),
        use_container_width=True,
    ):
        st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
            _current_pairs(),
            [],
        )
        for pair in _current_pairs():
            st.session_state[_split_selection_widget_key(pair["id"])] = False
        _reset_split_final_outputs()
        st.rerun()

    if clear_col.button(
        t("split_clear_final_comparison"),
        use_container_width=True,
    ):
        _clear_all_split_comparison_pairs()
        st.rerun()


def _cell_html(value, *, warning: bool = False, reference: bool = False) -> str:
    bg_color = "rgba(255,152,0,0.10)" if reference else "#1e1e1e"
    text_color = "#ffb74d" if reference else "white"
    cell = (
        f"text-align:center;background-color:{bg_color};color:{text_color};"
        "padding:8px;border-radius:4px;font-size:var(--mda-font-table);"
    )
    if warning:
        cell = (
            f"text-align:center;background-color:{bg_color};color:#ff6b6b;"
            "padding:8px;border-radius:4px;font-weight:bold;"
            "font-size:var(--mda-font-table);"
        )
    escaped_value = html.escape(str(value)).replace("\n", "<br>")
    return f"<div style='{cell}'>{escaped_value}</div>"


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


def _render_remove_button(column, pair_id: str, label: str, t) -> None:
    if column.button(
        "❌",
        key=f"rem_split_{pair_id}",
        help=f"{t('split_remove_pair')}: {label}",
        use_container_width=True,
    ):
        _remove_split_pair(pair_id)
        st.rerun()


def _render_pair_row(pair: dict, normalized: dict, t) -> None:
    pair_id = normalized["_pair_id"]
    selected_key = _split_selection_widget_key(pair_id)
    previous = bool(pair.get("selected", False))
    if selected_key not in st.session_state:
        st.session_state[selected_key] = previous

    columns = st.columns(ROW_RATIOS)
    selected = columns[0].checkbox(
        t("split_selected"),
        key=selected_key,
        label_visibility="collapsed",
    )
    if selected != previous:
        _set_split_pair_selected_data_only(pair_id, selected)

    values = [
        normalized["_pair_label"].replace(" | ", "\n"),
        format_split_comparison_display_value(normalized["_temp"], 1),
        format_split_comparison_display_value(normalized["_press"], 2),
        format_split_comparison_display_value(normalized["_wind"], 2),
        format_split_comparison_display_value(normalized["_F0"], 4),
        format_split_comparison_display_value(normalized["_F2"], 6),
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
    for column, value, warning in zip(columns[1:10], values, warnings):
        column.markdown(
            _cell_html(value, warning=warning),
            unsafe_allow_html=True,
        )
    _render_remove_button(columns[10], pair_id, normalized["_pair_label"], t)


def _render_reference_row(pair: dict, normalized: dict, t) -> None:
    pair_id = normalized["_pair_id"]
    if pair.get("selected", False):
        _set_split_pair_selected_data_only(pair_id, False)
    st.session_state.pop(_split_selection_widget_key(pair_id), None)

    columns = st.columns(ROW_RATIOS)
    columns[0].markdown(_cell_html("⚠️", reference=True), unsafe_allow_html=True)
    values = [
        normalized["_pair_label"].replace(" | ", "\n"),
        format_split_comparison_display_value(normalized["_temp"], 1),
        format_split_comparison_display_value(normalized["_press"], 2),
        format_split_comparison_display_value(normalized["_wind"], 2),
        format_split_comparison_display_value(normalized["_f0_prime"], 4),
        format_split_comparison_display_value(normalized["_f2_prime"], 6),
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
    for column, value, warning in zip(columns[1:10], values, warnings):
        column.markdown(
            _cell_html(value, warning=warning, reference=True),
            unsafe_allow_html=True,
        )
    _render_remove_button(columns[10], pair_id, normalized["_pair_label"], t)


def _render_corrected_pairs(pairs: list[tuple[dict, dict]], t) -> None:
    st.subheader(t("split_corrected_pairs_section"))
    if not pairs:
        st.info(t("split_no_corrected_pairs"))
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

    st.markdown("---")
    st.subheader(t("split_uncorrected_pairs_reference_section"))
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


def _cv_value(value, t) -> str:
    if value is None:
        return t("split_cv_not_applicable_single_pair")
    return _metric_value(value, 2, "%")


def _conformity_label(status: str, t) -> str:
    return t(f"split_results_status_{status}")


def _render_selected_pair_statistics(selected_pairs: list[dict], t) -> dict:
    """Render compact statistics using the same Split final-results helper."""
    summary = consolidate_split_final_results(selected_pairs)
    st.subheader(
        t(
            "split_selected_pair_statistics_title",
            count=summary.get("num_pairs", 0),
        )
    )

    count_col, f0_col, f2_col, energy_col = st.columns(4)
    count_col.metric(
        t("split_selected_pairs"),
        str(summary.get("num_pairs", 0)),
    )
    f0_col.metric(
        t("split_results_final_f0"),
        _metric_value(summary.get("mean_f0"), 4, " N"),
        delta=f"{t('split_results_cv_f0')}: {_cv_value(summary.get('cv_f0'), t)}",
    )
    f2_col.metric(
        t("split_results_final_f2"),
        _metric_value(summary.get("mean_f2"), 6, " N/(km/h)^2"),
        delta=f"{t('split_results_cv_f2')}: {_cv_value(summary.get('cv_f2'), t)}",
    )
    energy_col.metric(
        t("split_results_mean_energy"),
        _metric_value(summary.get("mean_energy"), 4, " MJ/km"),
        delta=(
            f"{t('split_results_cv_energy')}: "
            f"{_cv_value(summary.get('cv_energy'), t)}"
        ),
    )

    status_col, warning_col = st.columns(2)
    status_col.metric(
        t("split_results_conformity"),
        _conformity_label(summary.get("conformity_status"), t),
    )
    warning_col.metric(
        t("split_card_warnings"),
        str(len(summary.get("warnings") or [])),
    )
    return summary


def _traceability_rows(selected_pairs: list[dict], t) -> list[dict]:
    rows = []
    for pair in selected_pairs:
        warnings = list(pair.get("warnings") or [])
        ambient_by_component = pair.get("ambient_by_component") or {}
        for ambient in ambient_by_component.values():
            if isinstance(ambient, dict):
                warnings.extend(ambient.get("warnings") or [])
        warnings = list(dict.fromkeys(str(w) for w in warnings if str(w).strip()))
        rows.append(
            {
                t("split_pair"): format_split_pair_label(pair),
                "High+ / Low+": (
                    f"Run {pair.get('high_plus_run', 'N/A')} / "
                    f"Run {pair.get('low_plus_run', 'N/A')}"
                ),
                "High- / Low-": (
                    f"Run {pair.get('high_minus_run', 'N/A')} / "
                    f"Run {pair.get('low_minus_run', 'N/A')}"
                ),
                "Delta t high + / - (s)": (
                    f"{_metric_value(pair.get('high_plus_delta_t_s'), 3)} / "
                    f"{_metric_value(pair.get('high_minus_delta_t_s'), 3)}"
                ),
                "Delta t low + / - (s)": (
                    f"{_metric_value(pair.get('low_plus_delta_t_s'), 3)} / "
                    f"{_metric_value(pair.get('low_minus_delta_t_s'), 3)}"
                ),
                t("split_temperature_plus_minus"): (
                    f"{_metric_value(pair.get('temp_plus_used'), 1)} / "
                    f"{_metric_value(pair.get('temp_minus_used'), 1)}"
                ),
                t("split_pressure_plus_minus"): (
                    f"{_metric_value(pair.get('press_plus_used'), 2)} / "
                    f"{_metric_value(pair.get('press_minus_used'), 2)}"
                ),
                t("split_card_warnings"): "; ".join(warnings) or "N/A",
            }
        )
    return rows


def _render_selected_traceability(selected_pairs: list[dict], t) -> None:
    with st.expander(t("split_selected_pairs_traceability"), expanded=False):
        rows = _traceability_rows(selected_pairs, t)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(t("split_selected_pairs_traceability_empty"))


def _render_final_results_action(summary: dict, t) -> None:
    if st.button(
        t("split_calculate_final_results"),
        type="primary",
        use_container_width=True,
    ):
        stored_summary = consolidate_split_final_results(
            st.session_state.get("split_comparison_pairs") or []
        )
        if stored_summary.get("selected_pairs"):
            st.session_state.split_final_results = stored_summary
            st.session_state.navigate_to_results = True
            st.rerun()
        else:
            st.warning(t("split_select_pairs_for_final_hint"))


def render(t) -> None:
    """Render the Split final comparison table."""
    st.header(t("page_split_final_comparison"))
    pairs = _current_pairs()
    if not pairs:
        st.info(t("split_comparison_empty"))
        return

    for pair in pairs:
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

    _render_actions(t)
    st.markdown("---")
    st.subheader(t("split_final_comparison_table"))
    _render_corrected_pairs(corrected, t)
    _render_reference_pairs(reference, t)

    selected_count = sum(
        1 for pair in st.session_state.get("split_comparison_pairs", [])
        if pair.get("selected", False) and is_split_pair_corrected(pair)
    )
    st.caption(
        t(
            "split_selected_pairs_count",
            selected=selected_count,
            total=len(st.session_state.get("split_comparison_pairs", [])),
        )
    )

    st.markdown("---")
    selected_pairs = get_selected_split_comparison_pairs()
    if not selected_pairs:
        st.info(t("split_select_pairs_for_final_hint"))
        return

    summary = _render_selected_pair_statistics(selected_pairs, t)
    st.markdown("---")
    _render_selected_traceability(selected_pairs, t)
    _render_final_results_action(summary, t)

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
from core.split_deviation_analysis import analyze_split_selected_deviations
from core.split_display import format_split_pair_label
from core.split_results import consolidate_split_final_results
from core.split_state import (
    clear_split_comparison_state,
    ensure_split_comparison_pairs,
    reset_split_final_outputs,
)


ROW_RATIOS = [0.5, 2.2, 0.9, 0.9, 1.0, 1.1, 1.1, 0.8, 0.8, 1.0, 0.5]
SELECTED_ROW_BG = "#D1FFBD"
SELECTED_ROW_TEXT = "black"
DEFAULT_ROW_BG = "#1e1e1e"
DEFAULT_ROW_TEXT = "white"
ENERGY_ROW_BG = "#D1FFBD"
ENERGY_ROW_TEXT = "black"
TARGET_ROW_BG = "#ADD8E6"
TARGET_ROW_TEXT = "black"
ENERGY_TARGET_ROW_BG = "#D8C7FF"
ENERGY_TARGET_ROW_TEXT = "black"
REFERENCE_ROW_BG = "rgba(255,152,0,0.10)"
REFERENCE_ROW_TEXT = "#ffb74d"
CV_WARNING_TEXT = "#ff6b6b"
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
    ensure_split_comparison_pairs(st.session_state)
    pairs, changed = force_uncorrected_split_pairs_unselected(
        st.session_state.split_comparison_pairs
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


def _legend_badge(label: str, bg_color: str, text_color: str) -> str:
    return (
        f"<span style='background-color:{bg_color};padding:4px 12px;"
        f"border-radius:4px;color:{text_color};font-size:var(--mda-font-table);"
        "display:inline-block;text-align:center;'>"
        f"{html.escape(label)}</span>"
    )


def _render_legend(t) -> None:
    badges = [
        _legend_badge(t("split_legend_manual_pair"), DEFAULT_ROW_BG, DEFAULT_ROW_TEXT),
        _legend_badge(t("split_legend_energy_pair"), ENERGY_ROW_BG, ENERGY_ROW_TEXT),
        _legend_badge(t("split_legend_target_pair"), TARGET_ROW_BG, TARGET_ROW_TEXT),
        _legend_badge(
            t("split_legend_energy_target_pair"),
            ENERGY_TARGET_ROW_BG,
            ENERGY_TARGET_ROW_TEXT,
        ),
        _legend_badge(
            t("split_legend_uncorrected_pair"),
            "rgba(255,152,0,0.18)",
            REFERENCE_ROW_TEXT,
        ),
        _legend_badge(t("split_legend_cv_warning"), CV_WARNING_TEXT, "black"),
    ]
    st.markdown(
        f"**{t('split_comparison_legend')}:** "
        "<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;'>"
        + "".join(badges)
        + "</div>",
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


def _diagnostic_status(status: str, t) -> str:
    icons = {
        "approved": "✅",
        "warning": "⚠️",
        "failed": "❌",
        "insufficient_data": "ℹ️",
    }
    return f"{icons.get(status, 'ℹ️')} {t(f'split_deviation_status_{status}')}"


def _render_table_tab(pairs: list[dict], t) -> None:
    """Render the existing Final Comparison behavior inside its tab."""
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
    st.subheader(t("split_comparison_pair_cards"))
    _render_legend(t)
    st.markdown("---")
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


def _render_deviation_analysis(t) -> None:
    selected_pairs = [
        pair
        for pair in st.session_state.get("split_comparison_pairs", [])
        if isinstance(pair, dict) and pair.get("selected") is True
    ]
    if not selected_pairs:
        st.warning(t("split_deviation_select_pairs_hint"))
        return

    analysis = analyze_split_selected_deviations(selected_pairs)
    coefficients = analysis["coefficient_summary"]
    times = analysis["time_summary"]
    weather = analysis["weather_summary"]

    cards = st.columns(6)
    cards[0].metric(t("split_deviation_selected_count"), analysis["pair_count"])
    cards[1].metric("CV F0", _metric_value(coefficients["cv_f0_pct"], 2, "%"))
    cards[2].metric("CV F2", _metric_value(coefficients["cv_f2_pct"], 2, "%"))
    cards[3].metric(t("split_deviation_coefficients_status"), _diagnostic_status(coefficients["status"], t))
    cards[4].metric(t("split_deviation_times_status"), _diagnostic_status(times["status"], t))
    cards[5].metric(t("split_deviation_weather_status"), _diagnostic_status(weather["status"], t))

    st.subheader(t("split_deviation_coefficients_title"))
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
    st.dataframe(pd.DataFrame(coefficient_rows), use_container_width=True, hide_index=True)

    st.subheader(t("split_deviation_times_title"))
    group_labels = {"high_plus": "high [+]", "high_minus": "high [-]", "low_plus": "low [+]", "low_minus": "low [-]"}
    time_rows = []
    for component, group in times["groups"].items():
        status = "insufficient_data" if group["passed"] is None else ("approved" if group["passed"] else "failed")
        time_rows.append({
            t("split_deviation_group"): group_labels[component],
            "n": group["count"],
            t("split_deviation_mean_time"): group["mean"],
            t("split_deviation_sample_stdev"): group["stdev"],
            "CV deltaT [%]": group["cv_pct"],
            t("split_deviation_limit"): times["cv_limit_pct"],
            t("split_deviation_status"): _diagnostic_status(status, t),
        })
    st.dataframe(pd.DataFrame(time_rows), use_container_width=True, hide_index=True)
    opposite_rows = []
    for interval, result in times["opposite_direction"].items():
        status = "insufficient_data" if result["passed"] is None else ("approved" if result["passed"] else "failed")
        opposite_rows.append({
            t("split_deviation_speed"): interval,
            t("split_deviation_mean_plus"): result["mean_plus"],
            t("split_deviation_mean_minus"): result["mean_minus"],
            t("split_deviation_difference_pct"): result["diff_pct"],
            t("split_deviation_limit"): times["opposite_mean_limit_pct"],
            t("split_deviation_status"): _diagnostic_status(status, t),
        })
    st.dataframe(pd.DataFrame(opposite_rows), use_container_width=True, hide_index=True)

    st.subheader(t("split_deviation_pairs_title"))
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
    st.dataframe(pd.DataFrame(deviation_rows), use_container_width=True, hide_index=True)

    st.subheader(t("split_deviation_weather_title"))
    weather_rows = [{
        t("split_pair"): row["pair"], t("split_temp_short"): row["temperature_c"],
        t("split_press_short"): row["pressure_kpa"], t("split_wind_short"): row["wind_speed_mps"],
        t("split_deviation_status"): _diagnostic_status(row["status"], t),
        t("split_deviation_alert"): "; ".join(row["alerts"]) or "-",
    } for row in weather["pairs"]]
    st.dataframe(pd.DataFrame(weather_rows), use_container_width=True, hide_index=True)
    st.caption(t("split_deviation_weather_note"))

    st.subheader(t("split_deviation_leave_one_out_title"))
    if not analysis["leave_one_out"]:
        st.info(t("split_deviation_leave_one_out_minimum"))
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
        st.dataframe(pd.DataFrame(leave_rows), use_container_width=True, hide_index=True)


def render(t) -> None:
    """Render Final Comparison as table and deviation-analysis sub-tabs."""
    st.header(t("page_split_final_comparison"))
    pairs = _current_pairs()
    tab_table, tab_deviation = st.tabs([
        t("split_final_comparison_tab_table"),
        t("split_final_comparison_tab_deviation"),
    ])
    with tab_table:
        _render_table_tab(pairs, t)
    with tab_deviation:
        _render_deviation_analysis(t)

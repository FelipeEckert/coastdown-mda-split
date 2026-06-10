# coding: utf-8
"""Final comparison page for calculated Coastdown Split pairs."""

import pandas as pd
import streamlit as st

from core.split_comparison import (
    build_split_comparison_table_rows,
    clear_split_comparison_pairs,
    coefficient_variation_percent,
    remove_split_comparison_pair,
    set_split_comparison_selected_ids,
)
from core.split_display import format_split_pair_label
from pages.page_split_coefficient_calculation import (
    COMPONENT_LABEL_KEYS,
    _ambient_mode_label,
    _first_value,
    _fmt,
    _translated_weather_warning,
    _weather_sync_rows,
    _weather_sync_warnings,
)


ROW_RATIOS = [
    0.45,
    1.8,
    0.85,
    0.65,
    0.65,
    0.65,
    0.65,
    0.9,
    1.0,
    0.9,
    1.0,
    1.05,
    1.0,
    0.55,
]


def _selection_source_label(source: str, t) -> str:
    if source == "manual":
        return t("split_selection_source_manual")
    if source == "algorithm":
        return t("split_selection_source_algorithm")
    return t("split_selection_source_unknown")


def _comparison_status_label(status: str, warning_count: int, t) -> str:
    if status == "ready":
        return t("split_comparison_status_ready")
    if status == "warning":
        return t("split_comparison_status_warning", count=warning_count)
    return t("split_comparison_status_incomplete")


def _comparison_rows(pairs: list[dict], t) -> list[dict]:
    """Translate pure Split comparison rows for UI and tests."""
    rows = []
    for pair in build_split_comparison_table_rows(pairs):
        rows.append(
            {
                t("split_selected"): pair["selected"],
                t("split_pair"): format_split_pair_label(pair),
                t("split_selection_source"): _selection_source_label(
                    pair["selection_source"],
                    t,
                ),
                t("split_high_plus_run_short"): pair["high_plus_run"],
                t("split_low_plus_run_short"): pair["low_plus_run"],
                t("split_high_minus_run_short"): pair["high_minus_run"],
                t("split_low_minus_run_short"): pair["low_minus_run"],
                t("split_corrected_f0_mean"): pair["F0_mean"],
                t("split_corrected_f2_mean"): pair["F2_mean"],
                t("split_energy_with_unit"): pair["energy"],
                t("split_temperature_plus_minus"): (
                    f"{_fmt(pair.get('temp_plus_used'), 1)} / "
                    f"{_fmt(pair.get('temp_minus_used'), 1)}"
                ),
                t("split_pressure_plus_minus"): (
                    f"{_fmt(pair.get('press_plus_used'), 2)} / "
                    f"{_fmt(pair.get('press_minus_used'), 2)}"
                ),
                t("split_comparison_status"): _comparison_status_label(
                    pair["status"],
                    pair["warning_count"],
                    t,
                ),
            }
        )
    return rows


def _source_colors(source: str) -> tuple[str, str]:
    if source == "algorithm":
        return "#D1FFBD", "#17210f"
    if source == "manual":
        return "#ADD8E6", "#102a35"
    return "#E6E6E6", "#303030"


def _cell_html(value, background: str, color: str, warning=False) -> str:
    border = "border-left:4px solid #b42318;" if warning else ""
    return (
        f"<div style='text-align:center;background-color:{background};"
        f"color:{color};padding:7px 5px;border-radius:4px;"
        f"min-height:34px;font-size:var(--mda-font-table);{border}'>"
        f"{value}</div>"
    )


def _format_value(value, precision: int) -> str:
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return "N/A"


def _selection_widget_key(pair_id: str) -> str:
    return f"split_final_pair_selected_{pair_id}"


def _reset_final_outputs() -> None:
    st.session_state.split_final_results = {}
    st.session_state.excel_buffer = None


def _set_all_selected(selected: bool) -> None:
    pairs = st.session_state.get("split_comparison_pairs") or []
    selected_ids = [pair.get("id") for pair in pairs if selected and pair.get("id")]
    st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
        pairs,
        selected_ids,
    )
    for pair in pairs:
        pair_id = pair.get("id")
        if pair_id:
            st.session_state[_selection_widget_key(pair_id)] = selected
    _reset_final_outputs()


def _clear_comparison() -> None:
    for pair in st.session_state.get("split_comparison_pairs") or []:
        pair_id = pair.get("id")
        if pair_id:
            st.session_state.pop(_selection_widget_key(pair_id), None)
    st.session_state.split_comparison_pairs = clear_split_comparison_pairs()
    _reset_final_outputs()


def _remove_pair(pair_id: str) -> None:
    st.session_state.split_comparison_pairs = remove_split_comparison_pair(
        st.session_state.get("split_comparison_pairs") or [],
        pair_id,
    )
    st.session_state.pop(_selection_widget_key(pair_id), None)
    _reset_final_outputs()


def _render_actions(t) -> None:
    select_col, deselect_col, clear_col = st.columns(3)
    if select_col.button(
        t("split_select_all_pairs"),
        use_container_width=True,
    ):
        _set_all_selected(True)
        st.rerun()
    if deselect_col.button(
        t("split_deselect_all_pairs"),
        use_container_width=True,
    ):
        _set_all_selected(False)
        st.rerun()
    if clear_col.button(
        t("split_clear_final_comparison"),
        use_container_width=True,
    ):
        _clear_comparison()
        st.rerun()


def _render_legend(t) -> None:
    label_col, manual_col, algorithm_col, pending_col = st.columns(
        [0.65, 1.0, 1.0, 1.0]
    )
    label_col.markdown(f"**{t('split_comparison_legend')}**")
    manual_col.markdown(
        _cell_html(
            t("split_selection_source_manual"),
            "#ADD8E6",
            "#102a35",
        ),
        unsafe_allow_html=True,
    )
    algorithm_col.markdown(
        _cell_html(
            t("split_selection_source_algorithm"),
            "#D1FFBD",
            "#17210f",
        ),
        unsafe_allow_html=True,
    )
    pending_col.markdown(
        _cell_html(
            t("split_selection_source_unknown"),
            "#E6E6E6",
            "#303030",
        ),
        unsafe_allow_html=True,
    )


def _render_header(t) -> None:
    headers = [
        t("split_selected_short"),
        t("split_pair"),
        t("split_selection_source"),
        t("split_high_plus_run_short"),
        t("split_low_plus_run_short"),
        t("split_high_minus_run_short"),
        t("split_low_minus_run_short"),
        t("split_corrected_f0_mean"),
        t("split_corrected_f2_mean"),
        t("split_energy_with_unit"),
        t("split_temperature_plus_minus"),
        t("split_pressure_plus_minus"),
        t("split_comparison_status"),
        "",
    ]
    for column, header in zip(st.columns(ROW_RATIOS), headers):
        column.markdown(
            (
                "<div style='text-align:center;font-size:var(--mda-font-table);"
                "color:#ffffff;background:#20242c;padding:7px 4px;"
                f"border-radius:4px;min-height:34px;'><strong>{header}</strong></div>"
            ),
            unsafe_allow_html=True,
        )


def _render_pair_row(pair: dict, row: dict, t) -> None:
    pair_id = pair.get("id")
    source = row["selection_source"]
    background, color = _source_colors(source)
    warning = row["status"] == "warning"
    selected_key = _selection_widget_key(pair_id)
    previous = bool(pair.get("selected", True))
    if selected_key not in st.session_state:
        st.session_state[selected_key] = previous

    columns = st.columns(ROW_RATIOS)
    selected = columns[0].checkbox(
        t("split_selected"),
        key=selected_key,
        label_visibility="collapsed",
    )
    if selected != previous:
        selected_ids = [
            item.get("id")
            for item in st.session_state.get("split_comparison_pairs") or []
            if item.get("id") and (
                selected if item.get("id") == pair_id else item.get("selected", True)
            )
        ]
        st.session_state.split_comparison_pairs = set_split_comparison_selected_ids(
            st.session_state.get("split_comparison_pairs") or [],
            selected_ids,
        )
        _reset_final_outputs()

    values = [
        format_split_pair_label(pair).replace(" | ", "<br>"),
        _selection_source_label(source, t),
        row["high_plus_run"] if row["high_plus_run"] is not None else "N/A",
        row["low_plus_run"] if row["low_plus_run"] is not None else "N/A",
        row["high_minus_run"] if row["high_minus_run"] is not None else "N/A",
        row["low_minus_run"] if row["low_minus_run"] is not None else "N/A",
        _format_value(row["F0_mean"], 3),
        _format_value(row["F2_mean"], 6),
        _format_value(row["energy"], 4),
        (
            f"{_format_value(row['temp_plus_used'], 1)} / "
            f"{_format_value(row['temp_minus_used'], 1)}"
        ),
        (
            f"{_format_value(row['press_plus_used'], 2)} / "
            f"{_format_value(row['press_minus_used'], 2)}"
        ),
        _comparison_status_label(row["status"], row["warning_count"], t),
    ]
    for column, value in zip(columns[1:13], values):
        column.markdown(
            _cell_html(value, background, color, warning=warning),
            unsafe_allow_html=True,
        )
    if columns[13].button(
        t("split_remove_pair_short"),
        key=f"split_final_remove_{pair_id}",
        help=t("split_remove_pair"),
        use_container_width=True,
    ):
        _remove_pair(pair_id)
        st.rerun()


def _pair_component_rows(pair: dict, t) -> list[dict]:
    rows = []
    for component in ("high_plus", "low_plus", "high_minus", "low_minus"):
        rows.append(
            {
                t("split_meteo_component"): t(COMPONENT_LABEL_KEYS[component]),
                "File": pair.get(f"{component}_file"),
                "Run": pair.get(f"{component}_run"),
                "Direction": pair.get(f"{component}_direction"),
                "Timestamp": pair.get(f"{component}_timestamp"),
                "Delta t (s)": pair.get(f"{component}_delta_t_s"),
            }
        )
    return rows


def _render_pair_card(pair: dict, t, pair_number: int) -> None:
    source = _selection_source_label(
        pair.get("selection_source", "manual"),
        t,
    )
    label = (
        f"{t('split_pair')} {pair_number} | "
        f"{format_split_pair_label(pair)} | {source}"
    )
    with st.expander(label, expanded=False):
        ambient_col, coefficients_col, variation_col, energy_col = st.columns(4)
        with ambient_col:
            st.markdown(f"##### {t('split_card_ambient_conditions')}")
            st.write(
                f"{t('split_temp_plus_used')}: "
                f"{_fmt(pair.get('temp_plus_used'), 2)} C"
            )
            st.write(
                f"{t('split_temp_minus_used')}: "
                f"{_fmt(pair.get('temp_minus_used'), 2)} C"
            )
            st.write(
                f"{t('split_press_plus_used')}: "
                f"{_fmt(pair.get('press_plus_used'), 3)} kPa"
            )
            st.write(
                f"{t('split_press_minus_used')}: "
                f"{_fmt(pair.get('press_minus_used'), 3)} kPa"
            )
            st.caption(
                f"{t('split_ambient_mode_label')}: "
                f"{_ambient_mode_label(pair, t)}"
            )

        with coefficients_col:
            st.markdown(f"##### {t('split_corrected_coefficients')}")
            st.metric(
                "F0",
                f"{_fmt(_first_value(pair, 'F0_mean', 'F0'), 3)} N",
            )
            st.metric(
                "F2",
                f"{_fmt(_first_value(pair, 'F2_mean', 'F2'), 6)} N/(km/h)^2",
            )
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
            unit = pair.get("energy_unit") or "MJ/km"
            st.metric(
                t("split_card_energy"),
                (
                    f"{_fmt(pair.get('energy'), 4)} {unit}"
                    if pair.get("energy") is not None
                    else "N/A"
                ),
            )

        st.markdown(f"**{t('split_card_traceability')}**")
        st.dataframe(
            pd.DataFrame(_pair_component_rows(pair, t)),
            use_container_width=True,
            hide_index=True,
        )

        ambient_by_component = pair.get("ambient_by_component") or {}
        st.markdown(f"**{t('split_ambient_traceability')}**")
        st.dataframe(
            pd.DataFrame(_weather_sync_rows(ambient_by_component, t)),
            use_container_width=True,
            hide_index=True,
        )

        warnings = _weather_sync_warnings(ambient_by_component, t)
        warnings.extend(
            _translated_weather_warning(warning, t)
            for warning in (pair.get("warnings") or [])
        )
        warnings = list(dict.fromkeys(warnings))
        if warnings:
            with st.popover(t("split_card_warnings")):
                for warning in warnings:
                    st.warning(warning)


def render(t) -> None:
    """Render the Split final comparison table and pair details."""
    st.header(t("page_split_final_comparison"))
    pairs = st.session_state.get("split_comparison_pairs") or []
    if not pairs:
        st.info(t("split_comparison_empty"))
        return

    _render_actions(t)
    st.markdown("---")
    _render_legend(t)
    st.markdown("---")
    st.subheader(t("split_final_comparison_table"))
    _render_header(t)

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
    rows_by_id = {
        row["id"]: row
        for row in build_split_comparison_table_rows(pairs)
    }
    for pair in pairs:
        pair_id = pair.get("id")
        row = rows_by_id.get(pair_id)
        if row:
            _render_pair_row(pair, row, t)
            st.markdown(
                "<hr style='margin:2px 0;border-color:rgba(128,128,128,0.18);'>",
                unsafe_allow_html=True,
            )

    selected_count = sum(
        1 for pair in st.session_state.split_comparison_pairs
        if pair.get("selected", True)
    )
    st.caption(
        t(
            "split_selected_pairs_count",
            selected=selected_count,
            total=len(st.session_state.split_comparison_pairs),
        )
    )

    st.markdown("---")
    st.subheader(t("split_comparison_pair_cards"))
    for pair_number, pair in enumerate(
        st.session_state.split_comparison_pairs,
        start=1,
    ):
        _render_pair_card(pair, t, pair_number)

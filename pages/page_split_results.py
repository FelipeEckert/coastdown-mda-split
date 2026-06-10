# coding: utf-8
"""Final consolidated results for pairs selected in Split Final Comparison."""

import pandas as pd
import streamlit as st

from core.split_display import format_split_pair_label
from core.split_results import consolidate_split_final_results
from pages.page_split_coefficient_calculation import (
    COMPONENT_LABEL_KEYS,
    _translated_weather_warning,
    _weather_sync_rows,
    _weather_sync_warnings,
)


def _fmt(value, precision=3, suffix=""):
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}{suffix}"
    return "N/A"


def _cv_label(value, t) -> str:
    if value is None:
        return t("split_results_not_applicable")
    return f"{value:.2f}%"


def _selection_source_label(source: str, t) -> str:
    if source == "manual":
        return t("split_selection_source_manual")
    if source == "algorithm":
        return t("split_selection_source_algorithm")
    return t("split_selection_source_unknown")


def _conformity_label(status: str, t) -> str:
    return t(f"split_results_status_{status}")


def _result_rows(results: list[dict], t=None) -> list[dict]:
    """Build final table rows from normalized selected Split pairs."""
    rows = []
    for idx, result in enumerate(results, start=1):
        row = {
            "Index": idx,
            "Pair": format_split_pair_label(result),
            "Selection source": result.get("selection_source"),
            "F0 (N)": result.get("F0_mean"),
            "F2 (N/(km/h)^2)": result.get("F2_mean"),
            "Energy (MJ/km)": result.get("energy"),
            "f'0 (N)": result.get("f0_prime_mean"),
            "f'2 (N/(m/s)^2)": result.get("f2_prime_mean"),
            "Warnings": "; ".join(result.get("warnings") or []),
        }
        if t is not None:
            row = {
                t("split_results_index"): idx,
                t("split_pair"): format_split_pair_label(result),
                t("split_selection_source"): _selection_source_label(
                    result.get("selection_source"),
                    t,
                ),
                t("split_results_final_f0"): result.get("F0_mean"),
                t("split_results_final_f2"): result.get("F2_mean"),
                t("split_results_mean_energy"): result.get("energy"),
                t("split_results_uncorrected_f0"): result.get("f0_prime_mean"),
                t("split_results_uncorrected_f2"): result.get("f2_prime_mean"),
                t("split_card_warnings"): "; ".join(
                    result.get("warnings") or []
                ),
            }
        rows.append(row)
    return rows


def _component_rows(pair: dict, t) -> list[dict]:
    rows = []
    for component in ("high_plus", "low_plus", "high_minus", "low_minus"):
        record = pair.get(component) or {}
        rows.append(
            {
                t("split_meteo_component"): t(COMPONENT_LABEL_KEYS[component]),
                t("split_file"): (
                    record.get("filename")
                    or pair.get(f"{component}_file")
                    or "N/A"
                ),
                t("split_run"): (
                    record.get("run_id")
                    if record.get("run_id") is not None
                    else pair.get(f"{component}_run", "N/A")
                ),
                t("split_direction"): (
                    record.get("heading")
                    or record.get("direction")
                    or pair.get(f"{component}_direction")
                    or "N/A"
                ),
                t("split_timestamp"): (
                    record.get("start_time_str")
                    or record.get("start_timestamp")
                    or pair.get(f"{component}_timestamp")
                    or "N/A"
                ),
                t("split_results_deceleration_time"): (
                    record.get("delta_t_s")
                    if record.get("delta_t_s") is not None
                    else pair.get(f"{component}_delta_t_s")
                ),
                t("split_results_subintervals"): ", ".join(
                    record.get("subintervals") or []
                ),
            }
        )
    return rows


def _pair_status(pair: dict) -> str:
    if pair.get("F0_mean") is None or pair.get("F2_mean") is None:
        return "incomplete"
    if pair.get("warnings"):
        return "warning"
    return "ready"


def _render_summary(summary: dict, t) -> None:
    st.subheader(t("split_results_consolidated"))
    f0_col, f2_col, energy_col = st.columns(3)
    f0_col.metric(
        t("split_results_final_f0"),
        _fmt(summary.get("mean_f0"), 4, " N"),
        delta=f"{t('split_results_cv_f0')}: {_cv_label(summary.get('cv_f0'), t)}",
    )
    f2_col.metric(
        t("split_results_final_f2"),
        _fmt(summary.get("mean_f2"), 6, " N/(km/h)^2"),
        delta=f"{t('split_results_cv_f2')}: {_cv_label(summary.get('cv_f2'), t)}",
    )
    energy_col.metric(
        t("split_results_mean_energy"),
        _fmt(summary.get("mean_energy"), 4, " MJ/km"),
        delta=(
            f"{t('split_results_cv_energy')}: "
            f"{_cv_label(summary.get('cv_energy'), t)}"
        ),
    )

    pairs_col, status_col = st.columns(2)
    pairs_col.metric(
        t("split_selected_pairs"),
        str(summary.get("num_pairs", 0)),
    )
    status_col.metric(
        t("split_results_conformity"),
        _conformity_label(summary.get("conformity_status"), t),
    )


def _render_vehicle_info(summary: dict, t) -> None:
    st.markdown("---")
    st.subheader(t("vehicle_information"))
    vehicle_info = st.session_state.get("vehicle_info") or {}
    model_col, date_col, mass_col = st.columns(3)
    model_col.write(
        f"**{t('vehicle_model')}:** {vehicle_info.get('model') or 'N/A'}"
    )
    date_col.write(
        f"**{t('test_date')}:** {vehicle_info.get('test_date') or 'N/A'}"
    )
    mass_col.write(
        f"**{t('effective_mass')}:** "
        f"{_fmt(vehicle_info.get('effective_mass'), 1, ' kg')}"
    )
    st.caption(
        t(
            "split_results_selected_source_note",
            count=summary.get("num_pairs", 0),
        )
    )


def _render_validation(summary: dict, t) -> None:
    st.markdown("---")
    st.subheader(t("split_results_validation"))
    status = summary.get("conformity_status")
    status_text = _conformity_label(status, t)
    if status == "conforming":
        st.success(status_text)
    elif status in ("nonconforming", "incomplete"):
        st.warning(status_text)
    else:
        st.info(status_text)

    selected_count = summary.get("num_pairs", 0)
    if summary.get("missing_f0_count") or summary.get("missing_f2_count"):
        st.warning(
            t(
                "split_results_missing_corrected",
                f0=summary.get("missing_f0_count", 0),
                f2=summary.get("missing_f2_count", 0),
                total=selected_count,
            )
        )
    if summary.get("missing_energy_count"):
        st.warning(
            t(
                "split_results_missing_energy",
                missing=summary.get("missing_energy_count", 0),
                total=selected_count,
            )
        )
    if summary.get("warnings"):
        st.warning(
            t(
                "split_results_warning_count",
                count=len(summary["warnings"]),
            )
        )


def _render_pair_details(pair: dict, pair_number: int, t) -> None:
    source = _selection_source_label(pair.get("selection_source"), t)
    label = (
        f"{t('split_pair')} {pair_number} | "
        f"{format_split_pair_label(pair)} | {source} | "
        f"{_conformity_label(_pair_status(pair), t)}"
    )
    with st.expander(label, expanded=False):
        corrected_col, raw_col, energy_col = st.columns(3)
        corrected_col.markdown(f"**{t('split_corrected_coefficients')}**")
        corrected_col.write(
            f"F0: {_fmt(pair.get('F0_mean'), 4, ' N')}"
        )
        corrected_col.write(
            f"F2: {_fmt(pair.get('F2_mean'), 6, ' N/(km/h)^2')}"
        )
        raw_col.markdown(f"**{t('split_uncorrected_results')}**")
        raw_col.write(
            f"f'0: {_fmt(pair.get('f0_prime_mean'), 4, ' N')}"
        )
        raw_col.write(
            f"f'2: {_fmt(pair.get('f2_prime_mean'), 6, ' N/(m/s)^2')}"
        )
        energy_col.markdown(f"**{t('split_card_energy')}**")
        energy_col.write(
            _fmt(
                pair.get("energy"),
                4,
                f" {pair.get('energy_unit') or 'MJ/km'}",
            )
        )

        st.markdown(f"**{t('split_card_traceability')}**")
        st.dataframe(
            pd.DataFrame(_component_rows(pair, t)),
            use_container_width=True,
            hide_index=True,
        )

        ambient = pair.get("ambient_by_component") or {}
        if ambient:
            st.markdown(f"**{t('split_ambient_traceability')}**")
            st.dataframe(
                pd.DataFrame(_weather_sync_rows(ambient, t)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(t("split_results_no_ambient_traceability"))

        warnings = _weather_sync_warnings(ambient, t)
        warnings.extend(
            _translated_weather_warning(warning, t)
            for warning in (pair.get("warnings") or [])
        )
        warnings = list(dict.fromkeys(warnings))
        if warnings:
            st.markdown(f"**{t('split_card_warnings')}**")
            for warning in warnings:
                st.warning(warning)


def render(t) -> None:
    """Render results selected in the Split Final Comparison."""
    st.header(t("page_split_results"))
    comparison_pairs = st.session_state.get("split_comparison_pairs") or []
    if not comparison_pairs:
        st.session_state.split_final_results = {}
        st.info(t("split_results_no_pairs_available"))
        return

    summary = consolidate_split_final_results(comparison_pairs)
    if not summary["selected_pairs"]:
        st.session_state.split_final_results = {}
        st.warning(t("split_results_no_pairs_selected"))
        return

    summary["vehicle_info"] = dict(
        st.session_state.get("vehicle_info") or {}
    )
    st.session_state.split_final_results = summary

    _render_summary(summary, t)
    _render_vehicle_info(summary, t)
    _render_validation(summary, t)

    st.markdown("---")
    st.subheader(t("split_results_final_table"))
    st.dataframe(
        pd.DataFrame(_result_rows(summary["selected_pairs"], t)),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader(t("split_results_pair_details"))
    for pair_number, pair in enumerate(summary["selected_pairs"], start=1):
        _render_pair_details(pair, pair_number, t)

    st.markdown("---")
    st.subheader(t("split_results_export"))
    st.button(
        t("split_results_export_button"),
        disabled=True,
        use_container_width=True,
    )
    st.info(t("split_results_export_pending"))

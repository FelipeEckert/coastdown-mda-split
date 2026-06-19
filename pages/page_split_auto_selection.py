# coding: utf-8
"""Controlled Streamlit integration for exact automatic Split pair selection."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from core.split_auto_selection import run_split_auto_selection_exact
from core.split_candidate_generation import (
    estimate_full_candidate_count,
    split_runs_by_role_and_heading,
)
from core.split_comparison import coefficient_variation_percent
from core.split_comparison_merge import (
    merge_algorithm_candidates_into_comparison_pairs,
)
from core.split_display import format_split_pair_label
from core.split_state import reset_split_final_outputs, split_parse_is_current


ALGORITHM_VALUES = {
    "energy": "split_auto_algorithm_energy",
    "target": "split_auto_algorithm_target",
}
GROUP_LABELS = {
    "high_plus": "split_high_plus_records_available",
    "low_plus": "split_low_plus_records_available",
    "high_minus": "split_high_minus_records_available",
    "low_minus": "split_low_minus_records_available",
}


def _finite_float(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _vehicle_data() -> dict | None:
    vehicle_info = dict(st.session_state.get("vehicle_info") or {})
    effective_mass = _finite_float(
        vehicle_info.get("effective_mass") or st.session_state.get("total_mass")
    )
    if effective_mass is None or effective_mass <= 0:
        return None
    vehicle_info["effective_mass"] = effective_mass
    return {
        "effective_mass": effective_mass,
        "total_mass": st.session_state.get("total_mass"),
        "vehicle_info": vehicle_info,
    }


def _correction_context(t) -> dict | None:
    ambient_mode = st.session_state.get("split_ambient_mode", "fixed")
    if ambient_mode != "fixed":
        st.warning(t("split_auto_weather_sync_not_supported"))
        return None

    temperature = _finite_float(
        st.session_state.get("split_fixed_temperature", 20.0)
    )
    pressure = _finite_float(
        st.session_state.get("split_fixed_pressure", 101.325)
    )
    if temperature is None or pressure is None or pressure <= 0:
        st.warning(t("split_auto_fixed_conditions_invalid"))
        return None
    return {
        "temperature_c": temperature,
        "pressure_kpa": pressure,
        "split_interval_config": (
            st.session_state.get("split_interval_config") or {}
        ),
    }


def _format_number(value, decimals: int = 2) -> str:
    number = _finite_float(value)
    if number is None:
        return "N/A"
    return f"{number:.{decimals}f}"


def _candidate_rows(candidates: list[dict], algorithm: str, t) -> list[dict]:
    rows = []
    for candidate in candidates or []:
        row = {
            t("split_pair"): format_split_pair_label(candidate),
            "F0": _finite_float(candidate.get("F0_mean")),
            "F2": _finite_float(candidate.get("F2_mean")),
            t("split_energy_with_unit"): _finite_float(candidate.get("energy")),
            "CV F0 [%]": coefficient_variation_percent(
                candidate.get("F0_plus"),
                candidate.get("F0_minus"),
            ),
            "CV F2 [%]": coefficient_variation_percent(
                candidate.get("F2_plus"),
                candidate.get("F2_minus"),
            ),
        }
        if algorithm == "target":
            row[t("split_auto_target_score")] = _finite_float(
                candidate.get("target_score")
            )
        rows.append(row)
    return rows


def _time_status_label(passed, t) -> str:
    if passed is True:
        return t("split_auto_time_status_passed")
    if passed is False:
        return t("split_auto_time_status_failed")
    return t("split_auto_time_status_inconclusive")


def _render_time_validation(time_validation: dict | None, t) -> None:
    if not isinstance(time_validation, dict):
        return
    with st.expander(t("split_auto_time_diagnostic"), expanded=False):
        st.write(
            f"**{t('split_auto_time_overall_status')}:** "
            f"{_time_status_label(time_validation.get('passed'), t)}"
        )
        groups = time_validation.get("groups") or {}
        opposite = time_validation.get("opposite_direction") or {}
        rows = [
            {
                t("split_auto_time_check"): "CV high+",
                t("split_auto_time_value"): _format_number(
                    (groups.get("high_plus") or {}).get("cv_pct")
                ),
            },
            {
                t("split_auto_time_check"): "CV high-",
                t("split_auto_time_value"): _format_number(
                    (groups.get("high_minus") or {}).get("cv_pct")
                ),
            },
            {
                t("split_auto_time_check"): "CV low+",
                t("split_auto_time_value"): _format_number(
                    (groups.get("low_plus") or {}).get("cv_pct")
                ),
            },
            {
                t("split_auto_time_check"): "CV low-",
                t("split_auto_time_value"): _format_number(
                    (groups.get("low_minus") or {}).get("cv_pct")
                ),
            },
            {
                t("split_auto_time_check"): t("split_auto_high_direction_difference"),
                t("split_auto_time_value"): _format_number(
                    (opposite.get("high") or {}).get("diff_pct")
                ),
            },
            {
                t("split_auto_time_check"): t("split_auto_low_direction_difference"),
                t("split_auto_time_value"): _format_number(
                    (opposite.get("low") or {}).get("diff_pct")
                ),
            },
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        warnings = time_validation.get("warnings") or []
        if warnings:
            st.warning("\n".join(str(warning) for warning in warnings))


def _render_execution_result(result: dict, t) -> None:
    metadata = result.get("metadata") or {}
    merge_metadata = result.get("merge_metadata") or {}
    candidates = result.get("candidates") or []
    algorithm = metadata.get("algorithm") or result.get("algorithm") or "energy"

    st.success(t("split_auto_completed"))
    first_row = st.columns(4)
    first_row[0].metric(
        t("split_auto_generated_count"),
        str(metadata.get("generated_count", 0)),
    )
    first_row[1].metric(
        t("split_auto_ranked_count"),
        str(metadata.get("ranked_count", 0)),
    )
    first_row[2].metric(
        t("split_auto_suggested_count"),
        str(metadata.get("selected_count", 0)),
    )
    first_row[3].metric(
        t("split_auto_added_count"),
        str(merge_metadata.get("added_count", 0)),
    )

    selection_metadata = metadata.get("selection") or {}
    second_row = st.columns(4)
    second_row[0].metric(
        t("split_auto_duplicates_count"),
        str(merge_metadata.get("duplicate_count", 0)),
    )
    second_row[1].metric(
        t("split_auto_repeated_skipped"),
        str(selection_metadata.get("skipped_repeated_count", 0)),
    )
    second_row[2].metric(t("split_auto_mode"), str(metadata.get("mode", "exact")))
    second_row[3].metric(
        t("split_auto_algorithm"),
        t(ALGORITHM_VALUES.get(algorithm, "split_auto_algorithm_energy")),
    )

    warnings = []
    warnings.extend(metadata.get("warnings") or [])
    warnings.extend(merge_metadata.get("warnings") or [])
    warnings = list(dict.fromkeys(str(warning) for warning in warnings))
    if warnings:
        st.warning("\n".join(warnings))

    if candidates:
        st.subheader(t("split_auto_suggested_candidates"))
        st.dataframe(
            pd.DataFrame(_candidate_rows(candidates, algorithm, t)),
            width="stretch",
            hide_index=True,
        )
    _render_time_validation(metadata.get("time_validation"), t)
    if merge_metadata.get("added_count", 0) or merge_metadata.get(
        "updated_existing_count", 0
    ):
        st.info(t("split_auto_comparison_guidance"))


def _persist_last_result(result: dict) -> None:
    st.session_state.split_auto_selection_last_result = result
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_last_result"] = result


def render(t) -> None:
    """Render exact automatic selection without changing final user selection."""
    st.subheader(t("split_auto_title"))
    st.write(t("split_auto_description"))

    if not st.session_state.get("data_loaded"):
        st.info(t("split_auto_process_intervals_first"))
        return
    if not split_parse_is_current(st.session_state):
        st.warning(t("split_parse_dirty_calculation_blocked"))
        return

    parsed_runs = st.session_state.get("split_parsed_runs") or {}
    grouped = split_runs_by_role_and_heading(parsed_runs)
    estimated_total = estimate_full_candidate_count(grouped)
    metric_columns = st.columns(5)
    for column, group_key in zip(metric_columns[:4], GROUP_LABELS):
        column.metric(t(GROUP_LABELS[group_key]), str(len(grouped[group_key])))
    metric_columns[4].metric(
        t("split_auto_estimated_combinations"),
        f"{estimated_total:,}",
    )

    if grouped.get("warnings"):
        with st.expander(t("split_auto_grouping_warnings"), expanded=False):
            st.warning("\n".join(str(warning) for warning in grouped["warnings"]))
    if estimated_total == 0:
        st.warning(t("split_auto_no_complete_combinations"))

    vehicle_data = _vehicle_data()
    if vehicle_data is None:
        st.warning(t("split_effective_mass_required_for_calculation"))

    st.markdown("---")
    st.subheader(t("split_auto_settings"))
    algorithm_labels = {
        t("split_auto_algorithm_energy"): "energy",
        t("split_auto_algorithm_target"): "target",
    }
    algorithm_label = st.radio(
        t("split_auto_algorithm"),
        options=list(algorithm_labels),
        horizontal=True,
        key="split_auto_algorithm_selector",
    )
    algorithm = algorithm_labels[algorithm_label]

    settings_columns = st.columns(3)
    k = int(
        settings_columns[0].number_input(
            t("split_auto_k"),
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            key="split_auto_k",
        )
    )
    max_combinations = int(
        settings_columns[1].number_input(
            t("split_auto_max_combinations"),
            min_value=100,
            max_value=1_000_000,
            value=200_000,
            step=10_000,
            key="split_auto_max_combinations",
        )
    )
    avoid_repeated_runs = settings_columns[2].checkbox(
        t("split_auto_avoid_repeated"),
        value=True,
        key="split_auto_avoid_repeated",
    )
    settings_columns[2].caption(t("split_auto_avoid_repeated_help"))

    target_f0 = None
    target_f2 = None
    if algorithm == "target":
        target_columns = st.columns(2)
        target_f0 = target_columns[0].number_input(
            t("split_auto_target_f0"),
            min_value=0.000001,
            value=100.0,
            format="%.6f",
            key="split_auto_target_f0",
        )
        target_f2 = target_columns[1].number_input(
            t("split_auto_target_f2"),
            min_value=0.000001,
            value=0.004,
            format="%.8f",
            key="split_auto_target_f2",
        )

    exceeds_limit = estimated_total > max_combinations
    if exceeds_limit:
        st.warning(t("split_auto_exact_limit_exceeded"))

    correction_context = _correction_context(t)
    can_execute = (
        estimated_total > 0
        and not exceeds_limit
        and vehicle_data is not None
        and correction_context is not None
    )

    if st.button(
        t("split_auto_run"),
        type="primary",
        width="stretch",
        disabled=not can_execute,
    ):
        progress = st.progress(0.0)

        def progress_callback(value):
            progress.progress(min(max(float(value), 0.0), 1.0))

        try:
            with st.spinner(t("split_auto_running")):
                candidates, metadata = run_split_auto_selection_exact(
                    parsed_runs,
                    vehicle_data=vehicle_data,
                    correction_context=correction_context,
                    algorithm=algorithm,
                    k=k,
                    target_f0=target_f0,
                    target_f2=target_f2,
                    avoid_repeated_runs=avoid_repeated_runs,
                    max_combinations=max_combinations,
                    progress_callback=progress_callback,
                )
        except ValueError as exc:
            progress.empty()
            st.error(str(exc))
        else:
            progress.progress(1.0)
            if not candidates:
                result = {
                    "algorithm": algorithm,
                    "metadata": metadata,
                    "merge_metadata": {},
                    "candidates": [],
                }
                _persist_last_result(result)
                st.warning(t("split_auto_no_candidates_returned"))
            else:
                updated_pairs, merge_metadata = (
                    merge_algorithm_candidates_into_comparison_pairs(
                        st.session_state.get("split_comparison_pairs") or [],
                        candidates,
                        algorithm_source=algorithm,
                    )
                )
                st.session_state.split_comparison_pairs = updated_pairs
                reset_split_final_outputs(st.session_state)
                result = {
                    "algorithm": algorithm,
                    "metadata": metadata,
                    "merge_metadata": merge_metadata,
                    "candidates": candidates,
                }
                _persist_last_result(result)

    last_result = st.session_state.get("split_auto_selection_last_result")
    if isinstance(last_result, dict):
        st.markdown("---")
        _render_execution_result(last_result, t)

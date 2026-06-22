# coding: utf-8
"""Controlled Streamlit integration for exact automatic Split pair selection."""

from __future__ import annotations

from copy import deepcopy
import math

import pandas as pd
import streamlit as st

from core.split_auto_selection import (
    find_replacement_candidate,
    replace_pending_candidate,
    run_split_auto_selection_exact,
)
from core.split_candidate_generation import (
    estimate_full_candidate_count,
    split_runs_by_role_and_heading,
)
from core.split_comparison import coefficient_variation_percent
from core.split_comparison_merge import (
    merge_algorithm_candidates_into_comparison_pairs,
)
from core.split_display import format_split_pair_label
from core.split_pair_candidate import split_candidate_signature
from core.split_state import (
    ensure_split_comparison_pairs,
    reset_split_final_outputs,
    split_parse_is_current,
)
from core.split_time_validation import split_candidate_component_time
from core.split_weather_context import synchronize_weather_for_split_runs


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


def _correction_context(t, ambient_mode: str) -> dict | None:
    if ambient_mode == "weather_sync":
        if not st.session_state.get("weather_data"):
            st.warning(t("split_auto_weather_required"))
            return None
        return {
            "ambient_mode": "weather_sync",
            "split_interval_config": st.session_state.get("split_interval_config") or {},
        }

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
        "ambient_mode": "fixed",
        "temperature_c": temperature,
        "pressure_kpa": pressure,
        "split_interval_config": (
            st.session_state.get("split_interval_config") or {}
        ),
    }


def _render_weather_candidate_summary(candidate: dict, t) -> None:
    summary = candidate.get("weather_summary") or {}
    if not summary:
        return
    columns = st.columns(4)
    columns[0].metric(t("split_auto_weather_temp_mean"), _format_number(summary.get("temperature_c_mean"), 1))
    columns[1].metric(t("split_auto_weather_pressure_mean"), _format_number(summary.get("pressure_kpa_mean"), 2))
    columns[2].metric(t("split_auto_weather_wind_max"), _format_number(summary.get("wind_speed_mps_max"), 2))
    columns[3].metric(t("split_auto_weather_status"), str(summary.get("status", "N/A")))
    if summary.get("warnings"):
        with st.expander(t("split_auto_weather_details"), expanded=False):
            st.warning("\n".join(str(item) for item in summary["warnings"]))


def _format_number(value, decimals: int = 2) -> str:
    number = _finite_float(value)
    if number is None:
        return "N/A"
    return f"{number:.{decimals}f}"


def _format_candidate_display_value(value, decimals: int | None = None) -> str:
    """Format one candidate-table value without mutating the source candidate."""
    if value is None:
        return "-"
    try:
        if bool(pd.isna(value)):
            return "-"
    except (TypeError, ValueError):
        pass
    if (
        isinstance(value, str)
        and value.strip().lower() in {"", "nan", "n/a", "none"}
    ):
        return "-"
    if decimals is None:
        number = _finite_float(value)
        if number is None:
            return str(value)
        return str(int(number)) if number.is_integer() else str(number)
    number = _finite_float(value)
    return "-" if number is None else f"{number:.{decimals}f}"


def _candidate_run_time_label(candidate: dict, component: str) -> str:
    """Format one run and Delta t for candidate display only."""
    run_value = candidate.get(f"{component}_run")
    if run_value is None:
        record = candidate.get(component)
        if isinstance(record, dict):
            run_value = record.get("run_id")
    run_label = _format_candidate_display_value(run_value)
    delta_t = split_candidate_component_time(candidate, component)
    delta_t_label = _format_candidate_display_value(delta_t, 2)
    if delta_t_label == "-":
        return f"Run {run_label} | dt = -"
    return f"Run {run_label} | dt = {delta_t_label} s"


def _candidate_direction_weather(candidate: dict, suffix: str) -> tuple[float | None, str]:
    components = candidate.get("weather_components") or {}
    selected = [components.get(f"high_{suffix}") or {}, components.get(f"low_{suffix}") or {}]
    winds = [_finite_float(item.get("wind_speed_mps", item.get("wind_speed"))) for item in selected]
    valid_winds = [value for value in winds if value is not None]
    warnings = []
    for item in selected:
        warnings.extend(item.get("invalid_reasons") or [])
    return (
        sum(valid_winds) / len(valid_winds) if valid_winds else None,
        " | ".join(dict.fromkeys(warnings)) or "-",
    )


def _candidate_rows(candidates: list[dict], algorithm: str, t) -> list[dict]:
    rows = []
    for candidate in candidates or []:
        pair_label = format_split_pair_label(candidate)
        directional_rows = (
            (t("split_auto_outbound"), "plus"),
            (t("split_auto_return"), "minus"),
            (t("split_auto_average"), "mean"),
        )
        for section_label, suffix in directional_rows:
            is_average = suffix == "mean"
            wind, weather_alerts = (
                (None, "-") if is_average else _candidate_direction_weather(candidate, suffix)
            )
            rows.append(
                {
                    t("split_pair"): pair_label,
                    t("split_auto_section"): section_label,
                    t("split_auto_high_run"): (
                        None if is_average else _candidate_run_time_label(
                            candidate,
                            f"high_{suffix}",
                        )
                    ),
                    t("split_auto_low_run"): (
                        None if is_average else _candidate_run_time_label(
                            candidate,
                            f"low_{suffix}",
                        )
                    ),
                    "F0 [N]": _finite_float(candidate.get(f"F0_{suffix}")),
                    "F2 [N/(km/h)^2]": _finite_float(candidate.get(f"F2_{suffix}")),
                    "CV F0 [%]": (
                        coefficient_variation_percent(
                            candidate.get("F0_plus"), candidate.get("F0_minus")
                        ) if is_average else None
                    ),
                    "CV F2 [%]": (
                        coefficient_variation_percent(
                            candidate.get("F2_plus"), candidate.get("F2_minus")
                        ) if is_average else None
                    ),
                    t("split_auto_temperature"): (
                        None if is_average else _finite_float(
                            candidate.get(f"temp_{suffix}_used")
                        )
                    ),
                    t("split_auto_pressure"): (
                        None if is_average else _finite_float(
                            candidate.get(f"press_{suffix}_used")
                        )
                    ),
                    t("split_auto_wind"): wind,
                    t("split_auto_weather_alerts"): (
                        " | ".join((candidate.get("weather_summary") or {}).get("warnings") or [])
                        if is_average else weather_alerts
                    ),
                    t("split_auto_target_score"): (
                        _finite_float(candidate.get("target_score"))
                        if is_average and algorithm == "target" else None
                    ),
                    t("split_energy_with_unit"): (
                        _finite_float(candidate.get("energy")) if is_average else None
                    ),
                    "_is_average": is_average,
                }
            )
    return rows


def _candidate_table(candidate: dict, algorithm: str, t):
    rows = _candidate_rows([candidate], algorithm, t)
    dataframe = pd.DataFrame(rows)
    average_flags = dataframe.pop("_is_average")
    dataframe = dataframe.drop(columns=[t("split_pair")])
    run_columns = [t("split_auto_high_run"), t("split_auto_low_run")]
    for column in run_columns:
        dataframe[column] = dataframe[column].map(_format_candidate_display_value)
    numeric_formats = {
        "F0 [N]": 4,
        "F2 [N/(km/h)^2]": 6,
        "CV F0 [%]": 2,
        "CV F2 [%]": 2,
        t("split_auto_temperature"): 1,
        t("split_auto_pressure"): 2,
        t("split_auto_wind"): 2,
        t("split_auto_target_score"): 6,
        t("split_energy_with_unit"): 4,
    }
    for column, decimals in numeric_formats.items():
        dataframe[column] = dataframe[column].map(
            lambda value, precision=decimals: _format_candidate_display_value(
                value,
                precision,
            )
        )

    def highlight_average(row):
        if bool(average_flags.loc[row.name]):
            return [
                "background-color: rgba(209,255,189,0.18); font-weight: bold"
            ] * len(row)
        return [""] * len(row)

    return dataframe.style.apply(highlight_average, axis=1)


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


def _store_pending_selection(pending: dict) -> None:
    st.session_state.split_auto_selection_pending = pending
    st.session_state.split_auto_selection_last_result = pending
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_pending"] = pending
        tests[active_test_id]["split_auto_selection_last_result"] = pending


def _set_replace_request(
    replace_index: int,
    old_candidate: dict,
    new_candidate: dict,
    metadata: dict,
) -> None:
    request = {
        "index": replace_index,
        "old_candidate": deepcopy(old_candidate),
        "new_candidate": deepcopy(new_candidate),
        "old_signature": split_candidate_signature(old_candidate),
        "new_signature": split_candidate_signature(new_candidate),
        "metadata": deepcopy(metadata),
    }
    st.session_state.split_auto_replace_request = request
    st.session_state.split_auto_replace_dialog_open = True


def _clear_replace_request() -> None:
    st.session_state.split_auto_replace_request = None
    st.session_state.split_auto_replace_dialog_open = False


def _replace_dialog_state_is_valid(
    pending,
    request,
    dialog_open,
) -> bool:
    """Return whether a replacement dialog has a live, actionable request."""
    if not isinstance(pending, dict) or not pending.get("candidates"):
        return False
    if not isinstance(request, dict) or not request:
        return False
    if dialog_open is not True:
        return False
    if isinstance(pending.get("merge_metadata"), dict):
        return False
    return pending.get("pool_strategy") == "balanced_v2"


def _sanitize_replace_dialog_state(pending=None) -> bool:
    current_pending = (
        st.session_state.get("split_auto_selection_pending")
        if pending is None
        else pending
    )
    valid = _replace_dialog_state_is_valid(
        current_pending,
        st.session_state.get("split_auto_replace_request"),
        st.session_state.get("split_auto_replace_dialog_open"),
    )
    if not valid:
        _clear_replace_request()
    return valid


def _preview_pending_suggestion(replace_index: int) -> bool:
    pending = dict(st.session_state.get("split_auto_selection_pending") or {})
    candidates = pending.get("candidates") or []
    replacement, replacement_metadata = find_replacement_candidate(
        candidates,
        pending.get("ranked_pool") or [],
        replace_index,
        avoid_repeated_runs=bool(pending.get("avoid_repeated_runs", True)),
    )
    if replacement is None:
        replacement_metadata["replaced"] = False
        pending["replacement_feedback"] = replacement_metadata
        _store_pending_selection(pending)
        _clear_replace_request()
        return False
    _set_replace_request(
        replace_index,
        candidates[replace_index],
        replacement,
        replacement_metadata,
    )
    return True


def _confirm_pending_replacement() -> bool:
    request = dict(st.session_state.get("split_auto_replace_request") or {})
    pending = dict(st.session_state.get("split_auto_selection_pending") or {})
    replace_index = request.get("index")
    candidates = pending.get("candidates") or []
    if not isinstance(replace_index, int) or replace_index >= len(candidates):
        _clear_replace_request()
        return False
    if split_candidate_signature(candidates[replace_index]) != request.get(
        "old_signature"
    ):
        _clear_replace_request()
        return False

    candidates, replacement_metadata = replace_pending_candidate(
        pending.get("candidates") or [],
        [request.get("new_candidate")],
        replace_index,
        avoid_repeated_runs=bool(pending.get("avoid_repeated_runs", True)),
    )
    inserted_signature = (
        split_candidate_signature(candidates[replace_index])
        if replacement_metadata.get("replaced")
        else None
    )
    if inserted_signature != request.get("new_signature"):
        _clear_replace_request()
        return False
    pending["candidates"] = candidates
    pending["replacement_feedback"] = replacement_metadata
    pending["replacement_history"] = list(pending.get("replacement_history") or []) + [
        replacement_metadata
    ]
    pending["merge_metadata"] = None
    _store_pending_selection(pending)
    _clear_replace_request()
    return True


def _replace_dialog_content(t) -> None:
    request = st.session_state.get("split_auto_replace_request") or {}
    old_candidate = request.get("old_candidate")
    new_candidate = request.get("new_candidate")
    if not isinstance(old_candidate, dict) or not isinstance(new_candidate, dict):
        st.error(t("split_auto_replace_request_invalid"))
        return

    pending = st.session_state.get("split_auto_selection_pending") or {}
    algorithm = pending.get("algorithm") or "energy"
    st.write(t("split_auto_replace_modal_description"))
    st.markdown(f"### {t('split_auto_replace_current_pair')}")
    st.markdown(f"**{format_split_pair_label(old_candidate)}**")
    st.dataframe(
        _candidate_table(old_candidate, algorithm, t),
        width="stretch",
        hide_index=True,
    )
    st.markdown(f"### {t('split_auto_replace_next_pair')}")
    st.markdown(f"**{format_split_pair_label(new_candidate)}**")
    st.dataframe(
        _candidate_table(new_candidate, algorithm, t),
        width="stretch",
        hide_index=True,
    )

    confirm_column, cancel_column = st.columns(2)
    if confirm_column.button(
        t("split_auto_replace_confirm"),
        type="primary",
        width="stretch",
        key="split_auto_dialog_confirm",
    ):
        if not _confirm_pending_replacement():
            st.session_state.split_auto_replace_error = True
        st.rerun()
    if cancel_column.button(
        t("cancel"),
        width="stretch",
        key="split_auto_dialog_cancel",
    ):
        _clear_replace_request()
        st.rerun()


if hasattr(st, "dialog"):
    _render_replace_dialog = st.dialog(
        "\U0001F501 Confirmar substitui\u00e7\u00e3o de sugest\u00e3o",
        width="large",
        on_dismiss=_clear_replace_request,
    )(_replace_dialog_content)
else:
    def _render_replace_dialog(t) -> None:
        st.error(t("split_auto_dialog_not_supported"))
        _clear_replace_request()


def _merge_pending_suggestions() -> None:
    pending = dict(st.session_state.get("split_auto_selection_pending") or {})
    candidates = pending.get("candidates") or []
    algorithm = pending.get("algorithm") or "energy"
    updated_pairs, merge_metadata = merge_algorithm_candidates_into_comparison_pairs(
        st.session_state.split_comparison_pairs,
        candidates,
        algorithm_source=algorithm,
    )
    st.session_state.split_comparison_pairs = updated_pairs
    reset_split_final_outputs(st.session_state)
    pending["merge_metadata"] = merge_metadata
    _store_pending_selection(pending)
    _clear_replace_request()


def _clear_pending_suggestions() -> None:
    st.session_state.split_auto_selection_pending = None
    _clear_replace_request()
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_pending"] = None


def _render_merge_feedback(merge_metadata: dict, t) -> None:
    st.success(
        t(
            "split_auto_merge_completed",
            added=merge_metadata.get("added_count", 0),
            duplicates=merge_metadata.get("duplicate_count", 0),
            updated=merge_metadata.get("updated_existing_count", 0),
            preserved=merge_metadata.get("preserved_selected_count", 0),
        )
    )
    st.info(t("split_auto_comparison_guidance"))


def _render_execution_result(pending: dict, t) -> None:
    metadata = pending.get("metadata") or {}
    merge_metadata = pending.get("merge_metadata")
    candidates = pending.get("candidates") or []
    algorithm = metadata.get("algorithm") or pending.get("algorithm") or "energy"

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
    first_row[3].metric(t("split_auto_mode"), str(metadata.get("mode", "exact")))

    selection_metadata = metadata.get("selection") or {}
    second_row = st.columns(3)
    second_row[0].metric(
        t("split_auto_repeated_skipped"),
        str(selection_metadata.get("skipped_repeated_count", 0)),
    )
    second_row[1].metric(
        t("split_auto_algorithm"),
        t(ALGORITHM_VALUES.get(algorithm, "split_auto_algorithm_energy")),
    )
    second_row[2].metric(
        t("split_auto_replacement_pool_count"),
        str(len(pending.get("ranked_pool") or [])),
    )

    warnings = []
    warnings.extend(metadata.get("warnings") or [])
    if isinstance(merge_metadata, dict):
        warnings.extend(merge_metadata.get("warnings") or [])
    warnings = list(dict.fromkeys(str(warning) for warning in warnings))
    if warnings:
        st.warning("\n".join(warnings))

    if candidates:
        st.subheader(t("split_auto_suggested_candidates"))
        st.caption(t("split_auto_pending_review_help"))
        replacement_feedback = pending.get("replacement_feedback") or {}
        if replacement_feedback.get("replaced"):
            st.success(t("split_auto_replacement_succeeded"))
        elif replacement_feedback.get("warnings"):
            st.warning(
                t(
                    "split_auto_replacement_unavailable_diagnostic",
                    pool_size=replacement_feedback.get("pool_size", 0),
                    checked=replacement_feedback.get("checked_pool_count", 0),
                    old=replacement_feedback.get("skipped_old_candidate_count", 0),
                    existing=replacement_feedback.get("skipped_existing_count", 0),
                    repeated=replacement_feedback.get("skipped_repeated_count", 0),
                )
            )

        suggestions_merged = isinstance(merge_metadata, dict)
        pool_is_current = pending.get("pool_strategy") == "balanced_v2"
        if not pool_is_current:
            st.warning(t("split_auto_pending_pool_outdated"))
        dialog_state_valid = _sanitize_replace_dialog_state(pending)
        replace_request = st.session_state.get("split_auto_replace_request") or {}
        if st.session_state.pop("split_auto_replace_error", False):
            st.warning(t("split_auto_replace_preview_changed"))
        if dialog_state_valid and replace_request:
            _render_replace_dialog(t)
        for index, candidate in enumerate(candidates):
            with st.container(border=True):
                title_column, action_column = st.columns([0.78, 0.22])
                title_column.markdown(f"### {format_split_pair_label(candidate)}")
                if action_column.button(
                    t("split_auto_replace"),
                    key=f"split_auto_replace_{index}",
                    help=t("split_auto_replace_help"),
                    width="stretch",
                    disabled=suggestions_merged or not pool_is_current,
                ):
                    _preview_pending_suggestion(index)
                    st.rerun()
                _render_weather_candidate_summary(candidate, t)
                st.dataframe(
                    _candidate_table(candidate, algorithm, t),
                    width="stretch",
                    hide_index=True,
                )
        add_column, clear_column = st.columns([0.72, 0.28])
        if add_column.button(
            t("split_auto_add_pending_to_comparison"),
            type="primary",
            width="stretch",
            disabled=suggestions_merged,
        ):
            _merge_pending_suggestions()
            st.rerun()
        if clear_column.button(
            t("split_auto_clear_pending"),
            width="stretch",
        ):
            _clear_pending_suggestions()
            st.rerun()
    _render_time_validation(metadata.get("time_validation"), t)
    if isinstance(merge_metadata, dict):
        _render_merge_feedback(merge_metadata, t)


def render(t) -> None:
    """Render exact automatic selection without changing final user selection."""
    st.subheader(t("split_auto_title"))
    st.write(t("split_auto_description"))
    ensure_split_comparison_pairs(st.session_state)
    _sanitize_replace_dialog_state(
        st.session_state.get("split_auto_selection_pending")
    )

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

    st.markdown(f"#### {t('split_auto_environment_section')}")
    ambient_options = {
        t("split_ambient_mode_fixed"): "fixed",
        t("split_ambient_mode_weather_sync"): "weather_sync",
    }
    ambient_label = st.radio(
        t("split_ambient_mode_label"),
        options=list(ambient_options),
        horizontal=True,
        key="split_auto_ambient_mode_selector",
    )
    ambient_mode = ambient_options[ambient_label]
    exclude_invalid_weather = False
    parsed_runs_for_selection = parsed_runs
    weather_metadata = None
    if ambient_mode == "weather_sync":
        weather_columns = st.columns(2)
        max_time_diff_s = float(weather_columns[0].number_input(
            t("split_auto_weather_sync_limit"), min_value=0.0, value=300.0, step=30.0,
            key="split_auto_weather_sync_limit_s",
        ))
        exclude_invalid_weather = weather_columns[1].checkbox(
            t("split_auto_exclude_invalid_weather"), value=True,
            key="split_auto_exclude_invalid_weather",
        )
        weather_data = st.session_state.get("weather_data")
        if weather_data:
            parsed_runs_for_selection, weather_metadata = synchronize_weather_for_split_runs(
                parsed_runs, weather_data, max_time_diff_s=max_time_diff_s,
            )
            metrics = st.columns(6)
            values = (
                ("split_auto_weather_high_synced", weather_metadata["high_synchronized"]),
                ("split_auto_weather_low_synced", weather_metadata["low_synchronized"]),
                ("split_auto_weather_missing", weather_metadata["missing_count"]),
                ("split_auto_weather_wind_invalid", weather_metadata["wind_above_limit_count"]),
                ("split_auto_weather_temp_invalid", weather_metadata["temperature_above_limit_count"]),
                ("split_auto_weather_max_delta", _format_number(weather_metadata["max_time_diff_s_found"], 1)),
            )
            for column, (label_key, value) in zip(metrics, values):
                column.metric(t(label_key), str(value))
        else:
            st.warning(t("split_auto_weather_required"))

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

    correction_context = _correction_context(t, ambient_mode)
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
                    parsed_runs_for_selection,
                    vehicle_data=vehicle_data,
                    correction_context=correction_context,
                    algorithm=algorithm,
                    k=k,
                    target_f0=target_f0,
                    target_f2=target_f2,
                    avoid_repeated_runs=avoid_repeated_runs,
                    max_combinations=max_combinations,
                    replacement_pool_size=max(100, k * 10, k + 50),
                    progress_callback=progress_callback,
                    exclude_invalid_weather=exclude_invalid_weather,
                )
        except ValueError as exc:
            progress.empty()
            st.error(str(exc))
        else:
            progress.progress(1.0)
            ranked_pool = list(metadata.pop("replacement_pool", []))
            pending = {
                "algorithm": algorithm,
                "candidates": candidates,
                "ranked_pool": ranked_pool,
                "metadata": metadata,
                "avoid_repeated_runs": avoid_repeated_runs,
                "target_f0": target_f0,
                "target_f2": target_f2,
                "replacement_history": [],
                "replacement_feedback": None,
                "merge_metadata": None,
                "pool_strategy": "balanced_v2",
                "ambient_mode": ambient_mode,
                "weather_metadata": weather_metadata,
            }
            _store_pending_selection(pending)
            _clear_replace_request()
            if not candidates:
                st.warning(t("split_auto_no_candidates_returned"))

    pending = st.session_state.get("split_auto_selection_pending")
    if isinstance(pending, dict):
        st.markdown("---")
        _render_execution_result(pending, t)

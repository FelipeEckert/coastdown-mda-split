# coding: utf-8
"""Controlled Streamlit integration for exact automatic Split pair selection."""

from __future__ import annotations

from copy import deepcopy
import math

import pandas as pd
import streamlit as st

from core.split_auto_selection import (
    evaluate_split_constraint_satisfaction,
    find_replacement_candidate,
    normalize_split_time_constraints,
    replace_pending_candidate,
    run_split_auto_selection_exact,
    validate_split_candidate_set,
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
from core.split_weather_context import (
    build_fixed_split_correction_context,
    synchronize_weather_for_split_runs,
)
from core.split_vehicle_mass import normalize_split_vehicle_mass_data


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
    mass_data = normalize_split_vehicle_mass_data({
        "vehicle_info": vehicle_info,
        "total_mass": st.session_state.get("total_mass"),
    })
    effective_mass = _finite_float(mass_data["effective_mass_kg"])
    if effective_mass is None or effective_mass <= 0:
        return None
    vehicle_info.update(mass_data)
    vehicle_info["effective_mass"] = effective_mass
    return {
        **mass_data,
        "effective_mass": effective_mass,
        "vehicle_info": vehicle_info,
    }


def _correction_context(
    t,
    ambient_mode: str,
    fixed_temperature_c=None,
    fixed_pressure_kpa=None,
) -> dict | None:
    if ambient_mode == "weather_sync":
        if not st.session_state.get("weather_data"):
            st.warning(t("split_auto_weather_required"))
            return None
        return {
            "ambient_mode": "weather_sync",
            "split_interval_config": st.session_state.get("split_interval_config") or {},
        }

    try:
        return build_fixed_split_correction_context(
            fixed_temperature_c,
            fixed_pressure_kpa,
            split_interval_config=st.session_state.get("split_interval_config") or {},
        )
    except ValueError:
        st.warning(t("split_auto_fixed_conditions_invalid"))
        return None


def _render_weather_candidate_summary(candidate: dict, t) -> None:
    summary = candidate.get("weather_summary") or {}
    if not summary:
        return
    columns = st.columns(4)
    is_fixed = summary.get("mode") == "fixed"
    if is_fixed:
        metrics = (
            ("split_auto_environment", t("split_ambient_mode_fixed_short")),
            ("split_auto_weather_temp_mean", _format_candidate_display_value(summary.get("temperature_c_mean"), 1)),
            ("split_auto_weather_pressure_mean", _format_candidate_display_value(summary.get("pressure_kpa_mean"), 2)),
            ("split_auto_fixed_wind", "-"),
        )
    else:
        metrics = (
            ("split_auto_weather_temp_mean", _format_candidate_display_value(summary.get("temperature_c_mean"), 1)),
            ("split_auto_weather_pressure_mean", _format_candidate_display_value(summary.get("pressure_kpa_mean"), 2)),
            ("split_auto_weather_wind_max", _format_candidate_display_value(summary.get("wind_speed_mps_max"), 2)),
            ("split_auto_weather_status", str(summary.get("status") or "-")),
        )
    for column, (label_key, value) in zip(columns, metrics):
        column.metric(t(label_key), value)
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
                    t("split_auto_cv_f0_diagnostic"): (
                        coefficient_variation_percent(
                            candidate.get("F0_plus"), candidate.get("F0_minus")
                        ) if is_average else None
                    ),
                    t("split_auto_cv_f2_diagnostic"): (
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
        t("split_auto_cv_f0_diagnostic"): 2,
        t("split_auto_cv_f2_diagnostic"): 2,
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


def _constraints_active(constraints_enabled: dict | None) -> bool:
    return any(normalize_split_time_constraints(constraints_enabled).values())


def _default_constraint_search_pool_size(k: int) -> int:
    return max(120, int(k) * 30, int(k) + 60)


def _search_diagnostic_values(metadata: dict | None) -> dict | None:
    source = metadata if isinstance(metadata, dict) else {}
    selection = source.get("selection") or source
    if selection.get("strategy") != "constraint_first_v2":
        return None
    return {
        "strategy": selection.get("strategy"),
        "evaluated_sets_count": selection.get("evaluated_sets_count", 0),
        "valid_sets_found": selection.get("valid_sets_found", 0),
        "search_pool_size": selection.get("search_pool_size", 0),
        "max_set_evaluations_reached": bool(
            selection.get("max_set_evaluations_reached", False)
        ),
        "elapsed_seconds": selection.get("elapsed_seconds", 0.0),
        "max_search_seconds": selection.get("max_search_seconds", 0.0),
        "timeout_reached": bool(selection.get("timeout_reached", False)),
    }


def _render_search_diagnostics(metadata: dict | None, t) -> None:
    diagnostic = _search_diagnostic_values(metadata)
    if diagnostic is None:
        return
    metrics = (
        ("split_auto_search_evaluated_sets", diagnostic["evaluated_sets_count"]),
        ("split_auto_search_valid_sets", diagnostic["valid_sets_found"]),
        ("split_auto_search_pool", diagnostic["search_pool_size"]),
        (
            "split_auto_search_strategy",
            t("split_auto_search_strategy_constraint_first"),
        ),
        (
            "split_auto_search_elapsed_seconds",
            _format_number(diagnostic["elapsed_seconds"], 2),
        ),
        (
            "split_auto_search_time_limit",
            _format_number(diagnostic["max_search_seconds"], 1),
        ),
        (
            "split_auto_search_timeout_status",
            (
                t("split_auto_yes")
                if diagnostic["timeout_reached"]
                else t("split_auto_no")
            ),
        ),
        (
            "split_auto_search_evaluation_limit_status",
            (
                t("split_auto_yes")
                if diagnostic["max_set_evaluations_reached"]
                else t("split_auto_no")
            ),
        ),
    )
    for start in range(0, len(metrics), 4):
        columns = st.columns(4)
        for column, (label_key, value) in zip(columns, metrics[start:start + 4]):
            column.metric(t(label_key), str(value))
    if (
        diagnostic["max_set_evaluations_reached"]
        or diagnostic["timeout_reached"]
    ):
        st.warning(t("split_auto_search_limited_warning"))


def _render_generation_diagnostics(generation_metadata: dict | None, t) -> None:
    if not isinstance(generation_metadata, dict):
        return
    st.markdown(f"**{t('split_auto_diagnostics_generation')}**")
    columns = st.columns(2)
    columns[0].metric(
        t("split_auto_generated_count"),
        str(generation_metadata.get("generated_count", 0)),
    )
    columns[1].metric(
        t("split_auto_diagnostics_failed_count"),
        str(generation_metadata.get("failed_count", 0)),
    )
    prefilter_applied = bool(generation_metadata.get("prefilter_applied"))
    st.write(
        f"**{t('split_auto_diagnostics_prefilter')}:** "
        + (
            t("split_auto_diagnostics_prefilter_enabled")
            if prefilter_applied
            else t("split_auto_diagnostics_prefilter_disabled")
        )
    )
    prefilter = generation_metadata.get("prefilter") or {}
    if prefilter_applied and prefilter:
        rows = [
            {
                t("split_auto_prefilter_group"): t(GROUP_LABELS[group_key]),
                t("split_auto_prefilter_input"): (prefilter.get(group_key) or {}).get(
                    "input_count", 0
                ),
                t("split_auto_prefilter_output"): (prefilter.get(group_key) or {}).get(
                    "output_count", 0
                ),
                t("split_auto_prefilter_filtered"): (prefilter.get(group_key) or {}).get(
                    "filtered_count", 0
                ),
            }
            for group_key in GROUP_LABELS
            if group_key in prefilter
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _render_selection_diagnostics(metadata: dict | None, t) -> None:
    source = metadata if isinstance(metadata, dict) else {}
    with st.expander(t("split_auto_diagnostics_title"), expanded=False):
        _render_generation_diagnostics(source.get("generation"), t)
        st.markdown(f"**{t('split_auto_diagnostics_search')}**")
        if _search_diagnostic_values(source) is None:
            st.caption(t("split_auto_diagnostics_search_not_applicable"))
        else:
            _render_search_diagnostics(source, t)


def _constraint_status_label(status, t) -> str:
    if status is True:
        return t("split_auto_constraints_status_approved")
    if status is False:
        return t("split_auto_constraints_status_failed")
    return t("split_auto_constraints_status_inconclusive")


def _constraint_warning_messages(validation: dict | None, warnings=None) -> list[str]:
    messages = [str(item) for item in warnings or [] if str(item).strip()]
    if isinstance(validation, dict):
        messages.extend(
            str(item)
            for item in validation.get("warnings") or []
            if str(item).strip()
        )
        messages.extend(
            f"Failed check: {item}"
            for item in validation.get("failed_checks") or []
        )
    return list(dict.fromkeys(messages))


def _build_selection_state(
    *,
    algorithm: str,
    candidates: list[dict],
    ranked_pool: list[dict],
    metadata: dict,
    avoid_repeated_runs: bool,
    target_f0,
    target_f2,
    ambient_mode: str,
    weather_metadata,
) -> tuple[dict | None, dict | None]:
    """Build either a reviewable pending set or an explicit fallback offer."""
    constraints_enabled = normalize_split_time_constraints(
        metadata.get("constraints_enabled")
    )
    constraint_validation = metadata.get("constraint_validation")
    common = {
        "algorithm": algorithm,
        "candidates": list(candidates or []),
        "ranked_pool": list(ranked_pool or []),
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
        "constraints_enabled": constraints_enabled,
        "constraints_satisfied": metadata.get("constraints_satisfied"),
        "constraint_validation": constraint_validation,
        "fallback_used": False,
        "constraint_warnings": _constraint_warning_messages(
            constraint_validation,
            metadata.get("constraint_warnings"),
        ),
    }
    fallback_candidates = list(
        ((metadata.get("selection") or {}).get("fallback_candidates")) or []
    )
    if _constraints_active(constraints_enabled) and not candidates:
        offer = {
            **common,
            "candidates": fallback_candidates,
            "constraints_satisfied": False,
            "awaiting_fallback_confirmation": bool(fallback_candidates),
        }
        return None, offer
    return {**common, "awaiting_fallback_confirmation": False}, None


def _pending_from_fallback_offer(offer: dict) -> dict:
    """Promote an explicit fallback offer to pending only after user action."""
    pending = deepcopy(offer)
    pending["awaiting_fallback_confirmation"] = False
    pending["fallback_used"] = True
    pending["constraints_satisfied"] = False
    metadata = dict(pending.get("metadata") or {})
    metadata["selected_count"] = len(pending.get("candidates") or [])
    metadata["constraints_satisfied"] = False
    metadata["fallback_used"] = True
    pending["metadata"] = metadata
    return pending


def _replacement_constraint_preview(
    pending: dict,
    replace_index: int,
    replacement: dict,
) -> dict:
    """Validate the current and simulated post-replacement candidate sets."""
    constraints_enabled = normalize_split_time_constraints(
        pending.get("constraints_enabled")
    )
    if not _constraints_active(constraints_enabled):
        return {
            "constraints_enabled": constraints_enabled,
            "current_status": None,
            "next_status": None,
            "current_validation": None,
            "next_validation": None,
        }
    candidates = list(pending.get("candidates") or [])
    simulated = list(candidates)
    simulated[replace_index] = replacement
    current_validation = validate_split_candidate_set(candidates)
    next_validation = validate_split_candidate_set(simulated)
    return {
        "constraints_enabled": constraints_enabled,
        "current_status": evaluate_split_constraint_satisfaction(
            current_validation,
            constraints_enabled,
        ),
        "next_status": evaluate_split_constraint_satisfaction(
            next_validation,
            constraints_enabled,
        ),
        "current_validation": current_validation,
        "next_validation": next_validation,
    }


def _pending_has_constraint_warning(pending: dict) -> bool:
    return (
        _constraints_active(pending.get("constraints_enabled"))
        and pending.get("constraints_satisfied") is False
    )


def _render_constraint_validation(
    validation: dict | None,
    t,
    *,
    expanded: bool = False,
) -> None:
    if not isinstance(validation, dict):
        return
    groups = validation.get("time_group_results") or {}
    opposite = validation.get("opposite_time_results") or {}
    rows = [
        ("split_auto_constraint_cv_high_plus", (groups.get("high_plus") or {}).get("cv_pct")),
        ("split_auto_constraint_cv_high_minus", (groups.get("high_minus") or {}).get("cv_pct")),
        ("split_auto_constraint_cv_low_plus", (groups.get("low_plus") or {}).get("cv_pct")),
        ("split_auto_constraint_cv_low_minus", (groups.get("low_minus") or {}).get("cv_pct")),
        ("split_auto_constraint_diff_high", (opposite.get("high") or {}).get("diff_pct")),
        ("split_auto_constraint_diff_low", (opposite.get("low") or {}).get("diff_pct")),
    ]
    with st.expander(t("split_auto_constraint_diagnostic"), expanded=expanded):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        t("split_auto_time_check"): t(label_key),
                        t("split_auto_time_value"): _format_number(value),
                    }
                    for label_key, value in rows
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def _store_pending_selection(pending: dict) -> None:
    st.session_state.split_auto_selection_pending = pending
    st.session_state.split_auto_selection_last_result = pending
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_pending"] = pending
        tests[active_test_id]["split_auto_selection_last_result"] = pending


def _store_fallback_offer(offer: dict) -> None:
    st.session_state.split_auto_selection_pending = None
    st.session_state.split_auto_selection_last_result = offer
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_pending"] = None
        tests[active_test_id]["split_auto_selection_last_result"] = offer


def _set_replace_request(
    replace_index: int,
    old_candidate: dict,
    new_candidate: dict,
    metadata: dict,
    constraint_preview: dict | None = None,
) -> None:
    request = {
        "index": replace_index,
        "old_candidate": deepcopy(old_candidate),
        "new_candidate": deepcopy(new_candidate),
        "old_signature": split_candidate_signature(old_candidate),
        "new_signature": split_candidate_signature(new_candidate),
        "metadata": deepcopy(metadata),
        "constraint_preview": deepcopy(constraint_preview),
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
        _replacement_constraint_preview(
            pending,
            replace_index,
            replacement,
        ),
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
    constraints_enabled = normalize_split_time_constraints(
        pending.get("constraints_enabled")
    )
    if _constraints_active(constraints_enabled):
        constraint_validation = validate_split_candidate_set(candidates)
        pending["constraint_validation"] = constraint_validation
        pending["constraints_satisfied"] = evaluate_split_constraint_satisfaction(
            constraint_validation,
            constraints_enabled,
        )
        pending["constraint_warnings"] = _constraint_warning_messages(
            constraint_validation
        )
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
    constraint_preview = request.get("constraint_preview") or {}
    if _constraints_active(constraint_preview.get("constraints_enabled")):
        status_columns = st.columns(2)
        status_columns[0].metric(
            t("split_auto_replace_current_constraint_status"),
            _constraint_status_label(
                constraint_preview.get("current_status"),
                t,
            ),
        )
        status_columns[1].metric(
            t("split_auto_replace_next_constraint_status"),
            _constraint_status_label(
                constraint_preview.get("next_status"),
                t,
            ),
        )
        if constraint_preview.get("next_status") is False:
            st.warning(t("split_auto_replace_constraints_failed"))
        elif constraint_preview.get("next_status") is None:
            st.info(t("split_auto_replace_constraints_inconclusive"))
        else:
            st.success(t("split_auto_replace_constraints_approved"))
        _render_constraint_validation(
            constraint_preview.get("next_validation"),
            t,
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
    st.session_state.split_auto_selection_last_result = None
    _clear_replace_request()
    active_test_id = st.session_state.get("active_test_id")
    tests = st.session_state.get("tests") or {}
    if active_test_id in tests:
        tests[active_test_id]["split_auto_selection_pending"] = None
        tests[active_test_id]["split_auto_selection_last_result"] = None


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
    if _constraints_active(pending.get("constraints_enabled")):
        if pending.get("constraints_satisfied") is True:
            st.success(t("split_auto_constraints_approved"))
        elif pending.get("constraints_satisfied") is False:
            st.warning(t("split_auto_constraints_pending_failed"))
        else:
            st.info(t("split_auto_constraints_inconclusive"))
    _render_selection_diagnostics(metadata, t)
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
                if _pending_has_constraint_warning(pending):
                    st.warning(t("split_auto_constraints_card_warning"))
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
    if isinstance(pending.get("constraint_validation"), dict):
        _render_constraint_validation(
            pending.get("constraint_validation"),
            t,
            expanded=_pending_has_constraint_warning(pending),
        )
    else:
        _render_time_validation(metadata.get("time_validation"), t)
    if isinstance(merge_metadata, dict):
        _render_merge_feedback(merge_metadata, t)


def _render_fallback_offer(offer: dict, t) -> None:
    st.warning(t("split_auto_constraints_no_valid_set"))
    _render_selection_diagnostics(offer.get("metadata"), t)
    _render_constraint_validation(
        offer.get("constraint_validation"),
        t,
        expanded=True,
    )
    warnings = offer.get("constraint_warnings") or []
    if warnings:
        with st.expander(t("split_auto_constraint_warnings"), expanded=False):
            st.warning("\n".join(str(item) for item in warnings))
    if offer.get("candidates") and st.button(
        t("split_auto_use_fallback"),
        type="primary",
        width="stretch",
        key="split_auto_use_fallback",
    ):
        _store_pending_selection(_pending_from_fallback_offer(offer))
        _clear_replace_request()
        st.rerun()


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

    k = int(
        st.number_input(
            t("split_auto_k"),
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            key="split_auto_k",
        )
    )
    with st.expander(
        t("split_auto_search_advanced_settings"),
        expanded=False,
    ):
        settings_columns = st.columns(2)
        max_combinations = int(
            settings_columns[0].number_input(
                t("split_auto_max_combinations"),
                min_value=100,
                max_value=1_000_000,
                value=200_000,
                step=10_000,
                key="split_auto_max_combinations",
            )
        )
        avoid_repeated_runs = settings_columns[1].checkbox(
            t("split_auto_avoid_repeated"),
            value=True,
            key="split_auto_avoid_repeated",
        )
        settings_columns[1].caption(t("split_auto_avoid_repeated_help"))

        st.markdown(f"#### {t('split_auto_constraint_section')}")
        st.caption(t("split_auto_constraint_description"))
        constraint_columns = st.columns(2)
        require_time_cv = constraint_columns[0].checkbox(
            t("split_auto_require_time_cv"),
            value=True,
            key="split_auto_require_time_cv",
        )
        require_opposite_time_difference = constraint_columns[1].checkbox(
            t("split_auto_require_opposite_difference"),
            value=True,
            key="split_auto_require_opposite_difference",
        )
        constraints_enabled = any(
            (
                require_time_cv,
                require_opposite_time_difference,
            )
        )
        search_columns = st.columns(3)
        search_pool_size = int(
            search_columns[0].number_input(
                t("split_auto_search_pool_size"),
                min_value=max(1, k),
                max_value=10000,
                value=_default_constraint_search_pool_size(k),
                step=20,
                key="split_auto_search_pool_size",
                disabled=not constraints_enabled,
            )
        )
        max_set_evaluations = int(
            search_columns[1].number_input(
                t("split_auto_search_max_set_evaluations"),
                min_value=1,
                max_value=1000000,
                value=6000,
                step=500,
                key="split_auto_search_max_set_evaluations",
                disabled=not constraints_enabled,
            )
        )
        max_search_seconds = float(
            search_columns[2].number_input(
                t("split_auto_search_max_seconds"),
                min_value=0.1,
                max_value=600.0,
                value=30.0,
                step=5.0,
                key="split_auto_search_max_seconds",
                disabled=not constraints_enabled,
            )
        )
        if not constraints_enabled:
            st.caption(t("split_auto_search_disabled_help"))

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
        fixed_temperature_c = None
        fixed_pressure_kpa = None
        if ambient_mode == "fixed":
            test_id = str(st.session_state.get("active_test_id") or "test")
            fixed_columns = st.columns(2)
            # Initial values only; both fixed parameters remain user-editable.
            fixed_temperature_c = float(fixed_columns[0].number_input(
                t("split_auto_fixed_temperature_c"),
                value=20.0,
                step=0.5,
                key=f"split_auto_fixed_temperature_c_{test_id}",
            ))
            fixed_pressure_kpa = float(fixed_columns[1].number_input(
                t("split_auto_fixed_pressure_kpa"),
                min_value=0.001,
                value=101.325,
                step=0.1,
                format="%.3f",
                key=f"split_auto_fixed_pressure_kpa_{test_id}",
            ))
            if fixed_temperature_c > 35.0:
                st.warning(t("split_auto_fixed_temperature_warning"))
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

    correction_context = _correction_context(
        t,
        ambient_mode,
        fixed_temperature_c,
        fixed_pressure_kpa,
    )
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
        phase_placeholder = st.empty()
        last_progress_percent = 0

        def update_progress(value):
            nonlocal last_progress_percent
            progress_value = min(max(float(value), 0.0), 1.0)
            progress_percent = int(progress_value * 100)
            if progress_percent != last_progress_percent:
                progress.progress(progress_value)
                last_progress_percent = progress_percent

        def progress_callback(value):
            generation_progress = min(max(float(value), 0.0), 1.0)
            update_progress(0.05 + generation_progress * 0.50)

        def phase_callback(phase):
            phase_config = {
                "generating": (0.05, "split_auto_phase_generating"),
                "ranking": (0.60, "split_auto_phase_ranking"),
                "searching": (0.65, "split_auto_phase_searching"),
                "finalizing": (0.95, "split_auto_phase_finalizing"),
            }
            progress_value, label_key = phase_config.get(
                phase,
                (0.0, "split_auto_running"),
            )
            update_progress(progress_value)
            phase_placeholder.caption(t(label_key))

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
                    phase_callback=phase_callback,
                    exclude_invalid_weather=exclude_invalid_weather,
                    require_time_cv=require_time_cv,
                    require_opposite_time_difference=(
                        require_opposite_time_difference
                    ),
                    search_pool_size=search_pool_size,
                    max_set_evaluations=max_set_evaluations,
                    max_search_seconds=max_search_seconds,
                )
        except ValueError as exc:
            progress.empty()
            st.error(str(exc))
        else:
            update_progress(1.0)
            selection_metadata = metadata.get("selection") or {}
            if (
                selection_metadata.get("timeout_reached")
                or selection_metadata.get("max_set_evaluations_reached")
            ):
                phase_placeholder.caption(t("split_auto_phase_stopped_by_limit"))
            else:
                phase_placeholder.caption(t("split_auto_phase_completed"))
            ranked_pool = list(metadata.pop("replacement_pool", []))
            pending, fallback_offer = _build_selection_state(
                algorithm=algorithm,
                candidates=candidates,
                ranked_pool=ranked_pool,
                metadata=metadata,
                avoid_repeated_runs=avoid_repeated_runs,
                target_f0=target_f0,
                target_f2=target_f2,
                ambient_mode=ambient_mode,
                weather_metadata=weather_metadata,
            )
            if pending is not None:
                _store_pending_selection(pending)
            elif fallback_offer is not None:
                _store_fallback_offer(fallback_offer)
            _clear_replace_request()
            if (
                not candidates
                and (
                    fallback_offer is None
                    or not fallback_offer.get("candidates")
                )
            ):
                st.warning(t("split_auto_no_candidates_returned"))

    pending = st.session_state.get("split_auto_selection_pending")
    if isinstance(pending, dict):
        st.markdown("---")
        _render_execution_result(pending, t)
    else:
        fallback_offer = st.session_state.get("split_auto_selection_last_result")
        if (
            isinstance(fallback_offer, dict)
            and fallback_offer.get("awaiting_fallback_confirmation") is True
        ):
            st.markdown("---")
            _render_fallback_offer(fallback_offer, t)

# coding: utf-8
"""Pure normative time diagnostics for selected Split candidates."""

from __future__ import annotations

import math
import statistics


TIME_COMPONENTS = ("high_plus", "high_minus", "low_plus", "low_minus")
EPSILON = 1e-12


def _finite_float(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _valid_values(values) -> list[float]:
    return [
        number
        for number in (_finite_float(value) for value in values or [])
        if number is not None
    ]


def coefficient_of_variation_percent(values: list[float]) -> float | None:
    """Return sample coefficient of variation in percent, when evaluable."""
    valid = _valid_values(values)
    if len(valid) < 2:
        return None
    mean_value = statistics.mean(valid)
    if abs(mean_value) <= EPSILON:
        return None
    return statistics.stdev(valid) / abs(mean_value) * 100.0


def opposite_mean_difference_percent(
    mean_a: float | None,
    mean_b: float | None,
) -> float | None:
    """Return percent difference between opposite-direction mean times."""
    first = _finite_float(mean_a)
    second = _finite_float(mean_b)
    if first is None or second is None:
        return None
    denominator = (first + second) / 2.0
    if abs(denominator) <= EPSILON:
        return None
    return abs(first - second) / abs(denominator) * 100.0


def split_candidate_component_time(candidate: dict, component: str) -> float | None:
    """Read one candidate component time using the canonical fallback order."""
    source = candidate if isinstance(candidate, dict) else {}

    time_components = source.get("time_components")
    if isinstance(time_components, dict):
        component_data = time_components.get(component)
        if isinstance(component_data, dict):
            value = _finite_float(component_data.get("delta_t_s"))
            if value is not None:
                return value

    value = _finite_float(source.get(f"{component}_delta_t_s"))
    if value is not None:
        return value

    record = source.get(component)
    if isinstance(record, dict):
        return _finite_float(record.get("delta_t_s"))
    return None


def extract_split_candidate_times(candidates: list[dict]) -> dict:
    """Extract valid high/low and plus/minus Delta t lists from candidates."""
    times = {component: [] for component in TIME_COMPONENTS}
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        for component in TIME_COMPONENTS:
            value = split_candidate_component_time(candidate, component)
            if value is not None:
                times[component].append(value)
    return times


def _mean(values: list[float]) -> float | None:
    valid = _valid_values(values)
    return statistics.mean(valid) if valid else None


def _group_result(values: list[float], cv_limit_pct: float) -> dict:
    valid = _valid_values(values)
    cv_pct = coefficient_of_variation_percent(valid)
    return {
        "count": len(valid),
        "mean": statistics.mean(valid) if valid else None,
        "cv_pct": cv_pct,
        "passed": None if cv_pct is None else cv_pct <= cv_limit_pct,
    }


def _opposite_result(
    mean_plus: float | None,
    mean_minus: float | None,
    opposite_mean_limit_pct: float,
) -> dict:
    diff_pct = opposite_mean_difference_percent(mean_plus, mean_minus)
    return {
        "mean_plus": mean_plus,
        "mean_minus": mean_minus,
        "diff_pct": diff_pct,
        "passed": (
            None
            if diff_pct is None
            else diff_pct <= opposite_mean_limit_pct
        ),
    }


def _missing_time_warnings(candidates: list[dict]) -> list[str]:
    warnings = []
    for index, candidate in enumerate(candidates or [], start=1):
        if not isinstance(candidate, dict):
            warnings.append(f"Candidate {index} is not a valid mapping.")
            continue
        candidate_id = candidate.get("id") or f"candidate {index}"
        for component in TIME_COMPONENTS:
            if split_candidate_component_time(candidate, component) is None:
                warnings.append(
                    f"Candidate {candidate_id} is missing {component} delta_t_s."
                )
    return warnings


def validate_split_selected_times(
    candidates: list[dict],
    *,
    cv_limit_pct: float = 2.5,
    opposite_mean_limit_pct: float = 10.0,
) -> dict:
    """Validate selected-candidate Split time diagnostics without filtering."""
    times = extract_split_candidate_times(candidates)
    warnings = _missing_time_warnings(candidates)

    groups = {
        component: _group_result(times[component], cv_limit_pct)
        for component in TIME_COMPONENTS
    }
    for component, result in groups.items():
        if result["count"] < 2:
            warnings.append(
                f"Insufficient sample to evaluate CV for {component}: "
                f"{result['count']} valid time(s)."
            )

    opposite_direction = {
        "high": _opposite_result(
            groups["high_plus"]["mean"],
            groups["high_minus"]["mean"],
            opposite_mean_limit_pct,
        ),
        "low": _opposite_result(
            groups["low_plus"]["mean"],
            groups["low_minus"]["mean"],
            opposite_mean_limit_pct,
        ),
    }
    for interval_name, result in opposite_direction.items():
        if result["diff_pct"] is None:
            warnings.append(
                f"Insufficient sample to evaluate opposite-direction mean "
                f"difference for {interval_name}."
            )

    checks = [
        result["passed"]
        for result in groups.values()
    ] + [
        result["passed"]
        for result in opposite_direction.values()
    ]
    if any(value is False for value in checks):
        passed = False
    elif all(value is True for value in checks):
        passed = True
    else:
        passed = None

    return {
        "passed": passed,
        "cv_limit_pct": cv_limit_pct,
        "opposite_mean_limit_pct": opposite_mean_limit_pct,
        "groups": groups,
        "opposite_direction": opposite_direction,
        "warnings": list(dict.fromkeys(warnings)),
    }

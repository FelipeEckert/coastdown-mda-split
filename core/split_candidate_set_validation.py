# coding: utf-8
"""Pure normative validation for sets of automatic Split candidates."""

from __future__ import annotations

from core.split_results import normalize_split_final_pair
from core.split_time_validation import (
    coefficient_of_variation_percent,
    validate_split_selected_times,
)


def _coefficient_values(candidates: list[dict]) -> tuple[list[float], list[float]]:
    f0_values = []
    f2_values = []
    for index, candidate in enumerate(candidates, start=1):
        normalized = normalize_split_final_pair(candidate, index)
        if normalized["F0_mean"] is not None:
            f0_values.append(normalized["F0_mean"])
        if normalized["F2_mean"] is not None:
            f2_values.append(normalized["F2_mean"])
    return f0_values, f2_values


def _coefficient_status(
    candidate_count: int,
    f0_values: list[float],
    f2_values: list[float],
    cv_f0_pct: float | None,
    cv_f2_pct: float | None,
    limit_pct: float,
) -> str:
    if any(
        value is not None and value > limit_pct
        for value in (cv_f0_pct, cv_f2_pct)
    ):
        return "failed"
    if (
        len(f0_values) != candidate_count
        or len(f2_values) != candidate_count
        or cv_f0_pct is None
        or cv_f2_pct is None
    ):
        return "insufficient_data"
    return "approved"


def validate_split_candidate_set(
    candidates: list[dict],
    *,
    coefficient_cv_limit_pct: float = 10.0,
    time_cv_limit_pct: float = 2.5,
    opposite_time_limit_pct: float = 10.0,
) -> dict:
    """Validate coefficient and time constraints for a complete candidate set."""
    valid_candidates = [
        candidate for candidate in candidates or [] if isinstance(candidate, dict)
    ]
    warnings = []
    if len(valid_candidates) != len(candidates or []):
        warnings.append("One or more candidates are not valid mappings.")

    f0_values, f2_values = _coefficient_values(valid_candidates)
    cv_f0_pct = coefficient_of_variation_percent(f0_values)
    cv_f2_pct = coefficient_of_variation_percent(f2_values)
    coefficient_status = _coefficient_status(
        len(valid_candidates),
        f0_values,
        f2_values,
        cv_f0_pct,
        cv_f2_pct,
        coefficient_cv_limit_pct,
    )
    if len(f0_values) != len(valid_candidates):
        warnings.append(
            "One or more candidates are missing corrected F0_mean/F0."
        )
    if len(f2_values) != len(valid_candidates):
        warnings.append(
            "One or more candidates are missing corrected F2_mean/F2."
        )
    if cv_f0_pct is None:
        warnings.append("Insufficient sample to evaluate corrected F0 CV.")
    if cv_f2_pct is None:
        warnings.append("Insufficient sample to evaluate corrected F2 CV.")

    time_validation = validate_split_selected_times(
        valid_candidates,
        cv_limit_pct=time_cv_limit_pct,
        opposite_mean_limit_pct=opposite_time_limit_pct,
    )
    time_status = {
        True: "approved",
        False: "failed",
        None: "insufficient_data",
    }[time_validation["passed"]]

    failed_checks = []
    if cv_f0_pct is not None and cv_f0_pct > coefficient_cv_limit_pct:
        failed_checks.append("coefficient.cv_f0")
    if cv_f2_pct is not None and cv_f2_pct > coefficient_cv_limit_pct:
        failed_checks.append("coefficient.cv_f2")
    for component, result in time_validation["groups"].items():
        if result["passed"] is False:
            failed_checks.append(f"time.group.{component}")
    for interval, result in time_validation["opposite_direction"].items():
        if result["passed"] is False:
            failed_checks.append(f"time.opposite.{interval}")

    statuses = (coefficient_status, time_status)
    if "failed" in statuses:
        passed = False
    elif all(status == "approved" for status in statuses):
        passed = True
    else:
        passed = None

    warnings.extend(time_validation["warnings"])
    return {
        "passed": passed,
        "coefficient_status": coefficient_status,
        "time_status": time_status,
        "cv_f0_pct": cv_f0_pct,
        "cv_f2_pct": cv_f2_pct,
        "time_group_results": time_validation["groups"],
        "opposite_time_results": time_validation["opposite_direction"],
        "failed_checks": failed_checks,
        "warnings": list(dict.fromkeys(warnings)),
    }

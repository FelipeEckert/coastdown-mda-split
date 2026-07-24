# coding: utf-8
"""Pure normative validation for sets of automatic Split candidates."""

from __future__ import annotations

from core.split_results import normalize_split_final_pair
from core.split_time_validation import (
    coefficient_of_variation_percent,
    validate_split_selected_times,
)


TIME_CONSTRAINT_KEYS = ("time_cv", "opposite_time_difference")


def normalize_split_time_constraints(constraints_enabled: dict | None) -> dict:
    """Return only normative Split time constraints, ignoring legacy keys."""
    source = constraints_enabled if isinstance(constraints_enabled, dict) else {}
    return {
        key: bool(source.get(key))
        for key in TIME_CONSTRAINT_KEYS
    }


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
    """Validate normative times and retain coefficient CV as diagnostics only."""
    valid_candidates = [
        candidate for candidate in candidates or [] if isinstance(candidate, dict)
    ]
    warnings = []
    coefficient_warnings = []
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
        coefficient_warnings.append(
            "One or more candidates are missing corrected F0_mean/F0."
        )
    if len(f2_values) != len(valid_candidates):
        coefficient_warnings.append(
            "One or more candidates are missing corrected F2_mean/F2."
        )
    if cv_f0_pct is None:
        coefficient_warnings.append(
            "Insufficient sample to evaluate corrected F0 CV."
        )
    if cv_f2_pct is None:
        coefficient_warnings.append(
            "Insufficient sample to evaluate corrected F2 CV."
        )

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
    for component, result in time_validation["groups"].items():
        if result["passed"] is False:
            failed_checks.append(f"time.group.{component}")
    for interval, result in time_validation["opposite_direction"].items():
        if result["passed"] is False:
            failed_checks.append(f"time.opposite.{interval}")

    warnings.extend(time_validation["warnings"])
    return {
        "passed": time_validation["passed"],
        "coefficient_status": coefficient_status,
        "coefficient_diagnostic_only": True,
        "coefficient_warnings": list(dict.fromkeys(coefficient_warnings)),
        "time_status": time_status,
        "time_cv_limit_pct": time_cv_limit_pct,
        "opposite_time_limit_pct": opposite_time_limit_pct,
        "cv_f0_pct": cv_f0_pct,
        "cv_f2_pct": cv_f2_pct,
        "time_group_results": time_validation["groups"],
        "opposite_time_results": time_validation["opposite_direction"],
        "failed_checks": failed_checks,
        "warnings": list(dict.fromkeys(warnings)),
    }


def evaluate_split_constraint_satisfaction(
    validation: dict,
    constraints_enabled: dict,
) -> bool | None:
    """Return aggregate status considering only normative Split time checks."""
    enabled = normalize_split_time_constraints(constraints_enabled)
    active_checks = []
    if enabled["time_cv"]:
        active_checks.extend(
            result["passed"]
            for result in validation["time_group_results"].values()
        )
    if enabled["opposite_time_difference"]:
        active_checks.extend(
            result["passed"]
            for result in validation["opposite_time_results"].values()
        )
    if any(check is False for check in active_checks):
        return False
    if active_checks and any(check is None for check in active_checks):
        return None
    return True

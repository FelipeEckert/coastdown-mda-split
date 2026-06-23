# coding: utf-8
"""Pure ranking and top-k helpers for automatic Split pair selection."""

from __future__ import annotations

from copy import deepcopy
import math

from core.split_candidate_set_validation import validate_split_candidate_set
from core.split_comparison import SELECTION_SOURCE_ALGORITHM
from core.split_pair_candidate import split_candidate_signature


VALID_ALGORITHMS = {"energy", "target"}


def _is_finite_number(value) -> bool:
    """Return True only for finite numeric values."""
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def _finite_float(value) -> float | None:
    return float(value) if _is_finite_number(value) else None


def _candidate_energy(candidate: dict) -> float | None:
    """Read the canonical Split energy, with legacy fallbacks."""
    source = candidate if isinstance(candidate, dict) else {}
    for key in ("energy_corrected", "mean_energy_corrected", "energy", "mean_energy"):
        value = _finite_float(source.get(key))
        if value is not None:
            return value
    return None


def _candidate_corrected_f0_f2(candidate: dict) -> tuple[float | None, float | None]:
    """Read corrected Split F0/F2 using canonical names and known aliases."""
    source = candidate if isinstance(candidate, dict) else {}
    f0 = None
    f2 = None
    for key in ("F0_corrected", "F0_mean_corrected", "mean_f0_corrected", "F0_mean", "F0", "mean_f0"):
        f0 = _finite_float(source.get(key))
        if f0 is not None:
            break
    for key in ("F2_corrected", "F2_mean_corrected", "mean_f2_corrected", "F2_mean", "F2", "mean_f2"):
        f2 = _finite_float(source.get(key))
        if f2 is not None:
            break
    return f0, f2


def _signature_sort_key(candidate: dict) -> tuple:
    signature = split_candidate_signature(candidate)
    return tuple(
        tuple(f"{type(value).__name__}:{value!r}" for value in item)
        for item in signature
    )


def rank_candidates_by_energy(candidates: list[dict]) -> list[dict]:
    """Return candidates with valid energy ordered by increasing energy."""
    valid = [
        candidate
        for candidate in candidates or []
        if isinstance(candidate, dict) and _candidate_energy(candidate) is not None
    ]
    return sorted(
        valid,
        key=lambda candidate: (
            _candidate_energy(candidate),
            _signature_sort_key(candidate),
        ),
    )


def rank_candidates_by_target(
    candidates: list[dict],
    target_f0: float,
    target_f2: float,
) -> list[dict]:
    """Return candidates ranked by normalized distance to corrected F0/F2 target."""
    target_f0_value = _finite_float(target_f0)
    target_f2_value = _finite_float(target_f2)
    if target_f0_value is None or target_f2_value is None:
        raise ValueError("Target F0 and F2 must be finite numbers.")
    if target_f0_value == 0 or target_f2_value == 0:
        raise ValueError("Target F0 and F2 must be different from zero.")

    ranked = []
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        f0, f2 = _candidate_corrected_f0_f2(candidate)
        if f0 is None or f2 is None:
            continue
        error_f0 = abs(f0 - target_f0_value) / abs(target_f0_value)
        error_f2 = abs(f2 - target_f2_value) / abs(target_f2_value)
        item = deepcopy(candidate)
        item["target_score"] = math.hypot(error_f0, error_f2)
        item["target_error_f0_pct"] = error_f0 * 100.0
        item["target_error_f2_pct"] = error_f2 * 100.0
        ranked.append(item)

    return sorted(
        ranked,
        key=lambda candidate: (
            candidate["target_score"],
            _signature_sort_key(candidate),
        ),
    )


def _normalized_run_usage(candidate: dict) -> tuple | None:
    source = candidate if isinstance(candidate, dict) else {}
    usage = source.get("run_usage")
    if not usage:
        return None
    try:
        normalized = tuple(tuple(item) for item in usage)
    except TypeError:
        return None
    if not normalized or any(not item for item in normalized):
        return None
    return normalized


def select_top_k_candidates(
    ranked_candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool = True,
) -> tuple[list[dict], dict]:
    """Select up to k ranked candidates, optionally avoiding repeated runs."""
    try:
        requested_k = int(k)
    except (TypeError, ValueError) as exc:
        raise ValueError("k must be a positive integer.") from exc
    if requested_k <= 0:
        raise ValueError("k must be greater than zero.")

    metadata = {
        "requested_k": requested_k,
        "selected_count": 0,
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "skipped_repeated_count": 0,
        "skipped_invalid_usage_count": 0,
        "warnings": [],
    }

    candidates = [
        candidate
        for candidate in ranked_candidates or []
        if isinstance(candidate, dict)
    ]
    if not avoid_repeated_runs:
        selected = candidates[:requested_k]
        metadata["selected_count"] = len(selected)
        if len(selected) < requested_k:
            metadata["warnings"].append(
                f"Only {len(selected)} candidates were selected from {requested_k} requested."
            )
        return selected, metadata

    selected = []
    used_runs = set()
    for candidate in candidates:
        usage = _normalized_run_usage(candidate)
        if usage is None:
            metadata["skipped_invalid_usage_count"] += 1
            continue
        usage_set = set(usage)
        if used_runs.intersection(usage_set):
            metadata["skipped_repeated_count"] += 1
            continue
        selected.append(candidate)
        used_runs.update(usage_set)
        if len(selected) == requested_k:
            break

    metadata["selected_count"] = len(selected)
    if len(selected) < requested_k:
        metadata["warnings"].append(
            f"Only {len(selected)} candidates were selected from {requested_k} requested."
        )
    return selected, metadata


def _constraint_satisfaction(validation: dict, enabled: dict) -> bool | None:
    if (
        enabled["coefficient_cv"]
        and validation["coefficient_status"] == "failed"
    ):
        return False
    active_checks = []
    if enabled["coefficient_cv"]:
        active_checks.append(
            {
                "approved": True,
                "failed": False,
                "insufficient_data": None,
            }[validation["coefficient_status"]]
        )
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


def _iter_candidate_sets(
    candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool,
):
    """Yield ranked combinations, pruning repeated run usage before each leaf."""
    selected = []

    def visit(start_index: int, used_runs: set):
        if len(selected) == k:
            yield tuple(selected)
            return
        missing = k - len(selected)
        last_start = len(candidates) - missing
        for index in range(start_index, last_start + 1):
            candidate = candidates[index]
            next_used_runs = used_runs
            if avoid_repeated_runs:
                usage = _normalized_run_usage(candidate)
                if usage is None:
                    continue
                usage_set = set(usage)
                if used_runs.intersection(usage_set):
                    continue
                next_used_runs = used_runs.union(usage_set)
            selected.append(candidate)
            yield from visit(index + 1, next_used_runs)
            selected.pop()

    yield from visit(0, set())


def select_top_k_candidates_with_constraints(
    ranked_candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool = True,
    require_coefficient_cv: bool = True,
    require_time_cv: bool = True,
    require_opposite_time_difference: bool = True,
    coefficient_cv_limit_pct: float = 10.0,
    time_cv_limit_pct: float = 2.5,
    opposite_time_limit_pct: float = 10.0,
    search_pool_size: int | None = None,
    max_set_evaluations: int = 5000,
) -> tuple[list[dict], dict]:
    """Find the first ranked candidate set satisfying all active constraints."""
    try:
        requested_k = int(k)
    except (TypeError, ValueError) as exc:
        raise ValueError("k must be a positive integer.") from exc
    if requested_k <= 0:
        raise ValueError("k must be greater than zero.")
    try:
        evaluation_limit = int(max_set_evaluations)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_set_evaluations must be a positive integer.") from exc
    if evaluation_limit <= 0:
        raise ValueError("max_set_evaluations must be greater than zero.")

    default_pool_size = max(100, requested_k * 20, requested_k + 50)
    if search_pool_size is None:
        requested_pool_size = default_pool_size
    else:
        try:
            requested_pool_size = int(search_pool_size)
        except (TypeError, ValueError) as exc:
            raise ValueError("search_pool_size must be a positive integer.") from exc
        if requested_pool_size <= 0:
            raise ValueError("search_pool_size must be greater than zero.")

    candidates = [
        candidate
        for candidate in ranked_candidates or []
        if isinstance(candidate, dict)
    ]
    pool = candidates[:requested_pool_size]
    enabled = {
        "coefficient_cv": bool(require_coefficient_cv),
        "time_cv": bool(require_time_cv),
        "opposite_time_difference": bool(require_opposite_time_difference),
    }
    fallback_candidates, _ = select_top_k_candidates(
        candidates,
        requested_k,
        avoid_repeated_runs=avoid_repeated_runs,
    )
    metadata = {
        "requested_k": requested_k,
        "selected_count": 0,
        "constraints_enabled": enabled,
        "constraints_satisfied": False,
        "evaluated_sets_count": 0,
        "search_pool_size": len(pool),
        "fallback_used": False,
        "best_failed_validation": None,
        "fallback_candidates": list(fallback_candidates),
        "warnings": [],
    }

    if len(pool) < requested_k:
        metadata["warnings"].append(
            f"Search pool has only {len(pool)} candidates for {requested_k} requested."
        )
        return [], metadata

    for candidate_set in _iter_candidate_sets(
        pool,
        requested_k,
        avoid_repeated_runs=avoid_repeated_runs,
    ):
        validation = validate_split_candidate_set(
            list(candidate_set),
            coefficient_cv_limit_pct=coefficient_cv_limit_pct,
            time_cv_limit_pct=time_cv_limit_pct,
            opposite_time_limit_pct=opposite_time_limit_pct,
        )
        metadata["evaluated_sets_count"] += 1
        constraint_satisfaction = _constraint_satisfaction(validation, enabled)
        if constraint_satisfaction is not False:
            selected = list(candidate_set)
            metadata.update(
                {
                    "selected_count": len(selected),
                    "constraints_satisfied": constraint_satisfaction,
                    "fallback_candidates": [],
                    "validation": validation,
                }
            )
            return selected, metadata
        if metadata["best_failed_validation"] is None:
            metadata["best_failed_validation"] = validation
            metadata["fallback_candidates"] = list(candidate_set)
        if metadata["evaluated_sets_count"] >= evaluation_limit:
            metadata["warnings"].append(
                f"Search stopped after max_set_evaluations={evaluation_limit}."
            )
            break

    if metadata["best_failed_validation"] is None:
        metadata["warnings"].append(
            "No complete candidate set could be evaluated with the active run constraints."
        )
    else:
        metadata["warnings"].append(
            "No candidate set satisfied all active normative constraints."
        )
    if len(metadata["fallback_candidates"]) < requested_k:
        metadata["warnings"].append(
            "Fallback contains only "
            f"{len(metadata['fallback_candidates'])} candidates from "
            f"{requested_k} requested."
        )
    return [], metadata


def mark_algorithm_source(
    candidates: list[dict],
    algorithm: str,
) -> list[dict]:
    """Return copies marked as algorithm-origin candidates without final selection."""
    algorithm_name = str(algorithm or "").strip().lower()
    if algorithm_name not in VALID_ALGORITHMS:
        raise ValueError("algorithm must be 'energy' or 'target'.")

    marked = []
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        item = deepcopy(candidate)
        item["selected"] = False
        item["selection_source"] = SELECTION_SOURCE_ALGORITHM
        item["algorithm_source"] = algorithm_name
        item["selected_by_energy_algo"] = algorithm_name == "energy"
        item["selected_by_target_algo"] = algorithm_name == "target"
        marked.append(item)
    return marked

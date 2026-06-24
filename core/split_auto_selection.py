# coding: utf-8
"""Pure orchestration for exact automatic Split pair selection."""

from __future__ import annotations

from copy import deepcopy

from core.split_candidate_generation import generate_full_split_candidates_exact
from core.split_candidate_set_validation import (
    evaluate_split_constraint_satisfaction,
    normalize_split_time_constraints,
    validate_split_candidate_set,
)
from core.split_pair_candidate import split_candidate_signature
from core.split_selection_algorithms import (
    VALID_ALGORITHMS,
    mark_algorithm_source,
    rank_candidates_by_energy,
    rank_candidates_by_target,
    select_top_k_candidates,
    select_top_k_candidates_with_constraints_v2,
)
from core.split_time_validation import validate_split_selected_times


def _algorithm_name(value: str) -> str:
    algorithm = str(value or "").strip().lower()
    if algorithm not in VALID_ALGORITHMS:
        raise ValueError("algorithm must be 'energy' or 'target'.")
    return algorithm


def _requested_k(value: int) -> int:
    try:
        requested = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("k must be a positive integer.") from exc
    if requested <= 0:
        raise ValueError("k must be greater than zero.")
    return requested


def _replacement_pool_limit(value: int | None) -> int | None:
    if value is None:
        return None
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("replacement_pool_size must be a positive integer.") from exc
    if limit <= 0:
        raise ValueError("replacement_pool_size must be greater than zero.")
    return limit


def _warnings(*sources) -> list[str]:
    warnings = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        warnings.extend(source.get("warnings") or [])
    return list(dict.fromkeys(str(warning) for warning in warnings if str(warning).strip()))


def _notify_phase(callback, phase: str) -> None:
    if callback is not None:
        callback(phase)


def _empty_selection_metadata(k: int, avoid_repeated_runs: bool) -> dict:
    return {
        "requested_k": k,
        "selected_count": 0,
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "skipped_repeated_count": 0,
        "skipped_invalid_usage_count": 0,
        "warnings": [],
    }


def _normalized_run_usage(candidate: dict) -> tuple | None:
    usage = candidate.get("run_usage") if isinstance(candidate, dict) else None
    if not usage:
        return None
    try:
        normalized = tuple(tuple(item) for item in usage)
    except TypeError:
        return None
    if not normalized or any(not item for item in normalized):
        return None
    return normalized


def _candidate_identifier(candidate: dict):
    identifier = candidate.get("id") if isinstance(candidate, dict) else None
    return identifier or split_candidate_signature(candidate)


def _build_replacement_pool(
    ranked_candidates: list[dict],
    selected_candidates: list[dict],
    limit: int,
    *,
    avoid_repeated_runs: bool,
) -> list[dict]:
    """Collect ranked candidates that can replace the visible suggestions."""
    selected = [
        candidate
        for candidate in selected_candidates
        if isinstance(candidate, dict)
    ]
    if not selected:
        return []

    quota = max(1, limit // len(selected))
    option_counts = [0] * len(selected)
    selected_signatures = [split_candidate_signature(candidate) for candidate in selected]
    remaining_signatures = []
    remaining_runs = []
    for replace_index in range(len(selected)):
        remaining = selected[:replace_index] + selected[replace_index + 1 :]
        remaining_signatures.append(
            {split_candidate_signature(candidate) for candidate in remaining}
        )
        used_runs = set()
        for candidate in remaining:
            usage = _normalized_run_usage(candidate)
            if usage is not None:
                used_runs.update(usage)
        remaining_runs.append(used_runs)

    pool = []
    for candidate in ranked_candidates:
        if not isinstance(candidate, dict):
            continue
        signature = split_candidate_signature(candidate)
        usage = _normalized_run_usage(candidate) if avoid_repeated_runs else None
        valid_indices = []
        for replace_index in range(len(selected)):
            if option_counts[replace_index] >= quota:
                continue
            if signature == selected_signatures[replace_index]:
                continue
            if signature in remaining_signatures[replace_index]:
                continue
            if avoid_repeated_runs:
                if usage is None or remaining_runs[replace_index].intersection(usage):
                    continue
            valid_indices.append(replace_index)
        if not valid_indices:
            continue
        pool.append(candidate)
        assigned_index = min(
            valid_indices,
            key=lambda index: (option_counts[index], index),
        )
        option_counts[assigned_index] += 1
        if len(pool) >= limit or all(count >= quota for count in option_counts):
            break
    return pool


def find_replacement_candidate(
    current_candidates: list[dict],
    ranked_pool: list[dict],
    replace_index: int,
    *,
    avoid_repeated_runs: bool = True,
) -> tuple[dict | None, dict]:
    """Return the next valid ranked replacement without mutating inputs."""
    candidates = [
        deepcopy(candidate)
        for candidate in (current_candidates or [])
        if isinstance(candidate, dict)
    ]
    if not isinstance(replace_index, int) or isinstance(replace_index, bool):
        raise ValueError("replace_index must be an integer.")
    if replace_index < 0 or replace_index >= len(candidates):
        raise IndexError("replace_index is outside the pending candidate list.")

    old_candidate = candidates[replace_index]
    remaining = candidates[:replace_index] + candidates[replace_index + 1 :]
    old_signature = split_candidate_signature(old_candidate)
    remaining_signatures = {
        split_candidate_signature(candidate) for candidate in remaining
    }
    used_runs = set()
    if avoid_repeated_runs:
        for candidate in remaining:
            usage = _normalized_run_usage(candidate)
            if usage is not None:
                used_runs.update(usage)

    metadata = {
        "found": False,
        "replace_index": replace_index,
        "old_identifier": _candidate_identifier(old_candidate),
        "new_identifier": None,
        "skipped_old_candidate_count": 0,
        "skipped_existing_count": 0,
        "skipped_repeated_count": 0,
        "skipped_invalid_usage_count": 0,
        "checked_pool_count": 0,
        "pool_size": len(ranked_pool or []),
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "warnings": [],
    }

    replacement = None
    for candidate in ranked_pool or []:
        metadata["checked_pool_count"] += 1
        if not isinstance(candidate, dict):
            continue
        signature = split_candidate_signature(candidate)
        if signature == old_signature:
            metadata["skipped_old_candidate_count"] += 1
            continue
        if signature in remaining_signatures:
            metadata["skipped_existing_count"] += 1
            continue
        if avoid_repeated_runs:
            usage = _normalized_run_usage(candidate)
            if usage is None:
                metadata["skipped_invalid_usage_count"] += 1
                continue
            if used_runs.intersection(usage):
                metadata["skipped_repeated_count"] += 1
                continue
        replacement = deepcopy(candidate)
        break

    if replacement is None:
        metadata["warnings"].append(
            "No valid replacement candidate is available after checking "
            f"{metadata['checked_pool_count']} of {metadata['pool_size']} pool candidates."
        )
        return None, metadata

    metadata["found"] = True
    metadata["new_identifier"] = _candidate_identifier(replacement)
    return replacement, metadata


def replace_pending_candidate(
    current_candidates: list[dict],
    ranked_pool: list[dict],
    replace_index: int,
    *,
    avoid_repeated_runs: bool = True,
) -> tuple[list[dict], dict]:
    """Replace one pending suggestion with the candidate returned by preview."""
    candidates = [
        deepcopy(candidate)
        for candidate in (current_candidates or [])
        if isinstance(candidate, dict)
    ]
    replacement, find_metadata = find_replacement_candidate(
        candidates,
        ranked_pool,
        replace_index,
        avoid_repeated_runs=avoid_repeated_runs,
    )
    metadata = dict(find_metadata)
    metadata["replaced"] = replacement is not None
    if replacement is None:
        return candidates, metadata
    candidates[replace_index] = deepcopy(replacement)
    return candidates, metadata


def run_split_auto_selection_exact(
    split_parsed_runs: dict,
    *,
    vehicle_data: dict,
    correction_context: dict | None = None,
    algorithm: str,
    k: int,
    target_f0: float | None = None,
    target_f2: float | None = None,
    avoid_repeated_runs: bool = True,
    max_combinations: int | None = None,
    replacement_pool_size: int | None = None,
    progress_callback=None,
    phase_callback=None,
    candidate_builder=None,
    exclude_invalid_weather: bool = False,
    require_coefficient_cv: bool = False,
    require_time_cv: bool = False,
    require_opposite_time_difference: bool = False,
    search_pool_size: int | None = None,
    max_set_evaluations: int = 3000,
    max_search_seconds: float = 30.0,
) -> tuple[list[dict], dict]:
    """Run exact automatic Split candidate generation, ranking and diagnostics."""
    algorithm_name = _algorithm_name(algorithm)
    requested = _requested_k(k)
    pool_limit = _replacement_pool_limit(replacement_pool_size)

    _notify_phase(phase_callback, "generating")
    candidates, generation_metadata = generate_full_split_candidates_exact(
        split_parsed_runs,
        vehicle_data=vehicle_data,
        correction_context=correction_context,
        candidate_builder=candidate_builder,
        max_combinations=max_combinations,
        progress_callback=progress_callback,
    )

    weather_filtered_count = 0
    if exclude_invalid_weather:
        valid_candidates = []
        for candidate in candidates:
            status = ((candidate.get("weather_summary") or {}).get("status"))
            if status in {"missing", "invalid"}:
                weather_filtered_count += 1
            else:
                valid_candidates.append(candidate)
        candidates = valid_candidates

    constraints_enabled = normalize_split_time_constraints({
        "time_cv": bool(require_time_cv),
        "opposite_time_difference": bool(require_opposite_time_difference),
    })
    constraints_active = any(constraints_enabled.values())
    metadata = {
        "mode": "exact",
        "algorithm": algorithm_name,
        "requested_k": requested,
        "generated_count": len(candidates),
        "generated_before_weather_filter_count": len(candidates) + weather_filtered_count,
        "weather_filtered_count": weather_filtered_count,
        "exclude_invalid_weather": bool(exclude_invalid_weather),
        "ranked_count": 0,
        "selected_count": 0,
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "generation": generation_metadata,
        "selection": _empty_selection_metadata(requested, avoid_repeated_runs),
        "time_validation": None,
        "constraints_enabled": constraints_enabled,
        "constraints_satisfied": None,
        "constraint_validation": None,
        "constraint_warnings": [],
        "warnings": _warnings(generation_metadata),
    }
    if weather_filtered_count:
        metadata["warnings"].append(
            f"{weather_filtered_count} candidates were excluded by weather validation."
        )
    if pool_limit is not None:
        metadata["replacement_pool"] = []

    if not candidates:
        _notify_phase(phase_callback, "finalizing")
        metadata["warnings"] = _warnings(
            generation_metadata,
            {"warnings": ["No candidates were generated for automatic selection."]},
            {"warnings": metadata.get("warnings") or []},
        )
        return [], metadata

    _notify_phase(phase_callback, "ranking")
    if algorithm_name == "energy":
        ranked_candidates = rank_candidates_by_energy(candidates)
    else:
        if target_f0 is None or target_f2 is None:
            raise ValueError("target_f0 and target_f2 are required for target ranking.")
        ranked_candidates = rank_candidates_by_target(candidates, target_f0, target_f2)
    metadata["ranked_count"] = len(ranked_candidates)
    if constraints_active:
        _notify_phase(phase_callback, "searching")
        selected_candidates, selection_metadata = (
            select_top_k_candidates_with_constraints_v2(
                ranked_candidates,
                requested,
                avoid_repeated_runs=avoid_repeated_runs,
                require_time_cv=require_time_cv,
                require_opposite_time_difference=(
                    require_opposite_time_difference
                ),
                search_pool_size=search_pool_size,
                max_set_evaluations=max_set_evaluations,
                max_search_seconds=max_search_seconds,
            )
        )
    else:
        selected_candidates, selection_metadata = select_top_k_candidates(
            ranked_candidates,
            requested,
            avoid_repeated_runs=avoid_repeated_runs,
        )
    fallback_candidates = list(selection_metadata.get("fallback_candidates") or [])
    marked_candidates = mark_algorithm_source(selected_candidates, algorithm_name)
    marked_fallback_candidates = mark_algorithm_source(
        fallback_candidates,
        algorithm_name,
    )
    if constraints_active:
        selection_metadata["fallback_candidates"] = marked_fallback_candidates
    diagnostic_candidates = marked_candidates or marked_fallback_candidates
    if pool_limit is not None:
        replacement_pool = _build_replacement_pool(
            ranked_candidates,
            selected_candidates or fallback_candidates,
            pool_limit,
            avoid_repeated_runs=avoid_repeated_runs,
        )
        metadata["replacement_pool"] = mark_algorithm_source(
            replacement_pool,
            algorithm_name,
        )
    time_validation = validate_split_selected_times(diagnostic_candidates)
    constraint_validation = None
    constraints_satisfied = None
    constraint_warnings = []
    if constraints_active:
        constraint_validation = (
            selection_metadata.get("validation")
            or selection_metadata.get("best_failed_validation")
        )
        constraints_satisfied = selection_metadata.get("constraints_satisfied")
        constraint_warnings = _warnings(
            selection_metadata,
            constraint_validation,
        )

    metadata.update(
        {
            "selected_count": len(marked_candidates),
            "selection": selection_metadata,
            "time_validation": time_validation,
            "constraints_satisfied": constraints_satisfied,
            "constraint_validation": constraint_validation,
            "constraint_warnings": constraint_warnings,
        }
    )
    if len(marked_candidates) < requested:
        selection_metadata.setdefault("warnings", []).append(
            f"Automatic selection returned {len(marked_candidates)} candidates from {requested} requested."
        )
    metadata["warnings"] = _warnings(
        generation_metadata,
        selection_metadata,
        time_validation,
        {"warnings": metadata.get("warnings") or []},
    )
    _notify_phase(phase_callback, "finalizing")
    return marked_candidates, metadata

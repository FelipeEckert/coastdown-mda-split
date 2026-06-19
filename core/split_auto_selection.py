# coding: utf-8
"""Pure orchestration for exact automatic Split pair selection."""

from __future__ import annotations

from core.split_candidate_generation import generate_full_split_candidates_exact
from core.split_selection_algorithms import (
    VALID_ALGORITHMS,
    mark_algorithm_source,
    rank_candidates_by_energy,
    rank_candidates_by_target,
    select_top_k_candidates,
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


def _warnings(*sources) -> list[str]:
    warnings = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        warnings.extend(source.get("warnings") or [])
    return list(dict.fromkeys(str(warning) for warning in warnings if str(warning).strip()))


def _empty_selection_metadata(k: int, avoid_repeated_runs: bool) -> dict:
    return {
        "requested_k": k,
        "selected_count": 0,
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "skipped_repeated_count": 0,
        "skipped_invalid_usage_count": 0,
        "warnings": [],
    }


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
    progress_callback=None,
    candidate_builder=None,
) -> tuple[list[dict], dict]:
    """Run exact automatic Split candidate generation, ranking and diagnostics."""
    algorithm_name = _algorithm_name(algorithm)
    requested = _requested_k(k)

    candidates, generation_metadata = generate_full_split_candidates_exact(
        split_parsed_runs,
        vehicle_data=vehicle_data,
        correction_context=correction_context,
        candidate_builder=candidate_builder,
        max_combinations=max_combinations,
        progress_callback=progress_callback,
    )

    metadata = {
        "mode": "exact",
        "algorithm": algorithm_name,
        "requested_k": requested,
        "generated_count": len(candidates),
        "ranked_count": 0,
        "selected_count": 0,
        "avoid_repeated_runs": bool(avoid_repeated_runs),
        "generation": generation_metadata,
        "selection": _empty_selection_metadata(requested, avoid_repeated_runs),
        "time_validation": None,
        "warnings": _warnings(generation_metadata),
    }

    if not candidates:
        metadata["warnings"] = _warnings(
            generation_metadata,
            {"warnings": ["No candidates were generated for automatic selection."]},
        )
        return [], metadata

    if algorithm_name == "energy":
        ranked_candidates = rank_candidates_by_energy(candidates)
    else:
        if target_f0 is None or target_f2 is None:
            raise ValueError("target_f0 and target_f2 are required for target ranking.")
        ranked_candidates = rank_candidates_by_target(candidates, target_f0, target_f2)
    metadata["ranked_count"] = len(ranked_candidates)

    selected_candidates, selection_metadata = select_top_k_candidates(
        ranked_candidates,
        requested,
        avoid_repeated_runs=avoid_repeated_runs,
    )
    marked_candidates = mark_algorithm_source(selected_candidates, algorithm_name)
    time_validation = validate_split_selected_times(marked_candidates)

    metadata.update(
        {
            "selected_count": len(marked_candidates),
            "selection": selection_metadata,
            "time_validation": time_validation,
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
    )
    return marked_candidates, metadata

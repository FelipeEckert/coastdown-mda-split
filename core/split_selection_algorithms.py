# coding: utf-8
"""Pure ranking and top-k helpers for automatic Split pair selection."""

from __future__ import annotations

from copy import deepcopy
import math
import random
import time

from core.split_candidate_set_validation import (
    evaluate_split_constraint_satisfaction,
    normalize_split_time_constraints,
    validate_split_candidate_set,
)
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
        item = candidate.copy()
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


def _iter_candidate_sets(
    candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool,
    should_stop=None,
):
    """Yield ranked combinations, pruning repeated run usage before each leaf.

    `used_runs` only accumulates runs from candidates already placed in the
    partial combination under construction (`selected`), never from the rest
    of the pool. Two pool candidates sharing a physical run is expected and
    normal for a Split cartesian-product pool; only two pairs inside the
    same yielded k-set may never share one.

    This canonical (rank-ascending) traversal order is deterministic and
    exhaustive, but a ranked pool naturally clusters its best-ranked
    candidates around the same few physical runs, which can make this
    specific visiting order take a very long time to reach a single
    complete leaf even when many exist elsewhere in the search space. See
    `_randomized_disjoint_set` for the bounded rescue pass used when this
    search exhausts its time/evaluation budget without a result.
    """
    selected = []

    def visit(start_index: int, used_runs: set):
        if should_stop is not None and should_stop():
            return
        if len(selected) == k:
            yield tuple(selected)
            return
        missing = k - len(selected)
        last_start = len(candidates) - missing
        for index in range(start_index, last_start + 1):
            if should_stop is not None and should_stop():
                return
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


def _randomized_disjoint_set(
    pool: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool,
    rng: random.Random,
) -> list[dict] | None:
    """Return one randomized run-disjoint k-subset of pool, or None.

    A single randomized first-fit pass over a shuffled pool order, with no
    backtracking. Used only as a bounded rescue once the deterministic,
    exhaustive `_iter_candidate_sets` search has used its full time/
    evaluation budget without reaching a single complete leaf - a single
    fixed traversal order can stall deep in conflict-heavy branches even
    when many disjoint k-subsets exist elsewhere in the same pool.
    """
    order = list(range(len(pool)))
    rng.shuffle(order)
    used_runs = set()
    chosen = []
    for index in order:
        candidate = pool[index]
        if avoid_repeated_runs:
            usage = _normalized_run_usage(candidate)
            if usage is None:
                continue
            usage_set = set(usage)
            if used_runs.intersection(usage_set):
                continue
            used_runs.update(usage_set)
        chosen.append(candidate)
        if len(chosen) == k:
            return chosen
    return None


def _constraint_search_pool(
    ranked_candidates: list[dict],
    limit: int,
    *,
    min_run_diversity: int = 1,
) -> tuple[list[dict], dict, int]:
    """Return a unique ranked prefix plus original zero-based rank indices.

    The prefix normally stops at `limit`, but is extended past it while any
    Split component (high+/low+/high-/low-) has fewer than
    `min_run_diversity` distinct physical runs among the candidates
    collected so far. A low-energy/low-error ranking naturally clusters
    around the same few best runs in one or more components, so a
    fixed-size prefix can otherwise contain too few distinct runs in some
    slot to ever assemble `k` mutually run-disjoint sets - making the
    constrained search provably infeasible before it evaluates a single
    complete set.
    """
    valid_candidates = [
        candidate
        for candidate in ranked_candidates or []
        if isinstance(candidate, dict)
    ]
    pool = []
    rank_indices = {}
    duplicate_count = 0
    slot_diversity: list[set] | None = None

    for rank_index, candidate in enumerate(valid_candidates):
        signature = _signature_sort_key(candidate)
        if signature in rank_indices:
            duplicate_count += 1
            continue
        rank_indices[signature] = rank_index

        if len(pool) >= limit:
            diversity_sufficient = slot_diversity is not None and all(
                len(slot_set) >= min_run_diversity for slot_set in slot_diversity
            )
            if diversity_sufficient:
                break

        pool.append(candidate)
        usage = _normalized_run_usage(candidate)
        if usage is not None:
            if slot_diversity is None:
                slot_diversity = [set() for _ in usage]
            for slot_set, identity in zip(slot_diversity, usage):
                slot_set.add(identity)

    return pool, rank_indices, duplicate_count


def _candidate_set_rank_score(
    candidate_set: tuple[dict, ...],
    rank_indices: dict,
) -> tuple[int, tuple[int, ...]]:
    indices = tuple(
        rank_indices[_signature_sort_key(candidate)]
        for candidate in candidate_set
    )
    return sum(indices), indices


def select_top_k_candidates_with_constraints_v2(
    ranked_candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool = True,
    require_coefficient_cv: bool = False,
    require_time_cv: bool = True,
    require_opposite_time_difference: bool = True,
    coefficient_cv_limit_pct: float = 10.0,
    time_cv_limit_pct: float = 2.5,
    opposite_time_limit_pct: float = 10.0,
    search_pool_size: int | None = None,
    max_set_evaluations: int = 3000,
    max_search_seconds: float = 30.0,
) -> tuple[list[dict], dict]:
    """Find valid sets first, then choose the best aggregate ranking score."""
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
    search_seconds = _finite_float(max_search_seconds)
    if search_seconds is None or search_seconds <= 0:
        raise ValueError("max_search_seconds must be a positive finite number.")

    default_pool_size = max(80, requested_k * 20, requested_k + 40)
    if search_pool_size is None:
        requested_pool_size = default_pool_size
    else:
        try:
            requested_pool_size = int(search_pool_size)
        except (TypeError, ValueError) as exc:
            raise ValueError("search_pool_size must be a positive integer.") from exc
        if requested_pool_size <= 0:
            raise ValueError("search_pool_size must be greater than zero.")

    search_started = time.perf_counter()
    candidates = [
        candidate
        for candidate in ranked_candidates or []
        if isinstance(candidate, dict)
    ]
    pool, rank_indices, duplicate_count = _constraint_search_pool(
        candidates,
        requested_pool_size,
        min_run_diversity=(
            max(3 * requested_k, requested_k + 10) if avoid_repeated_runs else 1
        ),
    )
    enabled = normalize_split_time_constraints({
        "time_cv": bool(require_time_cv),
        "opposite_time_difference": bool(require_opposite_time_difference),
    })
    fallback_candidates, _ = select_top_k_candidates(
        candidates,
        requested_k,
        avoid_repeated_runs=avoid_repeated_runs,
    )
    metadata = {
        "strategy": "constraint_first_v2",
        "requested_k": requested_k,
        "selected_count": 0,
        "constraints_enabled": enabled,
        "constraints_satisfied": False,
        "evaluated_sets_count": 0,
        "search_pool_size": len(pool),
        "requested_pool_size": requested_pool_size,
        "pool_expanded_for_run_diversity": len(pool) > min(requested_pool_size, len(candidates)),
        "valid_sets_found": 0,
        "max_set_evaluations_reached": False,
        "elapsed_seconds": 0.0,
        "max_search_seconds": search_seconds,
        "timeout_reached": False,
        "best_valid_score": None,
        "best_failed_score": None,
        "duplicate_candidates_skipped": duplicate_count,
        "fallback_used": False,
        "best_failed_validation": None,
        "fallback_candidates": list(fallback_candidates),
        "warnings": [],
    }

    if len(candidates) > requested_pool_size:
        metadata["warnings"].append(
            f"Constraint search used {len(pool)} of {len(candidates)} ranked candidates."
        )
    if metadata["pool_expanded_for_run_diversity"]:
        metadata["warnings"].append(
            f"Search pool was expanded from {requested_pool_size} to {len(pool)} "
            f"ranked candidates to guarantee at least {requested_k} distinct runs "
            "per Split component."
        )
    if duplicate_count:
        metadata["warnings"].append(
            f"{duplicate_count} duplicate ranked candidate(s) were ignored."
        )

    if len(pool) < requested_k:
        metadata["warnings"].append(
            f"Search pool has only {len(pool)} candidates for {requested_k} requested."
        )
        return [], metadata

    best_valid = None
    best_valid_key = None
    best_valid_status = None
    best_valid_validation = None
    best_failed_key = None
    best_failed_candidates = None
    best_failed_validation = None

    def search_timed_out() -> bool:
        return time.perf_counter() - search_started >= search_seconds

    def search_should_stop() -> bool:
        return (
            metadata["evaluated_sets_count"] >= evaluation_limit
            or search_timed_out()
        )

    candidate_sets = _iter_candidate_sets(
        pool,
        requested_k,
        avoid_repeated_runs=avoid_repeated_runs,
        should_stop=search_should_stop,
    )
    for candidate_set in candidate_sets:
        if metadata["evaluated_sets_count"] >= evaluation_limit:
            metadata["max_set_evaluations_reached"] = True
            break
        if search_timed_out():
            metadata["timeout_reached"] = True
            break
        validation = validate_split_candidate_set(
            list(candidate_set),
            coefficient_cv_limit_pct=coefficient_cv_limit_pct,
            time_cv_limit_pct=time_cv_limit_pct,
            opposite_time_limit_pct=opposite_time_limit_pct,
        )
        metadata["evaluated_sets_count"] += 1
        constraint_satisfaction = evaluate_split_constraint_satisfaction(
            validation,
            enabled,
        )
        score_key = _candidate_set_rank_score(candidate_set, rank_indices)
        if constraint_satisfaction is not False:
            metadata["valid_sets_found"] += 1
            if best_valid_key is None or score_key < best_valid_key:
                best_valid = list(candidate_set)
                best_valid_key = score_key
                best_valid_status = constraint_satisfaction
                best_valid_validation = validation
            continue
        if best_failed_key is None or score_key < best_failed_key:
            best_failed_key = score_key
            best_failed_candidates = list(candidate_set)
            best_failed_validation = validation

    metadata["elapsed_seconds"] = time.perf_counter() - search_started
    if metadata["evaluated_sets_count"] >= evaluation_limit:
        metadata["max_set_evaluations_reached"] = True
    if metadata["elapsed_seconds"] >= search_seconds:
        metadata["timeout_reached"] = True
    if metadata["max_set_evaluations_reached"]:
        metadata["warnings"].append(
            f"Search stopped after max_set_evaluations={evaluation_limit}."
        )
    if metadata["timeout_reached"]:
        metadata["warnings"].append(
            f"Search stopped after max_search_seconds={search_seconds:.3f}."
        )

    rescue_metadata = {
        "attempted": False,
        "evaluations": 0,
        "found_valid_set": False,
        "elapsed_seconds": 0.0,
    }
    if (
        best_valid is None
        and avoid_repeated_runs
        and metadata["evaluated_sets_count"] == 0
        and (metadata["timeout_reached"] or metadata["max_set_evaluations_reached"])
    ):
        rescue_metadata["attempted"] = True
        rescue_started = time.perf_counter()
        rescue_time_budget = max(1.0, min(3.0, search_seconds))
        rescue_max_attempts = 500
        rng = random.Random(0)
        evaluated_signatures = set()
        attempts = 0
        while (
            attempts < rescue_max_attempts
            and metadata["evaluated_sets_count"] < evaluation_limit
            and time.perf_counter() - rescue_started < rescue_time_budget
        ):
            attempts += 1
            candidate_set = _randomized_disjoint_set(
                pool,
                requested_k,
                avoid_repeated_runs=avoid_repeated_runs,
                rng=rng,
            )
            if candidate_set is None:
                continue
            candidate_set = tuple(candidate_set)
            signature = frozenset(
                _signature_sort_key(candidate) for candidate in candidate_set
            )
            if signature in evaluated_signatures:
                continue
            evaluated_signatures.add(signature)
            validation = validate_split_candidate_set(
                list(candidate_set),
                coefficient_cv_limit_pct=coefficient_cv_limit_pct,
                time_cv_limit_pct=time_cv_limit_pct,
                opposite_time_limit_pct=opposite_time_limit_pct,
            )
            metadata["evaluated_sets_count"] += 1
            rescue_metadata["evaluations"] += 1
            constraint_satisfaction = evaluate_split_constraint_satisfaction(
                validation,
                enabled,
            )
            score_key = _candidate_set_rank_score(candidate_set, rank_indices)
            if constraint_satisfaction is not False:
                metadata["valid_sets_found"] += 1
                if best_valid_key is None or score_key < best_valid_key:
                    best_valid = list(candidate_set)
                    best_valid_key = score_key
                    best_valid_status = constraint_satisfaction
                    best_valid_validation = validation
                rescue_metadata["found_valid_set"] = True
                break
            if best_failed_key is None or score_key < best_failed_key:
                best_failed_key = score_key
                best_failed_candidates = list(candidate_set)
                best_failed_validation = validation
        rescue_metadata["elapsed_seconds"] = time.perf_counter() - rescue_started
        metadata["elapsed_seconds"] += rescue_metadata["elapsed_seconds"]
        if rescue_metadata["found_valid_set"]:
            metadata["warnings"].append(
                "A valid set was found by a bounded randomized rescue pass "
                "after the exhaustive search used its full time/evaluation "
                "budget without reaching a complete set."
            )
    metadata["rescue"] = rescue_metadata

    if best_valid is not None:
        metadata.update(
            {
                "selected_count": len(best_valid),
                "constraints_satisfied": best_valid_status,
                "best_valid_score": best_valid_key[0],
                "fallback_candidates": [],
                "validation": best_valid_validation,
            }
        )
        return best_valid, metadata

    if len(fallback_candidates) < requested_k and best_failed_candidates is not None:
        fallback_candidates = best_failed_candidates
    metadata["fallback_candidates"] = list(fallback_candidates)
    metadata["best_failed_validation"] = best_failed_validation
    if fallback_candidates:
        try:
            metadata["best_failed_score"] = _candidate_set_rank_score(
                tuple(fallback_candidates),
                rank_indices,
            )[0]
        except KeyError:
            metadata["best_failed_score"] = None

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


def select_top_k_candidates_with_constraints(
    ranked_candidates: list[dict],
    k: int,
    *,
    avoid_repeated_runs: bool = True,
    require_coefficient_cv: bool = False,
    require_time_cv: bool = True,
    require_opposite_time_difference: bool = True,
    coefficient_cv_limit_pct: float = 10.0,
    time_cv_limit_pct: float = 2.5,
    opposite_time_limit_pct: float = 10.0,
    search_pool_size: int | None = None,
    max_set_evaluations: int = 3000,
    max_search_seconds: float = 30.0,
) -> tuple[list[dict], dict]:
    """Compatibility wrapper for the constraint-first v2 selector."""
    return select_top_k_candidates_with_constraints_v2(
        ranked_candidates,
        k,
        avoid_repeated_runs=avoid_repeated_runs,
        require_coefficient_cv=require_coefficient_cv,
        require_time_cv=require_time_cv,
        require_opposite_time_difference=require_opposite_time_difference,
        coefficient_cv_limit_pct=coefficient_cv_limit_pct,
        time_cv_limit_pct=time_cv_limit_pct,
        opposite_time_limit_pct=opposite_time_limit_pct,
        search_pool_size=search_pool_size,
        max_set_evaluations=max_set_evaluations,
        max_search_seconds=max_search_seconds,
    )


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

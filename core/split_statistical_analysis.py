# coding: utf-8
"""Pure run-level candidate grouping for Split statistical analysis."""

from __future__ import annotations

import math

import numpy as np

from core.split_comparison import group_split_records_by_direction
from core.split_time_validation import TIME_COMPONENTS, validate_split_selected_times


MIN_CANDIDATE_GROUP_SIZE = 5
_EPSILON = 1e-12


def _finite_positive(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _feature_vector(record: dict) -> tuple[tuple[str, ...], tuple[float, ...]] | None:
    labels = record.get("subintervals") if isinstance(record, dict) else None
    values = record.get("subinterval_times_s") if isinstance(record, dict) else None
    if not isinstance(labels, (list, tuple)) or not isinstance(values, (list, tuple)):
        return None
    if not labels or len(labels) != len(values):
        return None

    feature_labels = tuple(str(label) for label in labels)
    feature_values = tuple(_finite_positive(value) for value in values)
    if len(set(feature_labels)) != len(feature_labels) or any(
        value is None for value in feature_values
    ):
        return None
    return feature_labels, feature_values


def build_split_run_feature_vectors(records: list[dict]) -> dict:
    """Project canonical parsed subinterval times into one aligned run matrix."""
    feature_labels = None
    runs = []
    warnings = []
    for source_index, record in enumerate(records or []):
        vector = _feature_vector(record)
        run_id = record.get("run_id") if isinstance(record, dict) else None
        if vector is None:
            warnings.append(f"Run {run_id or source_index + 1} has invalid subinterval times.")
            continue
        labels, values = vector
        if feature_labels is None:
            feature_labels = labels
        if labels != feature_labels:
            warnings.append(f"Run {run_id or source_index + 1} has incompatible subintervals.")
            continue
        runs.append(
            {
                "source_index": source_index,
                "run_id": run_id,
                "filename": record.get("filename"),
                "source_role": record.get("source_role"),
                "delta_t_s": record.get("delta_t_s"),
                "features_s": values,
            }
        )

    if not runs:
        return {
            "feature_labels": tuple(),
            "runs": tuple(),
            "warnings": tuple(warnings),
        }

    matrix = np.asarray([run["features_s"] for run in runs], dtype=float)
    means = matrix.mean(axis=0)
    stdevs = matrix.std(axis=0)
    divisors = np.where(stdevs <= _EPSILON, 1.0, stdevs)
    normalized = (matrix - means) / divisors
    projected_runs = tuple(
        run | {"normalized_features": tuple(normalized[index].tolist())}
        for index, run in enumerate(runs)
    )
    return {
        "feature_labels": feature_labels,
        "feature_means_s": tuple(means.tolist()),
        "feature_stdevs_s": tuple(stdevs.tolist()),
        "runs": projected_runs,
        "warnings": tuple(warnings),
    }


def _complete_linkage_hierarchy(
    matrix: np.ndarray,
) -> tuple[list[tuple[float, tuple[tuple[int, ...], ...]]], np.ndarray]:
    """Return deterministic complete-linkage partitions at each merge distance."""
    count = len(matrix)
    if count < 2:
        return [], np.empty((count, count))

    feature_count = matrix.shape[1]
    point_distances = (
        np.linalg.norm(matrix[:, None] - matrix[None, :], axis=2)
        / math.sqrt(feature_count)
    )
    clusters = [(index,) for index in range(count)]
    levels = []
    level_distance = None
    # ponytail: cubic scan is simplest for run-sized populations; use SciPy if
    # measured populations grow large enough for clustering to become material.
    while len(clusters) > 1:
        candidates = (
            (
                max(point_distances[left, right] for left in first for right in second),
                first,
                second,
            )
            for first_index, first in enumerate(clusters)
            for second in clusters[first_index + 1 :]
        )
        distance, first, second = min(candidates)
        distance = float(distance)
        if level_distance is not None and not math.isclose(
            distance,
            level_distance,
            rel_tol=0.0,
            abs_tol=_EPSILON,
        ):
            levels.append((level_distance, tuple(clusters)))
        clusters.remove(first)
        clusters.remove(second)
        clusters.append(tuple(sorted(first + second)))
        clusters.sort()
        level_distance = distance
    levels.append((level_distance, tuple(clusters)))
    return levels, point_distances


def _normative_cv(component: str, records: tuple[dict, ...], cv_limit_pct: float) -> dict:
    validation = validate_split_selected_times(
        [{component: record} for record in records],
        cv_limit_pct=cv_limit_pct,
    )
    return {
        **validation["groups"][component],
        "limit_pct": validation["cv_limit_pct"],
    }


def _analyze_population(
    component: str,
    records: list[dict],
    *,
    cv_limit_pct: float,
) -> dict:
    features = build_split_run_feature_vectors(records)
    usable_records = tuple(records[run["source_index"]] for run in features["runs"])
    matrix = np.asarray(
        [run["normalized_features"] for run in features["runs"]],
        dtype=float,
    )
    hierarchy, point_distances = _complete_linkage_hierarchy(matrix)
    candidate_groups = []
    seen = set()
    for _, clusters in hierarchy:
        for members in clusters:
            if len(members) < MIN_CANDIDATE_GROUP_SIZE or members in seen:
                continue
            seen.add(members)
            group_records = tuple(usable_records[index] for index in members)
            normative = _normative_cv(component, group_records, cv_limit_pct)
            candidate_groups.append(
                {
                    "id": f"{component}_{len(candidate_groups) + 1}",
                    "population": component,
                    "run_ids": tuple(
                        features["runs"][index]["run_id"] for index in members
                    ),
                    "size": len(members),
                    "mean_delta_t_s": normative["mean"],
                    "sample_stdev_s": normative["stdev"],
                    "cv_pct": normative["cv_pct"],
                    "cv_conforming": normative["passed"],
                    "cv_limit_pct": normative["limit_pct"],
                    "cohesion_distance": max(
                        float(point_distances[left, right])
                        for left in members
                        for right in members
                    ),
                    "runs": tuple(features["runs"][index] for index in members),
                }
            )
    return {
        "input_count": len(records or []),
        "usable_run_count": len(features["runs"]),
        **features,
        "candidate_groups": tuple(candidate_groups),
    }


def _compatibility_sort_key(combination: dict) -> tuple:
    opposite_status = {True: 0, False: 1, None: 2}[
        combination["opposite_conforming"]
    ]
    difference = combination["opposite_difference_pct"]
    return (
        opposite_status,
        0 if combination["both_directional_cvs_conforming"] else 1,
        math.inf if difference is None else difference,
        -combination["usable_run_count"],
        combination["cohesion_distance"],
        combination["plus_cohesion_distance"]
        + combination["minus_cohesion_distance"],
        combination["plus_candidate_id"],
        combination["minus_candidate_id"],
    )


def _opposite_direction_combinations(
    interval: str,
    plus_groups: tuple[dict, ...],
    minus_groups: tuple[dict, ...],
    *,
    opposite_mean_limit_pct: float,
) -> tuple[dict, ...]:
    plus_component = f"{interval}_plus"
    minus_component = f"{interval}_minus"
    combinations = []
    for plus_group in plus_groups:
        if plus_group["size"] < MIN_CANDIDATE_GROUP_SIZE:
            continue
        for minus_group in minus_groups:
            if minus_group["size"] < MIN_CANDIDATE_GROUP_SIZE:
                continue
            validation = validate_split_selected_times(
                [
                    *({plus_component: run} for run in plus_group["runs"]),
                    *({minus_component: run} for run in minus_group["runs"]),
                ],
                cv_limit_pct=plus_group["cv_limit_pct"],
                opposite_mean_limit_pct=opposite_mean_limit_pct,
            )
            plus_cv = validation["groups"][plus_component]
            minus_cv = validation["groups"][minus_component]
            opposite = validation["opposite_direction"][interval]
            plus_cohesion = plus_group["cohesion_distance"]
            minus_cohesion = minus_group["cohesion_distance"]
            combinations.append(
                {
                    "id": f"{plus_group['id']}__{minus_group['id']}",
                    "interval": interval,
                    "plus_candidate_id": plus_group["id"],
                    "plus_run_ids": plus_group["run_ids"],
                    "plus_size": plus_group["size"],
                    "plus_mean_delta_t_s": plus_cv["mean"],
                    "plus_cv_pct": plus_cv["cv_pct"],
                    "plus_cv_conforming": plus_cv["passed"],
                    "plus_cohesion_distance": plus_cohesion,
                    "minus_candidate_id": minus_group["id"],
                    "minus_run_ids": minus_group["run_ids"],
                    "minus_size": minus_group["size"],
                    "minus_mean_delta_t_s": minus_cv["mean"],
                    "minus_cv_pct": minus_cv["cv_pct"],
                    "minus_cv_conforming": minus_cv["passed"],
                    "minus_cohesion_distance": minus_cohesion,
                    "both_directional_cvs_conforming": (
                        plus_cv["passed"] is True and minus_cv["passed"] is True
                    ),
                    "opposite_difference_pct": opposite["diff_pct"],
                    "opposite_conforming": opposite["passed"],
                    "opposite_limit_pct": validation["opposite_mean_limit_pct"],
                    "usable_run_count": plus_group["size"] + minus_group["size"],
                    "cohesion_distance": max(plus_cohesion, minus_cohesion),
                }
            )
    combinations.sort(key=_compatibility_sort_key)
    return tuple(
        combination | {"rank": rank}
        for rank, combination in enumerate(combinations, start=1)
    )


def analyze_split_statistical_candidates(
    parsed_runs: dict,
    *,
    cv_limit_pct: float = 2.5,
    opposite_mean_limit_pct: float = 10.0,
) -> dict:
    """Analyze High+/High-/Low+/Low- runs independently without selecting pairs."""
    source = parsed_runs if isinstance(parsed_runs, dict) else {}
    grouped = group_split_records_by_direction(
        source.get("high") or [],
        source.get("low") or [],
    )
    populations = {
        component: _analyze_population(
            component,
            grouped[component],
            cv_limit_pct=cv_limit_pct,
        )
        for component in TIME_COMPONENTS
    }
    opposite_combinations = {
        interval: _opposite_direction_combinations(
            interval,
            populations[f"{interval}_plus"]["candidate_groups"],
            populations[f"{interval}_minus"]["candidate_groups"],
            opposite_mean_limit_pct=opposite_mean_limit_pct,
        )
        for interval in ("high", "low")
    }
    return {
        "method": "complete_linkage",
        "normalization": "population_z_score",
        "distance_metric": "euclidean_over_sqrt_feature_count",
        "minimum_group_size": MIN_CANDIDATE_GROUP_SIZE,
        "populations": populations,
        "candidate_groups": tuple(
            group
            for component in TIME_COMPONENTS
            for group in populations[component]["candidate_groups"]
        ),
        "opposite_direction_combinations": opposite_combinations,
        "invalid_direction_count": len(grouped["invalid"]),
    }

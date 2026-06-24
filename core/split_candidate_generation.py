# coding: utf-8
"""Pure exact candidate generation for automatic Split pair selection."""

from __future__ import annotations

import itertools
import math
import statistics

from core.split_pair_candidate import build_algorithm_split_pair_candidate


GROUP_KEYS = ("high_plus", "low_plus", "high_minus", "low_minus")


def _heading(record: dict) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("heading")
    if value in (None, ""):
        value = record.get("Heading")
    if value in (None, ""):
        value = record.get("direction")
    if value in (None, ""):
        value = record.get("Direction")
    text = str(value or "").strip()
    return text if text in ("+", "-") else None


def _record_label(record: dict, fallback_index: int) -> str:
    if not isinstance(record, dict):
        return f"record {fallback_index}"
    filename = record.get("filename") or "unknown file"
    run_id = record.get("run_id")
    run_text = f"run {run_id}" if run_id not in (None, "") else f"record {fallback_index}"
    return f"{filename} {run_text}"


def _sort_key(record: dict) -> tuple:
    source = record if isinstance(record, dict) else {}

    def normalized(value):
        if value is None:
            return ""
        return str(value)

    delta_t = source.get("delta_t_s")
    try:
        delta_value = float(delta_t)
    except (TypeError, ValueError):
        delta_value = float("inf")
    return (
        normalized(source.get("source_role")),
        normalized(source.get("filename")),
        normalized(source.get("run_id")),
        normalized(source.get("interval_name")),
        delta_value,
    )


def _valid_delta_t(record: dict) -> float | None:
    if not isinstance(record, dict):
        return None
    try:
        value = float(record.get("delta_t_s"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def filter_group_by_mad(
    records: list[dict],
    *,
    mad_multiplier: float = 2.5,
    min_pool_size: int = 4,
) -> tuple[list[dict], dict]:
    """Remove Δt outliers from a group using MAD (Median Absolute Deviation).

    Returns (filtered_records, metadata). Never reduces the group below
    min_pool_size records.
    """
    source = list(records or [])
    metadata = {
        "input_count": len(source),
        "output_count": len(source),
        "filtered_count": 0,
        "skipped_reason": None,
        "threshold": None,
        "median_delta_t": None,
        "mad": None,
        "mad_multiplier": mad_multiplier,
        "min_pool_size": min_pool_size,
    }

    valid_delta_t_values = [
        value for value in (_valid_delta_t(record) for record in source) if value is not None
    ]

    if len(valid_delta_t_values) < 3:
        metadata["skipped_reason"] = "too_few_records"
        return source, metadata

    median = statistics.median(valid_delta_t_values)
    mad = statistics.median([abs(value - median) for value in valid_delta_t_values])
    metadata["median_delta_t"] = median
    metadata["mad"] = mad

    if mad == 0:
        metadata["skipped_reason"] = "mad_is_zero"
        return source, metadata

    threshold = median + mad_multiplier * mad
    metadata["threshold"] = threshold

    filtered = [
        record
        for record in source
        if (lambda delta: delta is None or delta <= threshold)(_valid_delta_t(record))
    ]

    if len(filtered) < min_pool_size:
        metadata["skipped_reason"] = "min_pool_preserved"
        ordered = sorted(source, key=_sort_key)
        result = ordered[:min_pool_size]
        metadata["output_count"] = len(result)
        metadata["filtered_count"] = len(source) - len(result)
        return result, metadata

    metadata["output_count"] = len(filtered)
    metadata["filtered_count"] = len(source) - len(filtered)
    return filtered, metadata


def split_runs_by_role_and_heading(split_parsed_runs: dict) -> dict:
    """Group parsed Split runs into high/low and plus/minus buckets."""
    source = split_parsed_runs if isinstance(split_parsed_runs, dict) else {}
    grouped = {key: [] for key in GROUP_KEYS}
    grouped["warnings"] = list(source.get("warnings") or [])

    for role in ("high", "low"):
        records = source.get(role) or []
        for index, record in enumerate(records, start=1):
            heading = _heading(record)
            if heading == "+":
                grouped[f"{role}_plus"].append(record)
            elif heading == "-":
                grouped[f"{role}_minus"].append(record)
            else:
                grouped["warnings"].append(
                    f"Ignored {role} {_record_label(record, index)} with invalid heading."
                )

    for key in GROUP_KEYS:
        grouped[key] = sorted(grouped[key], key=_sort_key)
    return grouped


def estimate_full_candidate_count(grouped_runs: dict) -> int:
    """Return exact cartesian-product candidate count for grouped Split runs."""
    source = grouped_runs if isinstance(grouped_runs, dict) else {}
    total = 1
    for key in GROUP_KEYS:
        total *= len(source.get(key) or [])
    return total


def iter_full_candidate_run_groups(grouped_runs: dict):
    """Yield complete high+/low+/high-/low- run groups in stable order."""
    source = grouped_runs if isinstance(grouped_runs, dict) else {}
    groups = [
        sorted(source.get(key) or [], key=_sort_key)
        for key in GROUP_KEYS
    ]
    for high_plus, low_plus, high_minus, low_minus in itertools.product(*groups):
        yield {
            "high_plus_run": high_plus,
            "low_plus_run": low_plus,
            "high_minus_run": high_minus,
            "low_minus_run": low_minus,
        }


def _group_counts(grouped_runs: dict) -> dict:
    return {
        key: len((grouped_runs or {}).get(key) or [])
        for key in GROUP_KEYS
    }


def generate_full_split_candidates_exact(
    split_parsed_runs: dict,
    *,
    vehicle_data: dict,
    correction_context: dict | None = None,
    candidate_builder=None,
    max_combinations: int | None = None,
    progress_callback=None,
    use_mad_prefilter: bool = True,
    mad_multiplier: float = 2.5,
    mad_min_pool_size: int = 4,
) -> tuple[list[dict], dict]:
    """Generate exact complete Split candidates by cartesian product."""
    builder = candidate_builder or build_algorithm_split_pair_candidate
    grouped = split_runs_by_role_and_heading(split_parsed_runs)

    prefilter_metadata = {}
    if use_mad_prefilter:
        for key in GROUP_KEYS:
            filtered, filter_meta = filter_group_by_mad(
                grouped[key],
                mad_multiplier=mad_multiplier,
                min_pool_size=mad_min_pool_size,
            )
            grouped[key] = filtered
            prefilter_metadata[key] = filter_meta

    estimated_total = estimate_full_candidate_count(grouped)
    metadata = {
        "mode": "exact",
        "estimated_total": estimated_total,
        "attempted_count": 0,
        "generated_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "group_counts": _group_counts(grouped),
        "prefilter_applied": use_mad_prefilter,
        "prefilter": prefilter_metadata,
        "warnings": list(grouped.get("warnings") or []),
    }

    if estimated_total == 0:
        metadata["warnings"].append(
            "No complete Split candidate combination is available."
        )
        return [], metadata

    if max_combinations is not None:
        try:
            max_count = int(max_combinations)
        except (TypeError, ValueError):
            max_count = -1
        if max_count < 0:
            metadata["warnings"].append("max_combinations must be non-negative.")
            metadata["skipped_count"] = estimated_total
            return [], metadata
        if estimated_total > max_count:
            metadata["warnings"].append(
                "Total estimated candidates exceeds max_combinations."
            )
            metadata["skipped_count"] = estimated_total
            return [], metadata

    candidates = []
    for run_group in iter_full_candidate_run_groups(grouped):
        metadata["attempted_count"] += 1
        try:
            candidate = builder(
                **run_group,
                vehicle_data=vehicle_data,
                correction_context=correction_context,
            )
        except Exception as exc:  # candidate-level failure must not abort generation
            metadata["failed_count"] += 1
            metadata["warnings"].append(
                f"Candidate {metadata['attempted_count']} failed: {exc}"
            )
        else:
            if isinstance(candidate, dict):
                candidates.append(candidate)
                metadata["generated_count"] += 1
            else:
                metadata["skipped_count"] += 1
                metadata["warnings"].append(
                    f"Candidate {metadata['attempted_count']} was skipped because "
                    "the builder did not return a mapping."
                )
        if progress_callback:
            progress_callback(metadata["attempted_count"] / estimated_total)

    return candidates, metadata

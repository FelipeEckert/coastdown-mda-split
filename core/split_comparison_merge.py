# coding: utf-8
"""Pure merge helpers for algorithmic Split candidates and final comparison."""

from __future__ import annotations

from copy import deepcopy

from core.split_comparison import SELECTION_SOURCE_ALGORITHM
from core.split_pair_candidate import (
    MISSING_IDENTITY_VALUE,
    split_candidate_signature,
)


VALID_ALGORITHM_SOURCES = {"energy", "target"}
COMPONENT_FIELD_CONTRACT = (
    ("high_plus", "high", "+"),
    ("low_plus", "low", "+"),
    ("high_minus", "high", "-"),
    ("low_minus", "low", "-"),
)


def _algorithm_source(value: str) -> str:
    source = str(value or "").strip().lower()
    if source not in VALID_ALGORITHM_SOURCES:
        raise ValueError("algorithm_source must be 'energy' or 'target'.")
    return source


def _identity_value(value):
    if value is None or value == "":
        return MISSING_IDENTITY_VALUE
    return value


def _has_run_usage(pair: dict) -> bool:
    return bool((pair if isinstance(pair, dict) else {}).get("run_usage"))


def _has_component_records(pair: dict) -> bool:
    source = pair if isinstance(pair, dict) else {}
    return any(isinstance(source.get(component), dict) for component, _, _ in COMPONENT_FIELD_CONTRACT)


def _component_field_signature(pair: dict) -> tuple | None:
    source = pair if isinstance(pair, dict) else {}
    identities = []
    has_identity = False
    for component, interval_name, expected_direction in COMPONENT_FIELD_CONTRACT:
        run_id = source.get(f"{component}_run")
        filename = source.get(f"{component}_file")
        direction = source.get(f"{component}_direction") or expected_direction
        timestamp = source.get(f"{component}_timestamp")
        delta_t = source.get(f"{component}_delta_t_s")
        values = (run_id, filename, timestamp, delta_t)
        if any(value not in (None, "") for value in values):
            has_identity = True
        identities.append(
            (
                interval_name,
                direction,
                _identity_value(run_id),
                _identity_value(filename),
                _identity_value(timestamp),
                _identity_value(delta_t),
            )
        )
    if not has_identity:
        return None
    return tuple(identities)


def comparison_pair_signature(pair: dict) -> tuple:
    """
    Return a stable duplicate-detection signature for a Split comparison pair.

    The preferred identity is the automatic-candidate `run_usage`. For older or
    manually created comparison pairs, the helper falls back to embedded
    component records and then to flattened comparison fields.
    """
    source = pair if isinstance(pair, dict) else {}
    if _has_run_usage(source) or _has_component_records(source):
        return split_candidate_signature(source)

    field_signature = _component_field_signature(source)
    if field_signature is not None:
        return field_signature

    pair_id = source.get("pair_id") or source.get("id")
    if pair_id not in (None, ""):
        return ("pair_id", pair_id)
    return ("missing_pair_identity",)


def _source_list(pair: dict, algorithm_source: str) -> list[str]:
    values = []
    for key in ("algorithm_sources", "algorithm_source"):
        current = pair.get(key)
        if isinstance(current, (list, tuple, set)):
            values.extend(current)
        elif current not in (None, ""):
            values.append(current)
    values.append(algorithm_source)

    result = []
    for value in values:
        source = str(value or "").strip().lower()
        if source in VALID_ALGORITHM_SOURCES and source not in result:
            result.append(source)
    return result


def _apply_algorithm_origin(pair: dict, algorithm_source: str) -> tuple[dict, bool]:
    item = dict(pair)
    previous_sources = tuple(item.get("algorithm_sources") or [])
    previous_energy_flag = bool(item.get("selected_by_energy_algo", False))
    previous_target_flag = bool(item.get("selected_by_target_algo", False))
    sources = _source_list(item, algorithm_source)
    item["algorithm_sources"] = sources
    item["algorithm_source"] = algorithm_source
    item["selected_by_energy_algo"] = "energy" in sources
    item["selected_by_target_algo"] = "target" in sources
    changed = (
        previous_sources != tuple(sources)
        or previous_energy_flag != item["selected_by_energy_algo"]
        or previous_target_flag != item["selected_by_target_algo"]
    )
    return item, changed


def _new_algorithm_pair(candidate: dict, algorithm_source: str) -> dict:
    item, _ = _apply_algorithm_origin(dict(candidate), algorithm_source)
    item["selected"] = False
    item["selection_source"] = SELECTION_SOURCE_ALGORITHM
    item["candidate_signature"] = comparison_pair_signature(item)
    return item


def merge_algorithm_candidates_into_comparison_pairs(
    existing_pairs: list[dict],
    algorithm_candidates: list[dict],
    *,
    algorithm_source: str,
) -> tuple[list[dict], dict]:
    """Return comparison pairs enriched with algorithm candidates, without mutation."""
    source = _algorithm_source(algorithm_source)
    output = [deepcopy(pair) for pair in (existing_pairs or []) if isinstance(pair, dict)]
    metadata = {
        "algorithm_source": source,
        "input_existing_count": len(existing_pairs or []),
        "input_candidate_count": len(algorithm_candidates or []),
        "output_count": len(output),
        "added_count": 0,
        "duplicate_count": 0,
        "updated_existing_count": 0,
        "preserved_selected_count": 0,
        "warnings": [],
    }

    signatures = {}
    for index, pair in enumerate(output):
        signature = comparison_pair_signature(pair)
        if signature == ("missing_pair_identity",):
            metadata["warnings"].append("Existing comparison pair has no stable identity.")
        signatures.setdefault(signature, index)

    for candidate in algorithm_candidates or []:
        if not isinstance(candidate, dict):
            metadata["warnings"].append("Ignored non-dict algorithm candidate.")
            continue

        candidate_signature = comparison_pair_signature(candidate)
        if candidate_signature in signatures:
            metadata["duplicate_count"] += 1
            existing_index = signatures[candidate_signature]
            existing_pair = output[existing_index]
            if existing_pair.get("selected", False):
                metadata["preserved_selected_count"] += 1
            updated_pair, changed = _apply_algorithm_origin(existing_pair, source)
            for key in (
                "weather_components",
                "weather_summary",
                "weather_sync",
                "ambient_by_component",
                "environmental_conditions",
            ):
                if key not in updated_pair and key in candidate:
                    updated_pair[key] = deepcopy(candidate[key])
                    changed = True
            candidate_warnings = list(candidate.get("warnings") or [])
            if candidate_warnings:
                merged_warnings = list(
                    dict.fromkeys(list(updated_pair.get("warnings") or []) + candidate_warnings)
                )
                if merged_warnings != list(updated_pair.get("warnings") or []):
                    updated_pair["warnings"] = merged_warnings
                    changed = True
            updated_pair["selected"] = bool(existing_pair.get("selected", False))
            if changed:
                metadata["updated_existing_count"] += 1
            output[existing_index] = updated_pair
            continue

        new_pair = _new_algorithm_pair(deepcopy(candidate), source)
        output.append(new_pair)
        signatures[candidate_signature] = len(output) - 1
        metadata["added_count"] += 1

    metadata["output_count"] = len(output)
    metadata["warnings"] = list(dict.fromkeys(metadata["warnings"]))
    return output, metadata

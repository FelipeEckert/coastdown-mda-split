# coding: utf-8
"""Pure consolidation helpers for final Split comparison pairs."""

from __future__ import annotations

import math
import statistics


FINAL_CV_LIMIT_PERCENT = 10.0


def _finite_float(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _first_number(data: dict, *keys):
    for key in keys:
        number = _finite_float(data.get(key))
        if number is not None:
            return number
    return None


def _warnings(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    try:
        items = list(value)
    except TypeError:
        items = [value]
    return list(
        dict.fromkeys(
            str(item).strip()
            for item in items
            if str(item).strip()
        )
    )


def _sample_cv_percent(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = statistics.mean(values)
    if mean_value == 0:
        return None
    return statistics.stdev(values) / abs(mean_value) * 100.0


def normalize_split_final_pair(pair: dict, index: int = 1) -> dict:
    """Adapt one Split comparison pair to the final-results UI contract."""
    source = pair if isinstance(pair, dict) else {}
    ambient_by_component = dict(
        source.get("ambient_by_component") or {}
    )
    warnings = _warnings(source.get("warnings"))
    for ambient in ambient_by_component.values():
        if isinstance(ambient, dict):
            warnings.extend(_warnings(ambient.get("warnings")))
    warnings = list(dict.fromkeys(warnings))
    normalized = dict(source)
    normalized.update(
        {
            "id": source.get("id") or f"split_pair_{index}",
            "selected": bool(source.get("selected", True)),
            "F0_mean": _first_number(source, "F0_mean", "F0"),
            "F2_mean": _first_number(source, "F2_mean", "F2"),
            "energy": _first_number(source, "energy"),
            "f0_prime_mean": _first_number(
                source,
                "f0_prime_mean",
                "f0_prime",
            ),
            "f2_prime_mean": _first_number(
                source,
                "f2_prime_mean",
                "f2_prime",
            ),
            "warnings": warnings,
            "ambient_by_component": ambient_by_component,
        }
    )
    return normalized


def selected_split_final_pairs(pairs: list[dict] | None) -> list[dict]:
    """Return only pairs selected in the Split Final Comparison."""
    selected = []
    for index, pair in enumerate(pairs or [], start=1):
        if not isinstance(pair, dict) or pair.get("selected") is not True:
            continue
        selected.append(normalize_split_final_pair(pair, index))
    return selected


def consolidate_split_final_results(
    comparison_pairs: list[dict] | None,
) -> dict:
    """Consolidate corrected coefficients from selected Split pairs."""
    selected_pairs = selected_split_final_pairs(comparison_pairs)
    f0_values = [
        pair["F0_mean"]
        for pair in selected_pairs
        if pair["F0_mean"] is not None
    ]
    f2_values = [
        pair["F2_mean"]
        for pair in selected_pairs
        if pair["F2_mean"] is not None
    ]
    energy_values = [
        pair["energy"]
        for pair in selected_pairs
        if pair["energy"] is not None
    ]
    warnings = list(
        dict.fromkeys(
            warning
            for pair in selected_pairs
            for warning in pair["warnings"]
        )
    )

    cv_f0 = _sample_cv_percent(f0_values)
    cv_f2 = _sample_cv_percent(f2_values)
    cv_energy = _sample_cv_percent(energy_values)
    missing_f0 = len(selected_pairs) - len(f0_values)
    missing_f2 = len(selected_pairs) - len(f2_values)
    missing_energy = len(selected_pairs) - len(energy_values)

    if missing_f0 or missing_f2:
        conformity_status = "incomplete"
    elif any(
        value is not None and value > FINAL_CV_LIMIT_PERCENT
        for value in (cv_f0, cv_f2)
    ):
        conformity_status = "nonconforming"
    elif warnings:
        conformity_status = "warning"
    elif cv_f0 is None or cv_f2 is None:
        conformity_status = "not_evaluable"
    else:
        conformity_status = "conforming"

    return {
        "num_pairs": len(selected_pairs),
        "num_results": len(selected_pairs),
        "selected_pairs": selected_pairs,
        "mean_f0": statistics.mean(f0_values) if f0_values else None,
        "mean_f2": statistics.mean(f2_values) if f2_values else None,
        "mean_energy": (
            statistics.mean(energy_values)
            if energy_values
            else None
        ),
        "cv_f0": cv_f0,
        "cv_f2": cv_f2,
        "cv_energy": cv_energy,
        "f0_value_count": len(f0_values),
        "f2_value_count": len(f2_values),
        "energy_value_count": len(energy_values),
        "missing_f0_count": missing_f0,
        "missing_f2_count": missing_f2,
        "missing_energy_count": missing_energy,
        "warnings": warnings,
        "conformity_status": conformity_status,
        "cv_limit_percent": FINAL_CV_LIMIT_PERCENT,
    }

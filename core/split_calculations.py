# coding: utf-8
"""Pure calculation helpers for the Coastdown Split method."""

from __future__ import annotations

import math
from statistics import mean, stdev


DEFAULT_SPLIT_INTERVAL_CONFIG = {
    "high": {"start": 90.0, "end": 70.0, "reference": 80.0},
    "low": {"start": 45.0, "end": 35.0, "reference": 40.0},
}


def kmh_to_ms(value_kmh: float) -> float:
    """Convert speed from km/h to m/s."""
    return float(value_kmh) / 3.6


def delta_v_kmh(start_kmh: float, end_kmh: float) -> float:
    """Return positive Delta V using the Split convention."""
    return abs(float(start_kmh) - float(end_kmh))


def validate_split_inputs(
    effective_mass: float,
    delta_t1_s: float,
    delta_t2_s: float,
    low_start_kmh: float,
    low_end_kmh: float,
    low_reference_kmh: float,
    high_start_kmh: float,
    high_end_kmh: float,
    high_reference_kmh: float,
) -> list[str]:
    """Validate Split calculation inputs and return readable error messages."""
    errors = []

    if effective_mass <= 0:
        errors.append("Me must be greater than zero.")
    if delta_t1_s <= 0:
        errors.append("Delta t1 must be greater than zero.")
    if delta_t2_s <= 0:
        errors.append("Delta t2 must be greater than zero.")
    if high_reference_kmh <= low_reference_kmh:
        errors.append("High reference speed V2 must be greater than low reference speed V1.")
    if delta_v_kmh(low_start_kmh, low_end_kmh) <= 0:
        errors.append("Delta V1 must be greater than zero.")
    if delta_v_kmh(high_start_kmh, high_end_kmh) <= 0:
        errors.append("Delta V2 must be greater than zero.")
    if not (high_start_kmh > high_reference_kmh > high_end_kmh):
        errors.append("High interval must satisfy high_start > high_reference > high_end.")
    if not (low_start_kmh > low_reference_kmh > low_end_kmh):
        errors.append("Low interval must satisfy low_start > low_reference > low_end.")

    return errors


def calculate_split_coefficients(
    effective_mass: float,
    delta_t1_s: float,
    delta_t2_s: float,
    low_start_kmh: float,
    low_end_kmh: float,
    low_reference_kmh: float,
    high_start_kmh: float,
    high_end_kmh: float,
    high_reference_kmh: float,
) -> dict:
    """
    Calculate f'0 and f'2 for one Split calculation.

    V1 is the low reference speed and V2 is the high reference speed.
    Speeds are converted to m/s internally. Delta V is stored as a positive
    interval amplitude, then used in the road-load-positive form of the Split
    equations. This is equivalent to using signed deceleration internally,
    without hiding a final sign flip in the return value.
    """
    errors = validate_split_inputs(
        effective_mass,
        delta_t1_s,
        delta_t2_s,
        low_start_kmh,
        low_end_kmh,
        low_reference_kmh,
        high_start_kmh,
        high_end_kmh,
        high_reference_kmh,
    )
    if errors:
        raise ValueError("; ".join(errors))

    v1 = kmh_to_ms(low_reference_kmh)
    v2 = kmh_to_ms(high_reference_kmh)
    delta_v1 = kmh_to_ms(delta_v_kmh(low_start_kmh, low_end_kmh))
    delta_v2 = kmh_to_ms(delta_v_kmh(high_start_kmh, high_end_kmh))
    a1 = delta_v1 / delta_t1_s
    a2 = delta_v2 / delta_t2_s

    denominator = v2**2 - v1**2
    f0_prime = (effective_mass / denominator) * (
        a1 * v2**2
        - a2 * v1**2
    )
    f2_prime = (effective_mass / denominator) * (
        a2 - a1
    )

    return {
        "f0_prime": f0_prime,
        "f2_prime": f2_prime,
        "effective_mass": effective_mass,
        "delta_t1_s": delta_t1_s,
        "delta_t2_s": delta_t2_s,
        "delta_v1_kmh": delta_v_kmh(low_start_kmh, low_end_kmh),
        "delta_v2_kmh": delta_v_kmh(high_start_kmh, high_end_kmh),
        "v1_reference_kmh": low_reference_kmh,
        "v2_reference_kmh": high_reference_kmh,
    }


def calculate_split_result(high_record: dict, low_record: dict, effective_mass: float, config: dict) -> dict:
    """Build a traceable Split result from one high interval and one low interval."""
    high_cfg = config["high"]
    low_cfg = config["low"]
    result = calculate_split_coefficients(
        effective_mass=effective_mass,
        delta_t1_s=float(low_record["delta_t_s"]),
        delta_t2_s=float(high_record["delta_t_s"]),
        low_start_kmh=float(low_cfg["start"]),
        low_end_kmh=float(low_cfg["end"]),
        low_reference_kmh=float(low_cfg["reference"]),
        high_start_kmh=float(high_cfg["start"]),
        high_end_kmh=float(high_cfg["end"]),
        high_reference_kmh=float(high_cfg["reference"]),
    )
    result.update(
        {
            "high_record": high_record,
            "low_record": low_record,
            "selected": True,
            "valid": True,
            "warnings": list(high_record.get("warnings", [])) + list(low_record.get("warnings", [])),
        }
    )
    return result


def coefficient_summary(results: list[dict]) -> dict:
    """Aggregate selected valid Split results."""
    valid_results = [r for r in results if r.get("valid", True)]
    f0_values = [float(r["f0_prime"]) for r in valid_results if math.isfinite(float(r["f0_prime"]))]
    f2_values = [float(r["f2_prime"]) for r in valid_results if math.isfinite(float(r["f2_prime"]))]

    if not f0_values or not f2_values:
        raise ValueError("No valid Split results to summarize.")

    mean_f0 = mean(f0_values)
    mean_f2 = mean(f2_values)
    return {
        "mean_f0_prime": mean_f0,
        "mean_f2_prime": mean_f2,
        "cv_f0_prime": (stdev(f0_values) / mean_f0 * 100.0) if len(f0_values) > 1 and mean_f0 else 0.0,
        "cv_f2_prime": (stdev(f2_values) / mean_f2 * 100.0) if len(f2_values) > 1 and mean_f2 else 0.0,
        "num_results": len(valid_results),
    }

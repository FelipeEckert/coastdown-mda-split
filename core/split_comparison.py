# coding: utf-8
"""Pure helpers for complete Split ida/volta pairs and comparison items."""

from __future__ import annotations

import math
import statistics
from uuid import uuid4

from core.split_calculations import calculate_split_result
from core.split_corrections import (
    ENERGY_UNAVAILABLE_STATUS,
    normalize_ambient_by_component,
)


COMPLETE_PAIR_COMPONENTS = (
    "high_plus",
    "low_plus",
    "high_minus",
    "low_minus",
)

COMPLETE_PAIR_LABELS = {
    "high_plus": "high-speed ida (+)",
    "low_plus": "low-speed ida (+)",
    "high_minus": "high-speed volta (-)",
    "low_minus": "low-speed volta (-)",
}

EXPECTED_DIRECTIONS = {
    "high_plus": "+",
    "low_plus": "+",
    "high_minus": "-",
    "low_minus": "-",
}

def _record_value(record: dict, key: str):
    return record.get(key) if isinstance(record, dict) else None


def normalized_record_direction(record: dict) -> str | None:
    """Return '+' or '-' only when a parsed record carries an explicit direction."""
    if not isinstance(record, dict):
        return None
    for key in ("heading", "Heading", "direction", "Direction"):
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text in ("+", "-"):
            return text
    return None


def coefficient_variation_percent(first_value, second_value) -> float | None:
    """Return the sample CV for two directional results, or None if undefined."""
    try:
        values = [float(first_value), float(second_value)]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in values):
        return None
    mean_value = statistics.mean(values)
    if mean_value == 0:
        return None
    return statistics.stdev(values) / abs(mean_value) * 100.0


def group_split_records_by_direction(high_records: list[dict], low_records: list[dict]) -> dict:
    """Group parsed Split records by role and explicit ida/volta direction."""
    grouped = {
        "high_plus": [],
        "high_minus": [],
        "low_plus": [],
        "low_minus": [],
        "invalid": [],
    }
    for role, records in (("high", high_records or []), ("low", low_records or [])):
        for record in records:
            direction = normalized_record_direction(record)
            if direction not in ("+", "-"):
                grouped["invalid"].append(record)
                continue
            grouped[f"{role}_{'plus' if direction == '+' else 'minus'}"].append(record)
    return grouped


def validate_complete_split_pair_selection(selection: dict, effective_mass: float | None) -> list[str]:
    """Validate that a complete Split pair has four directional components."""
    errors = []
    for key in COMPLETE_PAIR_COMPONENTS:
        record = selection.get(key)
        if not record:
            errors.append(f"{COMPLETE_PAIR_LABELS[key]} is required.")
            continue
        direction = normalized_record_direction(record)
        if direction != EXPECTED_DIRECTIONS[key]:
            errors.append(
                f"{COMPLETE_PAIR_LABELS[key]} must have direction {EXPECTED_DIRECTIONS[key]}."
            )
    try:
        mass = float(effective_mass)
    except (TypeError, ValueError):
        mass = 0.0
    if mass <= 0:
        errors.append("Effective mass must be greater than zero.")
    return errors


def calculate_complete_split_pair(
    high_plus: dict,
    low_plus: dict,
    high_minus: dict,
    low_minus: dict,
    effective_mass: float,
    config: dict,
) -> dict:
    """Calculate one complete Split ida/volta pair and its arithmetic mean."""
    selection = {
        "high_plus": high_plus,
        "low_plus": low_plus,
        "high_minus": high_minus,
        "low_minus": low_minus,
    }
    errors = validate_complete_split_pair_selection(selection, effective_mass)
    if errors:
        raise ValueError("; ".join(errors))

    result_plus = calculate_split_result(high_plus, low_plus, effective_mass, config)
    result_minus = calculate_split_result(high_minus, low_minus, effective_mass, config)
    f0_pair = (result_plus["f0_prime"] + result_minus["f0_prime"]) / 2.0
    f2_pair = (result_plus["f2_prime"] + result_minus["f2_prime"]) / 2.0
    result_pair_mean = {
        "f0_prime": f0_pair,
        "f2_prime": f2_pair,
        "effective_mass": effective_mass,
        "v1_reference_kmh": result_plus.get("v1_reference_kmh"),
        "v2_reference_kmh": result_plus.get("v2_reference_kmh"),
        "delta_v1_kmh": result_plus.get("delta_v1_kmh"),
        "delta_v2_kmh": result_plus.get("delta_v2_kmh"),
    }
    warnings = []
    for record in selection.values():
        warnings.extend(record.get("warnings", []))
    warnings.extend(result_plus.get("warnings", []))
    warnings.extend(result_minus.get("warnings", []))

    return {
        "schema": "complete_ida_volta_pair_v1",
        "high_plus": high_plus,
        "low_plus": low_plus,
        "high_minus": high_minus,
        "low_minus": low_minus,
        "result_plus": result_plus,
        "result_minus": result_minus,
        "result_pair_mean": result_pair_mean,
        "f0_prime_plus": result_plus["f0_prime"],
        "f2_prime_plus": result_plus["f2_prime"],
        "f0_prime_minus": result_minus["f0_prime"],
        "f2_prime_minus": result_minus["f2_prime"],
        "f0_prime_mean": f0_pair,
        "f2_prime_mean": f2_pair,
        "f0_prime": f0_pair,
        "f2_prime": f2_pair,
        "effective_mass": effective_mass,
        "v1_reference_kmh": result_pair_mean["v1_reference_kmh"],
        "v2_reference_kmh": result_pair_mean["v2_reference_kmh"],
        "delta_v1_kmh": result_pair_mean["delta_v1_kmh"],
        "delta_v2_kmh": result_pair_mean["delta_v2_kmh"],
        "selected": True,
        "valid": True,
        "warnings": warnings,
        # Compatibility aliases for existing summary/export code.
        "high_record": high_plus,
        "low_record": low_plus,
    }


def _weather_summary(
    high_weather: dict | None = None,
    low_weather: dict | None = None,
    weather_records: dict | None = None,
    weather_sync: dict | None = None,
) -> dict:
    if weather_sync:
        records = [
            record
            for record in weather_sync.values()
            if record and record.get("matched")
        ]
        field_names = {
            "temp_c": "temperature",
            "baro_kpa": "pressure",
            "wind_ms": "wind_speed",
        }
    elif weather_records:
        records = [record for record in weather_records.values() if record]
        field_names = {
            "temp_c": "temp_c",
            "baro_kpa": "baro_kpa",
            "wind_ms": "wind_ms",
        }
    else:
        records = [record for record in (high_weather, low_weather) if record]
        field_names = {
            "temp_c": "temp_c",
            "baro_kpa": "baro_kpa",
            "wind_ms": "wind_ms",
        }

    def average(key):
        source_key = field_names[key]
        values = [
            record.get(source_key)
            for record in records
            if isinstance(record.get(source_key), (int, float))
        ]
        return sum(values) / len(values) if values else None

    return {
        "weather_high": high_weather,
        "weather_low": low_weather,
        "weather_records": weather_records or {},
        "weather_sync": weather_sync or {},
        "weather_match_count": len(records),
        "temp_c": average("temp_c"),
        "baro_kpa": average("baro_kpa"),
        "wind_ms": average("wind_ms"),
    }


def _direction_ambient_average(
    ambient_by_component: dict | None,
    components: tuple[str, str],
    key: str,
):
    values = []
    for component in components:
        value = ((ambient_by_component or {}).get(component) or {}).get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return sum(values) / len(values) if values else None


def build_split_comparison_pair(
    result: dict,
    high_weather: dict | None = None,
    low_weather: dict | None = None,
    weather_records: dict | None = None,
    weather_sync: dict | None = None,
    pair_id: str | None = None,
) -> dict:
    """Build one traceable Split comparison item from a calculated result."""
    if result.get("schema") == "complete_ida_volta_pair_v1":
        high_plus = result.get("high_plus") or {}
        low_plus = result.get("low_plus") or {}
        high_minus = result.get("high_minus") or {}
        low_minus = result.get("low_minus") or {}
        result_plus = result.get("result_plus") or {}
        result_minus = result.get("result_minus") or {}
        result_pair_mean = result.get("result_pair_mean") or {}
        corrected_plus = result.get("corrected_result_plus") or {}
        corrected_minus = result.get("corrected_result_minus") or {}
        corrected_pair_mean = result.get("corrected_pair_mean") or {}
        result_weather_sync = weather_sync or result.get("weather_sync") or {}
        source_ambient_by_component = (
            result.get("ambient_by_component")
            or normalize_ambient_by_component(result_weather_sync)
        )
        ambient_by_component = {
            component: dict(source_ambient_by_component.get(component) or {})
            for component in COMPLETE_PAIR_COMPONENTS
        }
        pair = {
            "id": pair_id or f"split_pair_{uuid4().hex[:8]}",
            "high_plus": high_plus,
            "low_plus": low_plus,
            "high_minus": high_minus,
            "low_minus": low_minus,
            "result_plus": result_plus,
            "result_minus": result_minus,
            "result_pair_mean": result_pair_mean,
            "corrected_result_plus": result.get("corrected_result_plus"),
            "corrected_result_minus": result.get("corrected_result_minus"),
            "corrected_pair_mean": result.get("corrected_pair_mean"),
            "high_plus_file": _record_value(high_plus, "filename"),
            "high_plus_run": _record_value(high_plus, "run_id"),
            "high_plus_direction": normalized_record_direction(high_plus),
            "high_plus_delta_t_s": _record_value(high_plus, "delta_t_s"),
            "high_plus_timestamp": _record_value(high_plus, "start_time_str") or _record_value(high_plus, "start_timestamp"),
            "low_plus_file": _record_value(low_plus, "filename"),
            "low_plus_run": _record_value(low_plus, "run_id"),
            "low_plus_direction": normalized_record_direction(low_plus),
            "low_plus_delta_t_s": _record_value(low_plus, "delta_t_s"),
            "low_plus_timestamp": _record_value(low_plus, "start_time_str") or _record_value(low_plus, "start_timestamp"),
            "high_minus_file": _record_value(high_minus, "filename"),
            "high_minus_run": _record_value(high_minus, "run_id"),
            "high_minus_direction": normalized_record_direction(high_minus),
            "high_minus_delta_t_s": _record_value(high_minus, "delta_t_s"),
            "high_minus_timestamp": _record_value(high_minus, "start_time_str") or _record_value(high_minus, "start_timestamp"),
            "low_minus_file": _record_value(low_minus, "filename"),
            "low_minus_run": _record_value(low_minus, "run_id"),
            "low_minus_direction": normalized_record_direction(low_minus),
            "low_minus_delta_t_s": _record_value(low_minus, "delta_t_s"),
            "low_minus_timestamp": _record_value(low_minus, "start_time_str") or _record_value(low_minus, "start_timestamp"),
            "effective_mass": result.get("effective_mass"),
            "v1_reference_kmh": result.get("v1_reference_kmh"),
            "v2_reference_kmh": result.get("v2_reference_kmh"),
            "delta_v1_kmh": result.get("delta_v1_kmh"),
            "delta_v2_kmh": result.get("delta_v2_kmh"),
            "f0_prime_plus": result.get(
                "f0_prime_plus",
                result_plus.get("f0_prime"),
            ),
            "f2_prime_plus": result.get(
                "f2_prime_plus",
                result_plus.get("f2_prime"),
            ),
            "f0_prime_minus": result.get(
                "f0_prime_minus",
                result_minus.get("f0_prime"),
            ),
            "f2_prime_minus": result.get(
                "f2_prime_minus",
                result_minus.get("f2_prime"),
            ),
            "f0_prime_mean": result.get(
                "f0_prime_mean",
                result_pair_mean.get("f0_prime"),
            ),
            "f2_prime_mean": result.get(
                "f2_prime_mean",
                result_pair_mean.get("f2_prime"),
            ),
            "f0_plus": result.get(
                "f0_prime_plus",
                result_plus.get("f0_prime"),
            ),
            "f2_plus": result.get(
                "f2_prime_plus",
                result_plus.get("f2_prime"),
            ),
            "f0_minus": result.get(
                "f0_prime_minus",
                result_minus.get("f0_prime"),
            ),
            "f2_minus": result.get(
                "f2_prime_minus",
                result_minus.get("f2_prime"),
            ),
            "f0_prime": result.get(
                "f0_prime_mean",
                result_pair_mean.get("f0_prime"),
            ),
            "f2_prime": result.get(
                "f2_prime_mean",
                result_pair_mean.get("f2_prime"),
            ),
            "correction_available": bool(result.get("correction_available")),
            "F0_plus": result.get("F0_plus", corrected_plus.get("F0")),
            "F2_plus": result.get("F2_plus", corrected_plus.get("F2")),
            "F0_minus": result.get("F0_minus", corrected_minus.get("F0")),
            "F2_minus": result.get("F2_minus", corrected_minus.get("F2")),
            "F0_mean": result.get("F0_mean", corrected_pair_mean.get("F0")),
            "F2_mean": result.get("F2_mean", corrected_pair_mean.get("F2")),
            "F0": result.get("F0_mean", corrected_pair_mean.get("F0")),
            "F2": result.get("F2_mean", corrected_pair_mean.get("F2")),
            "F0_unit": corrected_pair_mean.get("F0_unit"),
            "F2_unit": corrected_pair_mean.get("F2_unit"),
            "cv_F0_percent": coefficient_variation_percent(
                corrected_plus.get("F0"),
                corrected_minus.get("F0"),
            ),
            "cv_F2_percent": coefficient_variation_percent(
                corrected_plus.get("F2"),
                corrected_minus.get("F2"),
            ),
            "ambient_mode": result.get("ambient_mode"),
            "ambient_source": result.get("ambient_source"),
            "ambient_by_component": ambient_by_component,
            "temp_plus_used": result.get("temp_plus_used"),
            "press_plus_used": result.get("press_plus_used"),
            "temp_minus_used": result.get("temp_minus_used"),
            "press_minus_used": result.get("press_minus_used"),
            "wind_plus_ms": _direction_ambient_average(
                ambient_by_component,
                ("high_plus", "low_plus"),
                "wind_speed_ms",
            ),
            "wind_minus_ms": _direction_ambient_average(
                ambient_by_component,
                ("high_minus", "low_minus"),
                "wind_speed_ms",
            ),
            "energy": result.get("energy"),
            "energy_unit": result.get("energy_unit"),
            "energy_profile": result.get("energy_profile"),
            "energy_origin": result.get("energy_origin"),
            "energy_details": result.get("energy_details"),
            "energy_status": result.get(
                "energy_status",
                ENERGY_UNAVAILABLE_STATUS,
            ),
            "warnings": list(result.get("warnings") or []),
            # Compatibility aliases for existing table/export consumers.
            "high_file": _record_value(high_plus, "filename"),
            "high_run": _record_value(high_plus, "run_id"),
            "high_direction": normalized_record_direction(high_plus),
            "high_delta_t_s": _record_value(high_plus, "delta_t_s"),
            "high_timestamp": _record_value(high_plus, "start_time_str") or _record_value(high_plus, "start_timestamp"),
            "low_file": _record_value(low_plus, "filename"),
            "low_run": _record_value(low_plus, "run_id"),
            "low_direction": normalized_record_direction(low_plus),
            "low_delta_t_s": _record_value(low_plus, "delta_t_s"),
            "low_timestamp": _record_value(low_plus, "start_time_str") or _record_value(low_plus, "start_timestamp"),
        }
        for component in COMPLETE_PAIR_COMPONENTS:
            ambient = ambient_by_component.get(component) or {}
            pair[f"temp_{component}"] = ambient.get("temperature_c")
            pair[f"press_{component}"] = ambient.get("pressure_kpa")
            pair[f"wind_{component}"] = ambient.get("wind_speed_ms")
        weather_summary = _weather_summary(
            weather_records=weather_records,
            weather_sync=result_weather_sync,
        )
        if result.get("correction_available") and weather_summary.get("temp_c") is None:
            temperatures = [
                value
                for value in (
                    result.get("temp_plus_used"),
                    result.get("temp_minus_used"),
                )
                if isinstance(value, (int, float))
            ]
            pressures = [
                value
                for value in (
                    result.get("press_plus_used"),
                    result.get("press_minus_used"),
                )
                if isinstance(value, (int, float))
            ]
            weather_summary["temp_c"] = (
                sum(temperatures) / len(temperatures)
                if temperatures
                else None
            )
            weather_summary["baro_kpa"] = (
                sum(pressures) / len(pressures)
                if pressures
                else None
            )
        pair.update(weather_summary)
        return pair

    high = result.get("high_record") or {}
    low = result.get("low_record") or {}
    pair = {
        "id": pair_id or f"split_pair_{uuid4().hex[:8]}",
        "high_file": _record_value(high, "filename"),
        "high_run": _record_value(high, "run_id"),
        "high_direction": _record_value(high, "heading"),
        "high_delta_t_s": _record_value(high, "delta_t_s"),
        "high_timestamp": _record_value(high, "start_time_str") or _record_value(high, "start_timestamp"),
        "low_file": _record_value(low, "filename"),
        "low_run": _record_value(low, "run_id"),
        "low_direction": _record_value(low, "heading"),
        "low_delta_t_s": _record_value(low, "delta_t_s"),
        "low_timestamp": _record_value(low, "start_time_str") or _record_value(low, "start_timestamp"),
        "effective_mass": result.get("effective_mass"),
        "v1_reference_kmh": result.get("v1_reference_kmh"),
        "v2_reference_kmh": result.get("v2_reference_kmh"),
        "delta_v1_kmh": result.get("delta_v1_kmh"),
        "delta_v2_kmh": result.get("delta_v2_kmh"),
        "f0_prime": result.get("f0_prime"),
        "f2_prime": result.get("f2_prime"),
        "energy": None,
        "energy_unit": None,
        "energy_profile": None,
        "energy_origin": None,
        "energy_status": ENERGY_UNAVAILABLE_STATUS,
        "warnings": list(result.get("warnings") or []),
    }
    pair.update(
        _weather_summary(
            high_weather,
            low_weather,
            weather_records,
            weather_sync,
        )
    )
    return pair


def add_split_comparison_pair(pairs: list[dict], pair: dict) -> list[dict]:
    """Return a new comparison list with one pair appended."""
    return list(pairs or []) + [pair]


def remove_split_comparison_pair(pairs: list[dict], pair_id: str) -> list[dict]:
    """Return a new comparison list without the requested pair id."""
    return [pair for pair in (pairs or []) if pair.get("id") != pair_id]


def clear_split_comparison_pairs() -> list[dict]:
    """Return an empty comparison list."""
    return []

# coding: utf-8
"""Pure helpers for complete Split ida/volta pairs and comparison items."""

from __future__ import annotations

from uuid import uuid4

from core.split_calculations import calculate_split_result


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
) -> dict:
    if weather_records:
        records = [record for record in weather_records.values() if record]
    else:
        records = [record for record in (high_weather, low_weather) if record]

    def average(key):
        values = [record.get(key) for record in records if isinstance(record.get(key), (int, float))]
        return sum(values) / len(values) if values else None

    return {
        "weather_high": high_weather,
        "weather_low": low_weather,
        "weather_records": weather_records or {},
        "temp_c": average("temp_c"),
        "baro_kpa": average("baro_kpa"),
        "wind_ms": average("wind_ms"),
    }


def build_split_comparison_pair(
    result: dict,
    high_weather: dict | None = None,
    low_weather: dict | None = None,
    weather_records: dict | None = None,
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
        pair = {
            "id": pair_id or f"split_pair_{uuid4().hex[:8]}",
            "high_plus": high_plus,
            "low_plus": low_plus,
            "high_minus": high_minus,
            "low_minus": low_minus,
            "result_plus": result_plus,
            "result_minus": result_minus,
            "result_pair_mean": result_pair_mean,
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
            "f0_plus": result_plus.get("f0_prime"),
            "f2_plus": result_plus.get("f2_prime"),
            "f0_minus": result_minus.get("f0_prime"),
            "f2_minus": result_minus.get("f2_prime"),
            "f0_prime": result_pair_mean.get("f0_prime"),
            "f2_prime": result_pair_mean.get("f2_prime"),
            "energy": None,
            "energy_status": "N/A - neutral Split energy calculation not implemented",
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
        pair.update(_weather_summary(weather_records=weather_records))
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
        "energy_status": "N/A - neutral Split energy calculation not implemented",
        "warnings": list(result.get("warnings") or []),
    }
    pair.update(_weather_summary(high_weather, low_weather, weather_records))
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

# coding: utf-8
"""Pure helpers for Split final-comparison pairs."""

from __future__ import annotations

from uuid import uuid4


def _record_value(record: dict, key: str):
    return record.get(key) if isinstance(record, dict) else None


def _weather_summary(high_weather: dict | None = None, low_weather: dict | None = None) -> dict:
    records = [record for record in (high_weather, low_weather) if record]

    def average(key):
        values = [record.get(key) for record in records if isinstance(record.get(key), (int, float))]
        return sum(values) / len(values) if values else None

    return {
        "weather_high": high_weather,
        "weather_low": low_weather,
        "temp_c": average("temp_c"),
        "baro_kpa": average("baro_kpa"),
        "wind_ms": average("wind_ms"),
    }


def build_split_comparison_pair(
    result: dict,
    high_weather: dict | None = None,
    low_weather: dict | None = None,
    pair_id: str | None = None,
) -> dict:
    """Build one traceable Split comparison item from a calculated result."""
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
    pair.update(_weather_summary(high_weather, low_weather))
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

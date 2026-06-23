# coding: utf-8
"""Pure helpers for future automatic Split pair candidates."""

from __future__ import annotations

from copy import deepcopy

from core.split_calculations import DEFAULT_SPLIT_INTERVAL_CONFIG
from core.split_comparison import (
    SELECTION_SOURCE_ALGORITHM,
    build_split_comparison_pair,
    calculate_complete_split_pair,
)
from core.split_corrections import (
    apply_split_pair_correction,
    fixed_ambient_conditions,
    weather_sync_ambient_conditions,
)
from core.split_display import format_split_pair_label
from core.split_weather_context import build_split_candidate_weather_context
from core.split_vehicle_mass import normalize_split_vehicle_mass_data


MISSING_IDENTITY_VALUE = "<missing>"
COMPONENT_CONTRACT = (
    ("high_plus", "high", "+"),
    ("low_plus", "low", "+"),
    ("high_minus", "high", "-"),
    ("low_minus", "low", "-"),
)
SOURCE_HASH_KEYS = (
    "content_sha256",
    "source_content_sha256",
    "source_sha256",
    "file_sha256",
)


def _identity_value(value):
    if value is None or value == "":
        return MISSING_IDENTITY_VALUE
    return value


def _record_hash(record: dict):
    for key in SOURCE_HASH_KEYS:
        value = (record or {}).get(key)
        if value not in (None, ""):
            return value
    return MISSING_IDENTITY_VALUE


def _run_identity(record: dict, interval_name: str, direction: str) -> tuple:
    source = record if isinstance(record, dict) else {}
    return (
        interval_name,
        direction,
        _identity_value(source.get("run_id")),
        _identity_value(source.get("filename")),
        _identity_value(source.get("source_role")),
        _record_hash(source),
    )


def build_split_run_usage(
    *,
    high_plus_run: dict,
    low_plus_run: dict,
    high_minus_run: dict,
    low_minus_run: dict,
) -> tuple:
    """Return a stable four-component identity for one complete Split pair."""
    records = {
        "high_plus": high_plus_run,
        "low_plus": low_plus_run,
        "high_minus": high_minus_run,
        "low_minus": low_minus_run,
    }
    return tuple(
        _run_identity(records.get(component), interval_name, direction)
        for component, interval_name, direction in COMPONENT_CONTRACT
    )


def split_candidate_signature(candidate: dict) -> tuple:
    """Return the duplicate-detection signature for one candidate pair."""
    source = candidate if isinstance(candidate, dict) else {}
    run_usage = source.get("run_usage")
    if run_usage:
        return tuple(tuple(item) for item in run_usage)
    return build_split_run_usage(
        high_plus_run=source.get("high_plus") or {},
        low_plus_run=source.get("low_plus") or {},
        high_minus_run=source.get("high_minus") or {},
        low_minus_run=source.get("low_minus") or {},
    )


def _effective_mass_from_vehicle_data(vehicle_data: dict) -> float:
    mass_data = normalize_split_vehicle_mass_data(vehicle_data)
    mass = mass_data["effective_mass_kg"]
    if mass is not None:
        return mass
    raise ValueError("Effective mass must be provided in vehicle_data.")


def _split_interval_config(correction_context: dict | None) -> dict:
    config = deepcopy(DEFAULT_SPLIT_INTERVAL_CONFIG)
    source = correction_context if isinstance(correction_context, dict) else {}
    override = (
        source.get("config")
        or source.get("split_interval_config")
        or source.get("interval_config")
    )
    if isinstance(override, dict):
        if "step_kmh" in override:
            config["step_kmh"] = override["step_kmh"]
        for interval_name in ("high", "low"):
            if isinstance(override.get(interval_name), dict):
                config[interval_name].update(override[interval_name])
    return config


def _first_present(source: dict, *keys):
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return None


def _ambient_conditions(correction_context: dict | None) -> dict:
    source = correction_context if isinstance(correction_context, dict) else {}
    if "ambient_conditions" in source:
        return source.get("ambient_conditions") or {}
    if "weather_sync" in source:
        return weather_sync_ambient_conditions(source.get("weather_sync") or {})

    temperature = _first_present(
        source,
        "temperature_c",
        "fixed_temperature_c",
        "fixed_temperature",
        "temp_c",
    )
    pressure = _first_present(
        source,
        "pressure_kpa",
        "fixed_pressure_kpa",
        "fixed_pressure",
        "press_kpa",
    )
    if temperature is not None and pressure is not None:
        return fixed_ambient_conditions(temperature, pressure)
    return {}


def build_algorithm_split_pair_candidate(
    *,
    high_plus_run: dict,
    low_plus_run: dict,
    high_minus_run: dict,
    low_minus_run: dict,
    vehicle_data: dict,
    correction_context: dict | None = None,
) -> dict:
    """
    Build one comparison-compatible Split candidate for automatic selection.

    This helper intentionally reuses the manual calculation path and does not
    access Streamlit/session state. Ranking and bulk generation belong to later
    algorithm layers.
    """
    effective_mass = _effective_mass_from_vehicle_data(vehicle_data)
    config = _split_interval_config(correction_context)
    source_context = correction_context if isinstance(correction_context, dict) else {}
    weather_context = None
    if source_context.get("ambient_mode") == "weather_sync":
        weather_context = build_split_candidate_weather_context(
            {
                "high_plus": high_plus_run,
                "low_plus": low_plus_run,
                "high_minus": high_minus_run,
                "low_minus": low_minus_run,
            }
        )
        candidate_context = dict(source_context)
        candidate_context["weather_sync"] = weather_context["weather_sync"]
        ambient_conditions = _ambient_conditions(candidate_context)
    else:
        ambient_conditions = _ambient_conditions(correction_context)
        if source_context.get("ambient_mode") == "fixed":
            ambient_conditions = dict(ambient_conditions)
            ambient_conditions["ambient_source"] = source_context.get(
                "source", "user_fixed_inputs"
            )
            ambient_conditions["warnings"] = list(
                dict.fromkeys(
                    list(ambient_conditions.get("warnings") or [])
                    + list(source_context.get("warnings") or [])
                )
            )

    result = calculate_complete_split_pair(
        high_plus=high_plus_run,
        low_plus=low_plus_run,
        high_minus=high_minus_run,
        low_minus=low_minus_run,
        effective_mass=effective_mass,
        config=config,
    )
    corrected_result = apply_split_pair_correction(result, ambient_conditions)
    pair = build_split_comparison_pair(
        corrected_result,
        pair_id=(
            correction_context.get("pair_id")
            if isinstance(correction_context, dict)
            else None
        ),
        selection_source=SELECTION_SOURCE_ALGORITHM,
    )

    run_usage = build_split_run_usage(
        high_plus_run=high_plus_run,
        low_plus_run=low_plus_run,
        high_minus_run=high_minus_run,
        low_minus_run=low_minus_run,
    )
    pair["selected"] = False
    pair["selection_source"] = SELECTION_SOURCE_ALGORITHM
    pair["run_usage"] = run_usage
    pair["candidate_signature"] = split_candidate_signature(pair)
    pair["pair_label"] = format_split_pair_label(pair)
    if weather_context:
        pair["weather_components"] = weather_context["weather_components"]
        pair["weather_summary"] = weather_context["weather_summary"]
        pair["environmental_conditions"] = deepcopy(ambient_conditions)
        pair["warnings"] = list(
            dict.fromkeys(
                list(pair.get("warnings") or [])
                + list(weather_context["weather_summary"].get("warnings") or [])
            )
        )
    elif source_context.get("ambient_mode") == "fixed":
        pair["environmental_conditions"] = deepcopy(
            source_context.get("environmental_conditions")
            or {
                "mode": "fixed",
                "temperature_c": source_context.get("temperature_c"),
                "pressure_kpa": source_context.get("pressure_kpa"),
                "wind_speed_mps": None,
                "source": source_context.get("source", "user_fixed_inputs"),
            }
        )
        pair["weather_summary"] = deepcopy(
            source_context.get("weather_summary")
            or {
                "mode": "fixed",
                "temperature_c_mean": source_context.get("temperature_c"),
                "pressure_kpa_mean": source_context.get("pressure_kpa"),
                "wind_speed_mps_mean": None,
                "wind_speed_mps_max": None,
                "status": "fixed",
                "warnings": list(source_context.get("warnings") or []),
            }
        )
    return pair

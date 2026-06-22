# coding: utf-8
"""Pure weather synchronization and validation context for Split runs."""

from __future__ import annotations

from copy import deepcopy
import math

from core.weather_sync import sync_weather_to_run


DEFAULT_SPLIT_WEATHER_LIMITS = {
    "wind_speed_max_mps": 3.0,
    "temperature_max_c": 35.0,
}
COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _validated_limits(weather_limits: dict | None) -> dict:
    limits = dict(DEFAULT_SPLIT_WEATHER_LIMITS)
    limits.update(weather_limits or {})
    for key in DEFAULT_SPLIT_WEATHER_LIMITS:
        value = _finite(limits.get(key))
        if value is None or value < 0:
            raise ValueError(f"{key} must be a non-negative finite number.")
        limits[key] = value
    return limits


def build_fixed_split_correction_context(
    temperature_c,
    pressure_kpa,
    *,
    split_interval_config: dict | None = None,
    weather_limits: dict | None = None,
) -> dict:
    """Build the canonical traceable context for user-edited fixed inputs."""
    temperature = _finite(temperature_c)
    pressure = _finite(pressure_kpa)
    if temperature is None or temperature <= -273.15:
        raise ValueError("temperature_c must be finite and above absolute zero.")
    if pressure is None or pressure <= 0:
        raise ValueError("pressure_kpa must be a positive finite number.")
    limits = _validated_limits(weather_limits)
    warnings = []
    if temperature > limits["temperature_max_c"]:
        warnings.append(
            f"Temperatura fixa acima de {limits['temperature_max_c']:g} °C."
        )
    environmental_conditions = {
        "mode": "fixed",
        "temperature_c": temperature,
        "pressure_kpa": pressure,
        "wind_speed_mps": None,
        "source": "user_fixed_inputs",
    }
    weather_summary = {
        "mode": "fixed",
        "temperature_c_mean": temperature,
        "pressure_kpa_mean": pressure,
        "wind_speed_mps_mean": None,
        "wind_speed_mps_max": None,
        "status": "fixed",
        "warnings": warnings,
    }
    return {
        "mode": "fixed",
        "ambient_mode": "fixed",
        "temperature_c": temperature,
        "pressure_kpa": pressure,
        "wind_speed_mps": None,
        "source": "user_fixed_inputs",
        "split_interval_config": deepcopy(split_interval_config or {}),
        "environmental_conditions": environmental_conditions,
        "weather_summary": weather_summary,
        "warnings": warnings,
    }


def split_environmental_values(pair: dict) -> dict:
    """Read canonical Split ambient values, with legacy aliases as fallbacks."""
    source = pair if isinstance(pair, dict) else {}
    temperatures = []
    pressures = []
    winds = []

    def append_value(target: list, mapping: dict, canonical: str, *aliases: str):
        for key in (canonical, *aliases):
            value = _finite(mapping.get(key))
            if value is not None:
                target.append(value)
                return

    ambient = source.get("ambient_by_component") or {}
    for item in ambient.values() if isinstance(ambient, dict) else ():
        if not isinstance(item, dict):
            continue
        append_value(temperatures, item, "temperature_c", "temperature", "temp_c")
        append_value(pressures, item, "pressure_kpa", "pressure", "baro_kpa")
        append_value(winds, item, "wind_speed_mps", "wind_speed_ms", "wind_speed", "wind_ms")

    environmental = source.get("environmental_conditions") or {}
    summary = source.get("weather_summary") or {}
    if not temperatures:
        append_value(temperatures, environmental, "temperature_c", "temperature", "temp_c")
        append_value(temperatures, summary, "temperature_c_mean")
    if not pressures:
        append_value(pressures, environmental, "pressure_kpa", "pressure", "baro_kpa")
        append_value(pressures, summary, "pressure_kpa_mean")
    if not winds:
        append_value(winds, environmental, "wind_speed_mps", "wind_speed_ms", "wind_speed", "wind_ms")
        append_value(winds, summary, "wind_speed_mps_max", "wind_speed_mps_mean")

    for key in ("temp_plus_used", "temp_minus_used", "temp_c"):
        value = _finite(source.get(key))
        if value is not None:
            temperatures.append(value)
    for key in ("press_plus_used", "press_minus_used", "baro_kpa"):
        value = _finite(source.get(key))
        if value is not None:
            pressures.append(value)
    for key in ("wind_plus_mps", "wind_minus_mps", "wind_plus_ms", "wind_minus_ms", "wind_ms"):
        value = _finite(source.get(key))
        if value is not None:
            winds.append(value)

    return {
        "mode": environmental.get("mode") or summary.get("mode") or source.get("ambient_mode"),
        "temperature_c": max(temperatures) if temperatures else None,
        "pressure_kpa": sum(pressures) / len(pressures) if pressures else None,
        "wind_speed_mps": max(winds) if winds else None,
    }


def _run_weather_sync(run: dict, weather_data, max_time_diff_s: float, limits: dict) -> dict:
    sync = sync_weather_to_run(
        run,
        weather_data,
        max_time_delta_seconds=max_time_diff_s,
        allow_time_only_fallback=True,
    )
    item = deepcopy(sync)
    temperature = _finite(sync.get("temperature"))
    pressure = _finite(sync.get("pressure"))
    wind_speed = _finite(sync.get("wind_speed"))
    warnings = list(sync.get("warnings") or [])
    invalid_reasons = []
    missing = not sync.get("matched") or any(
        value is None for value in (temperature, pressure, wind_speed)
    )
    if missing:
        invalid_reasons.append("Meteorologia ausente.")
    if wind_speed is not None and wind_speed > limits["wind_speed_max_mps"]:
        invalid_reasons.append(
            f"Vento acima de {limits['wind_speed_max_mps']:g} m/s."
        )
    if temperature is not None and temperature > limits["temperature_max_c"]:
        invalid_reasons.append(
            f"Temperatura acima de {limits['temperature_max_c']:g} °C."
        )
    warnings.extend(invalid_reasons)
    if missing:
        status = "missing"
    elif invalid_reasons:
        status = "invalid"
    elif warnings:
        status = "warning"
    else:
        status = "ok"
    item.update(
        {
            "temperature_c": temperature,
            "pressure_kpa": pressure,
            "wind_speed_mps": wind_speed,
            "wind_direction_deg": _finite(sync.get("wind_direction")),
            "method": sync.get("sync_method"),
            "time_diff_s": _finite(sync.get("time_delta_seconds")),
            "source_timestamp": sync.get("weather_datetime"),
            "source_file": (
                (sync.get("weather_record") or {}).get("source_file")
                or (sync.get("weather_record") or {}).get("filename")
            ),
            "status": status,
            "invalid_reasons": invalid_reasons,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )
    return item


def synchronize_weather_for_split_runs(
    split_parsed_runs: dict,
    weather_data,
    *,
    max_time_diff_s: float = 300.0,
    weather_limits: dict | None = None,
) -> tuple[dict, dict]:
    """Return copied high/low runs enriched with one weather sync per run."""
    max_delta = _finite(max_time_diff_s)
    if max_delta is None or max_delta < 0:
        raise ValueError("max_time_diff_s must be a non-negative finite number.")
    limits = _validated_limits(weather_limits)
    source = split_parsed_runs if isinstance(split_parsed_runs, dict) else {}
    enriched = deepcopy(source)
    metadata = {
        "high_total": 0,
        "low_total": 0,
        "high_synchronized": 0,
        "low_synchronized": 0,
        "missing_count": 0,
        "wind_above_limit_count": 0,
        "temperature_above_limit_count": 0,
        "max_time_diff_s_found": None,
        "max_time_diff_s": max_delta,
        "weather_limits": limits,
        "warnings": [],
    }
    for role in ("high", "low"):
        output_runs = []
        for run in source.get(role) or []:
            copied_run = deepcopy(run)
            sync = _run_weather_sync(copied_run, weather_data, max_delta, limits)
            copied_run["weather_sync"] = sync
            output_runs.append(copied_run)
            metadata[f"{role}_total"] += 1
            if sync.get("matched"):
                metadata[f"{role}_synchronized"] += 1
            if sync.get("status") == "missing":
                metadata["missing_count"] += 1
            wind = _finite(sync.get("wind_speed_mps"))
            temperature = _finite(sync.get("temperature_c"))
            if wind is not None and wind > limits["wind_speed_max_mps"]:
                metadata["wind_above_limit_count"] += 1
            if temperature is not None and temperature > limits["temperature_max_c"]:
                metadata["temperature_above_limit_count"] += 1
            delta = _finite(sync.get("time_diff_s"))
            if delta is not None:
                current = metadata["max_time_diff_s_found"]
                metadata["max_time_diff_s_found"] = delta if current is None else max(current, delta)
            metadata["warnings"].extend(sync.get("warnings") or [])
        enriched[role] = output_runs
    metadata["warnings"] = list(dict.fromkeys(metadata["warnings"]))
    enriched["warnings"] = list(source.get("warnings") or [])
    return enriched, metadata


def build_split_candidate_weather_context(component_runs: dict) -> dict:
    """Build correction input and traceability from four enriched Split runs."""
    weather_components = {
        component: deepcopy(((component_runs.get(component) or {}).get("weather_sync") or {}))
        for component in COMPONENTS
    }
    temperatures = [_finite(item.get("temperature_c", item.get("temperature"))) for item in weather_components.values()]
    pressures = [_finite(item.get("pressure_kpa", item.get("pressure"))) for item in weather_components.values()]
    winds = [_finite(item.get("wind_speed_mps", item.get("wind_speed"))) for item in weather_components.values()]
    valid_temperatures = [value for value in temperatures if value is not None]
    valid_pressures = [value for value in pressures if value is not None]
    valid_winds = [value for value in winds if value is not None]
    statuses = [item.get("status", "missing") for item in weather_components.values()]
    warnings = []
    for component, item in weather_components.items():
        warnings.extend(f"{component}: {warning}" for warning in item.get("warnings") or [])
    if "missing" in statuses:
        status = "missing"
    elif "invalid" in statuses:
        status = "invalid"
    elif "warning" in statuses:
        status = "warning"
    else:
        status = "ok"
    return {
        "weather_components": weather_components,
        "weather_sync": weather_components,
        "weather_summary": {
            "temperature_c_mean": sum(valid_temperatures) / len(valid_temperatures) if valid_temperatures else None,
            "pressure_kpa_mean": sum(valid_pressures) / len(valid_pressures) if valid_pressures else None,
            "wind_speed_mps_max": max(valid_winds) if valid_winds else None,
            "wind_speed_mps_mean": sum(valid_winds) / len(valid_winds) if valid_winds else None,
            "status": status,
            "warnings": list(dict.fromkeys(warnings)),
        },
    }

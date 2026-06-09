# coding: utf-8
"""Pure environmental-correction helpers for Coastdown Split coefficients."""

from __future__ import annotations

import math

from core.split_energy import calculate_split_energy


REFERENCE_TEMPERATURE_K = 293.15
REFERENCE_PRESSURE_KPA = 101.325
TEMPERATURE_COEFFICIENT = 0.0086
PRESSURE_COEFFICIENT = 0.0002503
MS2_TO_KMH2 = 12.96

PAIR_COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")
PLUS_COMPONENTS = ("high_plus", "low_plus")
MINUS_COMPONENTS = ("high_minus", "low_minus")
ENERGY_UNAVAILABLE_STATUS = (
    "N/A - corrected Split F0/F2 are unavailable"
)


def correct_split_coefficients(
    f0_prime: float,
    f2_prime: float,
    temperature_c: float,
    pressure_kpa: float,
) -> dict:
    """
    Convert uncorrected Split f'0/f'2 into corrected F0/F2.

    Input f'2 is expressed in N/(m/s)^2. Corrected F2 is expressed in
    N/(km/h)^2, matching the inherited ABNT climatic-correction formula.
    """
    values = {
        "f0_prime": f0_prime,
        "f2_prime": f2_prime,
        "temperature_c": temperature_c,
        "pressure_kpa": pressure_kpa,
    }
    numeric = {}
    for key, value in values.items():
        try:
            numeric[key] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be numeric.") from exc
        if not math.isfinite(numeric[key]):
            raise ValueError(f"{key} must be finite.")

    if numeric["temperature_c"] <= -273.15:
        raise ValueError("Temperature must be greater than absolute zero.")
    if numeric["pressure_kpa"] <= 0:
        raise ValueError("Pressure must be greater than zero.")

    temperature_k = numeric["temperature_c"] + 273.15
    f0_corrected = numeric["f0_prime"] * (
        1
        + TEMPERATURE_COEFFICIENT
        * (temperature_k - REFERENCE_TEMPERATURE_K)
    )
    f2_corrected = (
        (
            (REFERENCE_PRESSURE_KPA * temperature_k)
            / (numeric["pressure_kpa"] * REFERENCE_TEMPERATURE_K)
        )
        * (
            numeric["f2_prime"]
            - PRESSURE_COEFFICIENT * numeric["f0_prime"]
        )
        + PRESSURE_COEFFICIENT * f0_corrected
    ) / MS2_TO_KMH2

    return {
        "F0": f0_corrected,
        "F2": f2_corrected,
        "temperature_c": numeric["temperature_c"],
        "pressure_kpa": numeric["pressure_kpa"],
        "F0_unit": "N",
        "F2_unit": "N/(km/h)^2",
    }


def fixed_ambient_conditions(temperature_c: float, pressure_kpa: float) -> dict:
    """Build valid fixed conditions for both Split directions."""
    # Validate through the same constraints used by the correction formula.
    correct_split_coefficients(0.0, 0.0, temperature_c, pressure_kpa)
    temperature = float(temperature_c)
    pressure = float(pressure_kpa)
    ambient_by_component = {
        component: {
            "matched": True,
            "run_datetime": None,
            "weather_datetime": None,
            "sync_method": "fixed",
            "time_delta_seconds": None,
            "temperature_c": temperature,
            "pressure_kpa": pressure,
            "wind_speed_ms": None,
            "wind_direction_deg": None,
            "source_file": None,
            "warnings": [],
        }
        for component in PAIR_COMPONENTS
    }
    return {
        "available": True,
        "plus_available": True,
        "minus_available": True,
        "ambient_mode": "fixed",
        "ambient_source": "manual_fixed",
        "temp_plus_used": temperature,
        "press_plus_used": pressure,
        "temp_minus_used": temperature,
        "press_minus_used": pressure,
        "ambient_by_component": ambient_by_component,
        "weather_sync": {},
        "warnings": [],
    }


def normalize_ambient_by_component(weather_sync: dict | None) -> dict:
    """Return the canonical four-component ambient traceability structure."""
    ambient = {}
    for component in PAIR_COMPONENTS:
        sync = (weather_sync or {}).get(component) or {}
        weather_record = sync.get("weather_record") or {}
        ambient[component] = {
            "matched": bool(sync.get("matched")),
            "run_datetime": sync.get("run_datetime"),
            "weather_datetime": sync.get("weather_datetime"),
            "sync_method": sync.get("sync_method", "not_found"),
            "time_delta_seconds": sync.get("time_delta_seconds"),
            "temperature_c": sync.get("temperature"),
            "pressure_kpa": sync.get("pressure"),
            "wind_speed_ms": sync.get("wind_speed"),
            "wind_direction_deg": sync.get("wind_direction"),
            "source_file": (
                sync.get("source_file")
                or weather_record.get("source_file")
                or weather_record.get("filename")
            ),
            "warnings": list(sync.get("warnings") or []),
        }
    return ambient


def _ambient_aliases(ambient_by_component: dict) -> dict:
    aliases = {}
    for component in PAIR_COMPONENTS:
        ambient = ambient_by_component.get(component) or {}
        aliases[f"temp_{component}"] = ambient.get("temperature_c")
        aliases[f"press_{component}"] = ambient.get("pressure_kpa")
        aliases[f"wind_{component}"] = ambient.get("wind_speed_ms")
    return aliases


def _direction_conditions(
    ambient_by_component: dict,
    components: tuple[str, str],
    direction: str,
) -> tuple[bool, float | None, float | None, list[str]]:
    temperatures = []
    pressures = []
    missing = []
    for component in components:
        ambient = ambient_by_component.get(component) or {}
        temperature = ambient.get("temperature_c")
        pressure = ambient.get("pressure_kpa")
        if not ambient.get("matched"):
            missing.append(f"{component}.match")
        if (
            not isinstance(temperature, (int, float))
            or isinstance(temperature, bool)
            or not math.isfinite(float(temperature))
        ):
            missing.append(f"{component}.temperature")
        else:
            temperatures.append(float(temperature))
        if (
            not isinstance(pressure, (int, float))
            or isinstance(pressure, bool)
            or not math.isfinite(float(pressure))
        ):
            missing.append(f"{component}.pressure")
        else:
            pressures.append(float(pressure))

    if missing:
        return (
            False,
            None,
            None,
            [
                "Corrected coefficients for direction "
                f"{direction} were not calculated because ambient values are "
                f"missing: {', '.join(missing)}."
            ],
        )

    return (
        True,
        sum(temperatures) / len(temperatures),
        sum(pressures) / len(pressures),
        [],
    )


def weather_sync_ambient_conditions(weather_sync: dict) -> dict:
    """Average high/low synchronized conditions independently by direction."""
    sync_data = weather_sync or {}
    ambient_by_component = normalize_ambient_by_component(sync_data)
    warnings = []
    for component in PAIR_COMPONENTS:
        sync = sync_data.get(component) or {}
        warnings.extend(sync.get("warnings") or [])
    plus_available, temp_plus, press_plus, plus_warnings = _direction_conditions(
        ambient_by_component,
        PLUS_COMPONENTS,
        "+",
    )
    minus_available, temp_minus, press_minus, minus_warnings = _direction_conditions(
        ambient_by_component,
        MINUS_COMPONENTS,
        "-",
    )
    warnings.extend(plus_warnings)
    warnings.extend(minus_warnings)

    conditions = {
        "available": plus_available and minus_available,
        "plus_available": plus_available,
        "minus_available": minus_available,
        "ambient_mode": "weather_sync",
        "ambient_source": "weather_file_sync",
        "temp_plus_used": temp_plus,
        "press_plus_used": press_plus,
        "temp_minus_used": temp_minus,
        "press_minus_used": press_minus,
        "ambient_by_component": ambient_by_component,
        "weather_sync": sync_data,
        "warnings": list(dict.fromkeys(warnings)),
    }
    conditions.update(_ambient_aliases(ambient_by_component))
    return conditions


def apply_split_pair_correction(
    split_result: dict,
    ambient_conditions: dict,
) -> dict:
    """Return one complete Split result with separate corrected coefficients."""
    result = dict(split_result)
    conditions = dict(ambient_conditions or {})
    raw_plus = result.get("result_plus") or {}
    raw_minus = result.get("result_minus") or {}
    raw_mean = result.get("result_pair_mean") or {}
    warnings = list(result.get("warnings") or [])
    warnings.extend(conditions.get("warnings") or [])
    ambient_by_component = {
        component: dict((conditions.get("ambient_by_component") or {}).get(component) or {})
        for component in PAIR_COMPONENTS
    }
    for component in PAIR_COMPONENTS:
        run_record = result.get(component) or {}
        if ambient_by_component[component].get("run_datetime") is None:
            ambient_by_component[component]["run_datetime"] = (
                run_record.get("start_timestamp")
                or run_record.get("start_time_str")
            )
    ambient_aliases = _ambient_aliases(ambient_by_component)

    result.update(
        {
            "ambient_mode": conditions.get("ambient_mode"),
            "ambient_source": conditions.get("ambient_source"),
            "temp_plus_used": conditions.get("temp_plus_used"),
            "press_plus_used": conditions.get("press_plus_used"),
            "temp_minus_used": conditions.get("temp_minus_used"),
            "press_minus_used": conditions.get("press_minus_used"),
            "ambient_by_component": ambient_by_component,
            "weather_sync": conditions.get("weather_sync") or {},
            "f0_prime_plus": result.get(
                "f0_prime_plus",
                raw_plus.get("f0_prime"),
            ),
            "f2_prime_plus": result.get(
                "f2_prime_plus",
                raw_plus.get("f2_prime"),
            ),
            "f0_prime_minus": result.get(
                "f0_prime_minus",
                raw_minus.get("f0_prime"),
            ),
            "f2_prime_minus": result.get(
                "f2_prime_minus",
                raw_minus.get("f2_prime"),
            ),
            "f0_prime_mean": result.get(
                "f0_prime_mean",
                raw_mean.get("f0_prime"),
            ),
            "f2_prime_mean": result.get(
                "f2_prime_mean",
                raw_mean.get("f2_prime"),
            ),
            "correction_available": False,
            "corrected_result_plus": None,
            "corrected_result_minus": None,
            "corrected_pair_mean": None,
            "F0_plus": None,
            "F2_plus": None,
            "F0_minus": None,
            "F2_minus": None,
            "F0_mean": None,
            "F2_mean": None,
            "energy": None,
            "energy_unit": None,
            "energy_profile": None,
            "energy_origin": None,
            "energy_status": ENERGY_UNAVAILABLE_STATUS,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )
    result.update(ambient_aliases)

    corrected_plus = None
    if conditions.get("plus_available", conditions.get("available")):
        corrected_plus = correct_split_coefficients(
            raw_plus.get("f0_prime"),
            raw_plus.get("f2_prime"),
            conditions.get("temp_plus_used"),
            conditions.get("press_plus_used"),
        )
        result.update(
            {
                "corrected_result_plus": corrected_plus,
                "F0_plus": corrected_plus["F0"],
                "F2_plus": corrected_plus["F2"],
            }
        )

    corrected_minus = None
    if conditions.get("minus_available", conditions.get("available")):
        corrected_minus = correct_split_coefficients(
            raw_minus.get("f0_prime"),
            raw_minus.get("f2_prime"),
            conditions.get("temp_minus_used"),
            conditions.get("press_minus_used"),
        )
        result.update(
            {
                "corrected_result_minus": corrected_minus,
                "F0_minus": corrected_minus["F0"],
                "F2_minus": corrected_minus["F2"],
            }
        )

    if corrected_plus is None or corrected_minus is None:
        return result

    corrected_mean = {
        "F0": (corrected_plus["F0"] + corrected_minus["F0"]) / 2.0,
        "F2": (corrected_plus["F2"] + corrected_minus["F2"]) / 2.0,
        "F0_unit": "N",
        "F2_unit": "N/(km/h)^2",
    }
    energy_result = calculate_split_energy(corrected_mean["F0"], corrected_mean["F2"])

    result.update(
        {
            "correction_available": True,
            "corrected_pair_mean": corrected_mean,
            "F0_mean": corrected_mean["F0"],
            "F2_mean": corrected_mean["F2"],
            "energy": energy_result["energy"],
            "energy_unit": energy_result["energy_unit"],
            "energy_profile": energy_result["energy_profile"],
            "energy_origin": energy_result["energy_origin"],
            "energy_status": energy_result["energy_status"],
            "energy_details": energy_result,
        }
    )
    return result

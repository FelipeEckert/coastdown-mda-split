# coding: utf-8
"""Pure environmental-correction helpers for Coastdown Split coefficients."""

from __future__ import annotations

import math


REFERENCE_TEMPERATURE_K = 293.15
REFERENCE_PRESSURE_KPA = 101.325
TEMPERATURE_COEFFICIENT = 0.0086
PRESSURE_COEFFICIENT = 0.0002503
MS2_TO_KMH2 = 12.96

PAIR_COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")
ENERGY_UNAVAILABLE_STATUS = (
    "N/A - no neutral Split energy function with explicit corrected F0/F2, "
    "mass and cycle/profile contract"
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
    return {
        "available": True,
        "ambient_mode": "fixed",
        "ambient_source": "manual_fixed",
        "temp_plus_used": temperature,
        "press_plus_used": pressure,
        "temp_minus_used": temperature,
        "press_minus_used": pressure,
        "weather_sync": {},
        "warnings": [],
    }


def weather_sync_ambient_conditions(weather_sync: dict) -> dict:
    """Average high/low synchronized conditions independently by direction."""
    sync_data = weather_sync or {}
    warnings = []
    missing = []
    for component in PAIR_COMPONENTS:
        sync = sync_data.get(component) or {}
        warnings.extend(sync.get("warnings") or [])
        temperature = sync.get("temperature")
        pressure = sync.get("pressure")
        if (
            not sync.get("matched")
            or not isinstance(temperature, (int, float))
            or not isinstance(pressure, (int, float))
        ):
            missing.append(component)

    if missing:
        warnings.append(
            "Corrected coefficients were not calculated because valid weather "
            f"conditions are missing for: {', '.join(missing)}."
        )
        return {
            "available": False,
            "ambient_mode": "weather_sync",
            "ambient_source": "weather_file_sync",
            "temp_plus_used": None,
            "press_plus_used": None,
            "temp_minus_used": None,
            "press_minus_used": None,
            "weather_sync": sync_data,
            "warnings": list(dict.fromkeys(warnings)),
        }

    temp_plus = (
        float(sync_data["high_plus"]["temperature"])
        + float(sync_data["low_plus"]["temperature"])
    ) / 2.0
    press_plus = (
        float(sync_data["high_plus"]["pressure"])
        + float(sync_data["low_plus"]["pressure"])
    ) / 2.0
    temp_minus = (
        float(sync_data["high_minus"]["temperature"])
        + float(sync_data["low_minus"]["temperature"])
    ) / 2.0
    press_minus = (
        float(sync_data["high_minus"]["pressure"])
        + float(sync_data["low_minus"]["pressure"])
    ) / 2.0

    return {
        "available": True,
        "ambient_mode": "weather_sync",
        "ambient_source": "weather_file_sync",
        "temp_plus_used": temp_plus,
        "press_plus_used": press_plus,
        "temp_minus_used": temp_minus,
        "press_minus_used": press_minus,
        "weather_sync": sync_data,
        "warnings": list(dict.fromkeys(warnings)),
    }


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

    result.update(
        {
            "ambient_mode": conditions.get("ambient_mode"),
            "ambient_source": conditions.get("ambient_source"),
            "temp_plus_used": conditions.get("temp_plus_used"),
            "press_plus_used": conditions.get("press_plus_used"),
            "temp_minus_used": conditions.get("temp_minus_used"),
            "press_minus_used": conditions.get("press_minus_used"),
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
            "energy_status": ENERGY_UNAVAILABLE_STATUS,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )

    if not conditions.get("available"):
        return result

    corrected_plus = correct_split_coefficients(
        raw_plus.get("f0_prime"),
        raw_plus.get("f2_prime"),
        conditions.get("temp_plus_used"),
        conditions.get("press_plus_used"),
    )
    corrected_minus = correct_split_coefficients(
        raw_minus.get("f0_prime"),
        raw_minus.get("f2_prime"),
        conditions.get("temp_minus_used"),
        conditions.get("press_minus_used"),
    )
    corrected_mean = {
        "F0": (corrected_plus["F0"] + corrected_minus["F0"]) / 2.0,
        "F2": (corrected_plus["F2"] + corrected_minus["F2"]) / 2.0,
        "F0_unit": "N",
        "F2_unit": "N/(km/h)^2",
    }

    result.update(
        {
            "correction_available": True,
            "corrected_result_plus": corrected_plus,
            "corrected_result_minus": corrected_minus,
            "corrected_pair_mean": corrected_mean,
            "F0_plus": corrected_plus["F0"],
            "F2_plus": corrected_plus["F2"],
            "F0_minus": corrected_minus["F0"],
            "F2_minus": corrected_minus["F2"],
            "F0_mean": corrected_mean["F0"],
            "F2_mean": corrected_mean["F2"],
        }
    )
    return result

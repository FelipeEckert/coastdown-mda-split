# coding: utf-8
"""Pure normalization and calculation of the Split effective mass."""

from __future__ import annotations

import math


ADDITIONAL_TEST_MASS_KG = 136.0
DEFAULT_ROTATIONAL_MASS_FRACTION = 0.03


def _positive_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _nonnegative_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def compute_split_effective_mass(
    *,
    running_order_mass_kg: float | None = None,
    test_mass_kg: float | None = None,
    rotational_equivalent_mass_kg: float | None = None,
    estimate_rotational_mass: bool = True,
) -> dict:
    """Return canonical masses using M = running-order mass + 136 and Me = M + me."""
    running_mass = _positive_number(running_order_mass_kg)
    test_mass = _positive_number(test_mass_kg)
    rotational_mass = _nonnegative_number(rotational_equivalent_mass_kg)
    warnings = []

    if running_mass is not None:
        calculated_test_mass = running_mass + ADDITIONAL_TEST_MASS_KG
        if test_mass is not None and not math.isclose(test_mass, calculated_test_mass):
            warnings.append(
                "Massa de ensaio informada ignorada: foi recalculada como massa em ordem de marcha + 136 kg."
            )
        test_mass = calculated_test_mass
    elif test_mass is None:
        raise ValueError("Running-order mass or test mass must be greater than zero.")

    estimated = False
    if rotational_mass is None:
        if not estimate_rotational_mass:
            raise ValueError("Rotational equivalent mass must be greater than zero.")
        rotational_mass = DEFAULT_ROTATIONAL_MASS_FRACTION * test_mass
        estimated = True

    return {
        "running_order_mass_kg": running_mass,
        "test_mass_kg": test_mass,
        "rotational_equivalent_mass_kg": rotational_mass,
        "rotational_mass_estimated": estimated,
        "effective_mass_kg": test_mass + rotational_mass,
        "warnings": warnings,
    }


def normalize_split_vehicle_mass_data(vehicle_data: dict | None) -> dict:
    """Normalize current and legacy vehicle mass fields without double-adding 136 kg."""
    source = dict(vehicle_data or {})
    nested = source.get("vehicle_info")
    if isinstance(nested, dict):
        source = {**nested, **source}

    running_mass = _positive_number(source.get("running_order_mass_kg"))
    test_mass = _positive_number(source.get("test_mass_kg"))
    rotational_mass = _nonnegative_number(
        source.get("rotational_equivalent_mass_kg")
        if source.get("rotational_equivalent_mass_kg") is not None
        else source.get("inertia_mass")
    )
    effective_mass = _positive_number(
        source.get("effective_mass_kg")
        or source.get("effective_mass")
        or source.get("Me")
    )
    legacy_total_mass = _positive_number(source.get("total_mass"))

    if running_mass is not None or test_mass is not None:
        result = compute_split_effective_mass(
            running_order_mass_kg=running_mass,
            test_mass_kg=test_mass,
            rotational_equivalent_mass_kg=rotational_mass,
        )
        if effective_mass is not None and not math.isclose(
            effective_mass, result["effective_mass_kg"], rel_tol=1e-9, abs_tol=1e-9,
        ):
            result["warnings"].append(
                "Massa efetiva legada divergente ignorada em favor dos campos canônicos."
            )
        return result

    # In the inherited UI, total_mass represented M whenever an explicit Me was saved.
    if effective_mass is not None and legacy_total_mass is not None:
        inferred_rotational = rotational_mass or (effective_mass - legacy_total_mass)
        if inferred_rotational >= 0:
            result = compute_split_effective_mass(
                test_mass_kg=legacy_total_mass,
                rotational_equivalent_mass_kg=inferred_rotational,
            )
            result["warnings"].append("Dados de massa legados normalizados.")
            return result

    # Compatibility: older calculation callers used total_mass (or effective_mass) as Me.
    direct_effective_mass = effective_mass or legacy_total_mass
    if direct_effective_mass is not None:
        return {
            "running_order_mass_kg": None,
            "test_mass_kg": None,
            "rotational_equivalent_mass_kg": None,
            "rotational_mass_estimated": False,
            "effective_mass_kg": direct_effective_mass,
            "warnings": [
                "Massa efetiva legada preservada; informe os campos normativos para obter a decomposição M + me."
            ],
        }

    return {
        "running_order_mass_kg": None,
        "test_mass_kg": None,
        "rotational_equivalent_mass_kg": None,
        "rotational_mass_estimated": False,
        "effective_mass_kg": None,
        "warnings": [],
    }

# coding: utf-8
"""Energy adapter for corrected Coastdown Split coefficients."""

from __future__ import annotations

import math

from core.calculations import calcular_energia


DEFAULT_SPLIT_ENERGY_PROFILE = "standard_formula_calcular_energia"
ENERGY_UNIT = "MJ/km"


def calculate_split_energy(
    F0_mean: float,
    F2_mean: float,
) -> dict:
    """
    Calculate Split energy by delegating to the inherited Standard formula.

    This adapter calls ``core.calculations.calcular_energia`` with corrected
    mean F0/F2. That inherited function depends only on those coefficients and
    returns MJ/km. Its constants and cycle/profile remain embedded in the
    existing Standard formula and still require normative provenance review.
    """
    try:
        f0_value = float(F0_mean)
        f2_value = float(F2_mean)
    except (TypeError, ValueError) as exc:
        raise ValueError("Corrected F0 and F2 must be numeric.") from exc
    if not math.isfinite(f0_value) or not math.isfinite(f2_value):
        raise ValueError("Corrected F0 and F2 must be finite.")

    energy = calcular_energia(f0_value, f2_value)

    return {
        "energy": energy,
        "energy_unit": ENERGY_UNIT,
        "energy_status": "calculated",
        "energy_profile": DEFAULT_SPLIT_ENERGY_PROFILE,
        "energy_origin": "core.calculations.calcular_energia",
        "F0_used": f0_value,
        "F2_used": f2_value,
    }

# coding: utf-8
"""Pure diagnostics for selected pairs in the Split final comparison."""

from __future__ import annotations

import math
import statistics
from copy import deepcopy

from core.split_display import get_split_pair_public_label
from core.split_results import consolidate_split_final_results
from core.split_time_validation import (
    extract_split_candidate_times,
    validate_split_selected_times,
)
from core.split_weather_context import split_environmental_values


DEFAULT_WEATHER_LIMITS = {
    # Initial diagnostic limits requested for Round 10A; they remain configurable.
    "wind_speed_max_mps": 3.0,
    "temperature_max_c": 35.0,
}
AMBIENT_COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")


def build_selected_pairs_signature(selected_pairs: list[dict]) -> tuple:
    """Return a stable signature containing only deviation-analysis inputs."""
    signature = []
    for index, pair in enumerate(selected_pairs or [], start=1):
        if not isinstance(pair, dict) or pair.get("selected") is not True:
            continue
        environmental = split_environmental_values(pair)
        component_times = []
        for component in AMBIENT_COMPONENTS:
            record = pair.get(component) if isinstance(pair.get(component), dict) else {}
            component_times.append(
                _finite_float(
                    pair.get(f"{component}_delta_t_s", record.get("delta_t_s"))
                )
            )
        signature.append(
            (
                str(pair.get("id") or pair.get("pair_id") or index),
                True,
                _first_number(pair, "F0_mean", "F0", "mean_f0_corrected"),
                _first_number(pair, "F2_mean", "F2", "mean_f2_corrected"),
                _first_number(pair, "energy", "mean_energy_corrected"),
                tuple(component_times),
                environmental.get("mode"),
                environmental.get("temperature_c"),
                environmental.get("pressure_kpa"),
                environmental.get("wind_speed_mps"),
                tuple(str(item) for item in pair.get("warnings") or []),
            )
        )
    return tuple(signature)


def get_cached_split_deviation_analysis(
    selected_pairs: list[dict],
    cache: dict | None,
    *,
    analyzer=None,
) -> tuple[dict, dict, bool]:
    """Return analysis plus refreshed cache and whether it was reused."""
    signature = build_selected_pairs_signature(selected_pairs)
    current = cache if isinstance(cache, dict) else {}
    if current.get("signature") == signature and isinstance(current.get("analysis"), dict):
        return deepcopy(current["analysis"]), current, True
    analyze = analyzer or analyze_split_selected_deviations
    analysis = analyze(selected_pairs)
    refreshed = {"signature": signature, "analysis": deepcopy(analysis)}
    return analysis, refreshed, False


def _finite_float(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _first_number(source: dict, *keys):
    for key in keys:
        value = _finite_float(source.get(key))
        if value is not None:
            return value
    return None


def _sample_stdev(values: list[float]):
    return statistics.stdev(values) if len(values) >= 2 else None


def _percent_deviation(value, mean):
    if value is None or mean is None or abs(mean) <= 1e-12:
        return None
    return (value - mean) / mean * 100.0


def _coefficient_status(summary: dict, limit: float) -> str:
    if summary.get("pair_count", 0) < 2:
        return "insufficient_data"
    if summary.get("missing_f0_count") or summary.get("missing_f2_count"):
        return "warning"
    cvs = (summary.get("cv_f0_pct"), summary.get("cv_f2_pct"))
    if any(value is not None and value > limit for value in cvs):
        return "failed"
    if any(value is None for value in cvs):
        return "insufficient_data"
    return "approved"


def _pair_label(pair: dict, index: int) -> str:
    return get_split_pair_public_label(pair)


def _pair_deviations(
    pairs: list[dict],
    coefficient_summary: dict,
    limit_pct: float,
) -> list[dict]:
    rows = []
    for index, pair in enumerate(pairs, start=1):
        f0 = _first_number(pair, "F0_mean", "F0", "mean_f0", "mean_f0_corrected")
        f2 = _first_number(pair, "F2_mean", "F2", "mean_f2", "mean_f2_corrected")
        f0_pct = _percent_deviation(f0, coefficient_summary.get("mean_f0"))
        f2_pct = _percent_deviation(f2, coefficient_summary.get("mean_f2"))
        rows.append(
            {
                "pair": _pair_label(pair, index),
                "pair_id": pair.get("id"),
                "f0": f0,
                "f0_deviation_abs": None if f0 is None else f0 - coefficient_summary["mean_f0"],
                "f0_deviation_pct": f0_pct,
                "f2": f2,
                "f2_deviation_abs": None if f2 is None else f2 - coefficient_summary["mean_f2"],
                "f2_deviation_pct": f2_pct,
                "energy": _first_number(pair, "energy"),
                "alerts": [],
                "largest_f0_deviation": False,
                "largest_f2_deviation": False,
                "outside_limit": any(
                    value is not None and abs(value) > limit_pct
                    for value in (f0_pct, f2_pct)
                ),
            }
        )

    for key, flag in (("f0_deviation_pct", "largest_f0_deviation"), ("f2_deviation_pct", "largest_f2_deviation")):
        valid = [row for row in rows if row[key] is not None]
        if valid:
            largest = max(valid, key=lambda row: abs(row[key]))
            largest[flag] = True

    for row in rows:
        for name, key in (("F0", "f0_deviation_pct"), ("F2", "f2_deviation_pct")):
            value = row[key]
            if value is not None and abs(value) > 1e-12:
                row["alerts"].append(f"{name} {'acima' if value > 0 else 'abaixo'} da média")
        if row["largest_f0_deviation"]:
            row["alerts"].append("Maior desvio de F0")
        if row["largest_f2_deviation"]:
            row["alerts"].append("Maior desvio de F2")
        if row["outside_limit"]:
            row["alerts"].append("Desvio fora da faixa")
        if not row["alerts"]:
            row["alerts"].append("Dentro da faixa")
    return rows


def _weather_rows(pairs: list[dict], limits: dict) -> tuple[list[dict], str, list[str]]:
    rows = []
    warnings = []
    for index, pair in enumerate(pairs, start=1):
        environmental = split_environmental_values(pair)
        temperature = environmental["temperature_c"]
        pressure = environmental["pressure_kpa"]
        wind = environmental["wind_speed_mps"]
        alerts = []
        if wind is not None and wind > limits["wind_speed_max_mps"]:
            alerts.append(f"⚠️ Potencialmente invalidante: vento acima de {limits['wind_speed_max_mps']:g} m/s")
        if temperature is not None and temperature > limits["temperature_max_c"]:
            alerts.append(f"⚠️ Potencialmente invalidante: temperatura acima de {limits['temperature_max_c']:g} °C")
        if alerts:
            warnings.extend(f"{_pair_label(pair, index)}: {alert}" for alert in alerts)
        rows.append(
            {
                "pair": _pair_label(pair, index),
                "temperature_c": temperature,
                "pressure_kpa": pressure,
                "wind_speed_mps": wind,
                "status": "failed" if alerts else ("approved" if temperature is not None or wind is not None else "insufficient_data"),
                "alerts": alerts,
            }
        )
    if any(row["status"] == "failed" for row in rows):
        status = "failed"
    elif rows and all(row["status"] == "approved" for row in rows):
        status = "approved"
    else:
        status = "insufficient_data"
    return rows, status, warnings


def _leave_one_out(pairs: list[dict], current: dict) -> list[dict]:
    if len(pairs) < 3:
        return []
    rows = []
    for index, pair in enumerate(pairs):
        reduced = consolidate_split_final_results(pairs[:index] + pairs[index + 1 :])
        new_f0 = reduced.get("cv_f0")
        new_f2 = reduced.get("cv_f2")
        current_f0 = current.get("cv_f0_pct")
        current_f2 = current.get("cv_f2_pct")
        rows.append(
            {
                "pair": _pair_label(pair, index + 1),
                "pair_id": pair.get("id"),
                "current_cv_f0_pct": current_f0,
                "new_cv_f0_pct": new_f0,
                "cv_f0_change_pct_points": None if new_f0 is None or current_f0 is None else new_f0 - current_f0,
                "current_cv_f2_pct": current_f2,
                "new_cv_f2_pct": new_f2,
                "cv_f2_change_pct_points": None if new_f2 is None or current_f2 is None else new_f2 - current_f2,
                "largest_f0_improvement": False,
                "largest_f2_improvement": False,
                "status": "diagnostic",
            }
        )
    for key, flag in (("cv_f0_change_pct_points", "largest_f0_improvement"), ("cv_f2_change_pct_points", "largest_f2_improvement")):
        valid = [row for row in rows if row[key] is not None]
        if valid and min(row[key] for row in valid) < 0:
            min(valid, key=lambda row: row[key])[flag] = True
    return rows


def analyze_split_selected_deviations(
    selected_pairs: list[dict],
    *,
    cv_limit_coefficients_pct: float = 10.0,
    cv_limit_time_pct: float = 2.5,
    opposite_time_limit_pct: float = 10.0,
    weather_limits: dict | None = None,
) -> dict:
    """Analyze selected Split pairs without mutating or filtering them."""
    pairs = [pair for pair in selected_pairs or [] if isinstance(pair, dict) and pair.get("selected") is True]
    limits = dict(DEFAULT_WEATHER_LIMITS)
    limits.update(weather_limits or {})
    consolidated = consolidate_split_final_results(pairs)
    f0_values = [pair["F0_mean"] for pair in consolidated["selected_pairs"] if pair["F0_mean"] is not None]
    f2_values = [pair["F2_mean"] for pair in consolidated["selected_pairs"] if pair["F2_mean"] is not None]
    coefficient_summary = {
        "pair_count": len(pairs),
        "mean_f0": consolidated.get("mean_f0"),
        "stdev_f0": _sample_stdev(f0_values),
        "cv_f0_pct": consolidated.get("cv_f0"),
        "mean_f2": consolidated.get("mean_f2"),
        "stdev_f2": _sample_stdev(f2_values),
        "cv_f2_pct": consolidated.get("cv_f2"),
        "missing_f0_count": consolidated.get("missing_f0_count", 0),
        "missing_f2_count": consolidated.get("missing_f2_count", 0),
        "limit_pct": cv_limit_coefficients_pct,
    }
    coefficient_summary["status"] = _coefficient_status(coefficient_summary, cv_limit_coefficients_pct)
    time_validation = validate_split_selected_times(
        pairs,
        cv_limit_pct=cv_limit_time_pct,
        opposite_mean_limit_pct=opposite_time_limit_pct,
    )
    time_summary = dict(time_validation)
    extracted_times = extract_split_candidate_times(pairs)
    time_summary["groups"] = {
        component: {
            **group,
            "stdev": _sample_stdev(extracted_times[component]),
        }
        for component, group in time_validation["groups"].items()
    }
    time_summary["status"] = {True: "approved", False: "failed", None: "insufficient_data"}[time_validation["passed"]]
    weather_rows, weather_status, weather_warnings = _weather_rows(pairs, limits)
    weather_summary = {"limits": limits, "pairs": weather_rows, "status": weather_status}
    warnings = list(dict.fromkeys([*time_validation["warnings"], *weather_warnings]))
    if len(pairs) < 3:
        warnings.append("Análise leave-one-out requer pelo menos 3 pares selecionados.")
    statuses = (coefficient_summary["status"], time_summary["status"], weather_status)
    if not pairs:
        status = "insufficient_data"
    elif "failed" in statuses:
        status = "failed"
    elif "warning" in statuses:
        status = "warning"
    elif "insufficient_data" in statuses:
        status = "insufficient_data"
    else:
        status = "approved"
    return {
        "pair_count": len(pairs),
        "coefficient_summary": coefficient_summary,
        "time_summary": time_summary,
        "weather_summary": weather_summary,
        "pair_deviations": _pair_deviations(
            pairs,
            coefficient_summary,
            cv_limit_coefficients_pct,
        ) if pairs and coefficient_summary["mean_f0"] is not None and coefficient_summary["mean_f2"] is not None else [],
        "leave_one_out": _leave_one_out(pairs, coefficient_summary),
        "status": status,
        "warnings": warnings,
    }

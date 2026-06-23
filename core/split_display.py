# coding: utf-8
"""Pure display helpers for Split runs and complete pairs."""

from __future__ import annotations

import math


MISSING_VALUE = "—"


def _finite_number(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _reference_speed_label(value) -> str:
    number = _finite_number(value)
    return "" if number is None else f" {number:g} km/h"


def get_split_reference_speeds(source) -> tuple[float | None, float | None]:
    """Return configured high/low reference speeds from pairs or config data."""
    items = source if isinstance(source, (list, tuple)) else [source]
    high_reference = None
    low_reference = None
    for item in items:
        if not isinstance(item, dict):
            continue
        config = item.get("split_interval_config") or item.get("interval_config") or {}
        high_config = config.get("high") if isinstance(config, dict) else {}
        low_config = config.get("low") if isinstance(config, dict) else {}
        if high_reference is None:
            high_reference = _finite_number(
                item.get("v2_reference_kmh", item.get("high_reference_speed_kmh"))
            )
            if high_reference is None and isinstance(high_config, dict):
                high_reference = _finite_number(high_config.get("reference"))
        if low_reference is None:
            low_reference = _finite_number(
                item.get("v1_reference_kmh", item.get("low_reference_speed_kmh"))
            )
            if low_reference is None and isinstance(low_config, dict):
                low_reference = _finite_number(low_config.get("reference"))
        if high_reference is not None and low_reference is not None:
            break
    return high_reference, low_reference


def format_split_time_group_label(
    group_key: str,
    *,
    high_reference_speed_kmh: float | None = None,
    low_reference_speed_kmh: float | None = None,
) -> str:
    """Return a public label for one normative Split Delta-t CV group."""
    groups = {
        "high_plus": ("alta", high_reference_speed_kmh, "[+]"),
        "high_minus": ("alta", high_reference_speed_kmh, "[-]"),
        "low_plus": ("baixa", low_reference_speed_kmh, "[+]"),
        "low_minus": ("baixa", low_reference_speed_kmh, "[-]"),
    }
    if group_key not in groups:
        return str(group_key)
    speed_group, reference_speed, direction = groups[group_key]
    return (
        f"C.V. Δt — Vel. ref. {speed_group}"
        f"{_reference_speed_label(reference_speed)} {direction}"
    )


def format_split_opposite_time_label(
    speed_group: str,
    *,
    high_reference_speed_kmh: float | None = None,
    low_reference_speed_kmh: float | None = None,
) -> str:
    """Return a public label for opposite-direction mean Delta-t comparison."""
    groups = {
        "high": ("alta", high_reference_speed_kmh),
        "low": ("baixa", low_reference_speed_kmh),
    }
    if speed_group not in groups:
        return str(speed_group)
    group_label, reference_speed = groups[speed_group]
    return (
        f"Dif. médias Δt — Vel. ref. {group_label}"
        f"{_reference_speed_label(reference_speed)}: [+] vs [-]"
    )


def _display_value(value) -> str:
    if value is None or value == "":
        return MISSING_VALUE
    return str(value)


def _component_run(pair: dict, component: str):
    source = pair if isinstance(pair, dict) else {}
    record = source.get(component)
    if isinstance(record, dict):
        run_id = record.get("run_id")
        if run_id not in (None, ""):
            return run_id
    return source.get(f"{component}_run")


def format_run_option_label(record: dict | None) -> str:
    """Return a compact run selector label without direction or timestamp."""
    source = record if isinstance(record, dict) else {}
    run_label = f"Run {_display_value(source.get('run_id'))}"

    delta_t = source.get("delta_t_s")
    try:
        delta_t_value = float(delta_t)
    except (TypeError, ValueError):
        delta_t_value = None
    if delta_t_value is not None and math.isfinite(delta_t_value):
        delta_t_label = f"dt={delta_t_value:.3f}s"
    else:
        delta_t_label = f"dt={MISSING_VALUE}"

    filename = source.get("filename")
    filename_label = str(filename) if filename not in (None, "") else f"File {MISSING_VALUE}"
    return " | ".join((run_label, delta_t_label, filename_label))


def format_split_pair_label(pair: dict | None) -> str:
    """Return the public high/low run composition for a complete Split pair."""
    source = pair if isinstance(pair, dict) else {}
    high_plus = _display_value(_component_run(source, "high_plus"))
    low_plus = _display_value(_component_run(source, "low_plus"))
    high_minus = _display_value(_component_run(source, "high_minus"))
    low_minus = _display_value(_component_run(source, "low_minus"))
    return (
        f"[+]: Run {high_plus} / Run {low_plus} | "
        f"[-]: Run {high_minus} / Run {low_minus}"
    )


def get_split_pair_public_label(pair: dict | None) -> str:
    """Return a saved public label or rebuild it without exposing technical ids."""
    source = pair if isinstance(pair, dict) else {}
    for key in ("pair_label", "public_label", "label"):
        saved = str(source.get(key) or "").strip()
        if saved and not saved.lower().startswith("split_pair_"):
            return saved
    return format_split_pair_label(source).replace(MISSING_VALUE, "-")


# Compatibility alias for code written before the public helper name stabilized.
format_split_pair_public_label = format_split_pair_label

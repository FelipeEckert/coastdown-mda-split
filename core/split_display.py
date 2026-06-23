# coding: utf-8
"""Pure display helpers for Split runs and complete pairs."""

from __future__ import annotations

import math


MISSING_VALUE = "—"


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

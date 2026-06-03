# coding: utf-8
"""Flexible parser helpers for Coastdown Split interval extraction."""

from __future__ import annotations

import math

from core.split_calculations import DEFAULT_SPLIT_INTERVAL_CONFIG, delta_v_kmh


def default_split_interval_config() -> dict:
    """Return a fresh copy of the default Split interval configuration."""
    return {
        "high": dict(DEFAULT_SPLIT_INTERVAL_CONFIG["high"]),
        "low": dict(DEFAULT_SPLIT_INTERVAL_CONFIG["low"]),
    }


def normalize_run_intervals(run_data: dict) -> list[dict]:
    """Convert cumulative or per-interval run timing data to interval rows."""
    if not isinstance(run_data, dict):
        return []

    times = run_data.get("times") or []
    velocities = run_data.get("velocities") or []
    if len(velocities) < 2 or not times:
        return []

    try:
        numeric_times = [float(value) for value in times]
        numeric_velocities = [float(value) for value in velocities]
    except (TypeError, ValueError):
        return []

    if len(numeric_times) == len(numeric_velocities) and abs(numeric_times[0]) < 1e-9:
        interval_times = [
            numeric_times[idx + 1] - numeric_times[idx]
            for idx in range(len(numeric_times) - 1)
        ]
    elif len(numeric_times) == len(numeric_velocities) - 1:
        interval_times = numeric_times
    else:
        return []

    rows = []
    for idx, interval_time in enumerate(interval_times):
        if idx + 1 >= len(numeric_velocities):
            break
        start = numeric_velocities[idx]
        end = numeric_velocities[idx + 1]
        if not math.isfinite(interval_time) or interval_time <= 0:
            continue
        rows.append(
            {
                "start_kmh": start,
                "end_kmh": end,
                "time_s": interval_time,
                "label": f"{start:g}-{end:g}",
            }
        )
    return rows


def _row_inside_interval(row: dict, start_kmh: float, end_kmh: float) -> bool:
    row_start = float(row["start_kmh"])
    row_end = float(row["end_kmh"])
    return row_start <= start_kmh and row_end >= end_kmh and row_start > row_end


def _has_complete_coverage(rows: list[dict], start_kmh: float, end_kmh: float) -> bool:
    """Return True when selected subintervals cover the requested interval exactly."""
    if not rows:
        return False

    tolerance = 1e-9
    ordered = sorted(rows, key=lambda row: float(row["start_kmh"]), reverse=True)
    if abs(float(ordered[0]["start_kmh"]) - start_kmh) > tolerance:
        return False
    if abs(float(ordered[-1]["end_kmh"]) - end_kmh) > tolerance:
        return False

    for current, following in zip(ordered, ordered[1:]):
        if abs(float(current["end_kmh"]) - float(following["start_kmh"])) > tolerance:
            return False
    return True


def extract_interval_record(
    run_id,
    run_data: dict,
    filename: str,
    source_role: str,
    interval_name: str,
    interval_config: dict,
) -> dict | None:
    """Extract one configured Split interval from a run with traceability."""
    start = float(interval_config["start"])
    end = float(interval_config["end"])
    reference = float(interval_config["reference"])
    interval_rows = normalize_run_intervals(run_data)
    used_rows = [row for row in interval_rows if _row_inside_interval(row, start, end)]

    if not used_rows:
        return None

    if not _has_complete_coverage(used_rows, start, end):
        return None

    warnings = []
    delta_t_s = sum(row["time_s"] for row in used_rows)
    if delta_t_s <= 0:
        warnings.append("Extracted Delta t is not greater than zero.")

    return {
        "interval_name": interval_name,
        "run_id": run_id,
        "heading": run_data.get("heading", "N/A"),
        "filename": filename,
        "source_role": source_role,
        "start_kmh": start,
        "end_kmh": end,
        "reference_kmh": reference,
        "delta_v_kmh": delta_v_kmh(start, end),
        "delta_t_s": delta_t_s,
        "subintervals": [row["label"] for row in used_rows],
        "start_timestamp": run_data.get("start_timestamp"),
        "start_time_str": run_data.get("start_time_str"),
        "warnings": warnings,
    }


def parse_split_sources(sources: list[dict], config: dict | None = None) -> dict:
    """Parse all configured Split intervals from one or more loaded CSV sources."""
    interval_config = config or default_split_interval_config()
    parsed = {"high": [], "low": [], "warnings": []}

    if not sources:
        parsed["warnings"].append("No coastdown CSV source was loaded.")
        return parsed

    for source in sources:
        filename = source.get("filename", "N/A")
        role = source.get("role", "coastdown")
        all_run_data = source.get("all_run_data") or {}
        role_text = str(role).lower()
        parse_high = role_text not in {"low", "baixa", "low_speed"}
        parse_low = role_text not in {"high", "alta", "high_speed"}

        for run_id, run_data in all_run_data.items():
            if parse_high:
                high_record = extract_interval_record(
                    run_id,
                    run_data,
                    filename,
                    role,
                    "high",
                    interval_config["high"],
                )
                if high_record:
                    parsed["high"].append(high_record)

            if parse_low:
                low_record = extract_interval_record(
                    run_id,
                    run_data,
                    filename,
                    role,
                    "low",
                    interval_config["low"],
                )
                if low_record:
                    parsed["low"].append(low_record)

    if not parsed["high"]:
        parsed["warnings"].append("No high-speed Split interval was found.")
    if not parsed["low"]:
        parsed["warnings"].append("No low-speed Split interval was found.")

    return parsed

# coding: utf-8
"""Flexible parser helpers for Coastdown Split interval extraction."""

from __future__ import annotations

import math
import re

from core.split_calculations import DEFAULT_SPLIT_INTERVAL_CONFIG, delta_v_kmh


def default_split_interval_config() -> dict:
    """Return a fresh copy of the default Split interval configuration."""
    return {
        "step_kmh": float(DEFAULT_SPLIT_INTERVAL_CONFIG["step_kmh"]),
        "high": dict(DEFAULT_SPLIT_INTERVAL_CONFIG["high"]),
        "low": dict(DEFAULT_SPLIT_INTERVAL_CONFIG["low"]),
    }


def normalize_split_interval_config(config: dict | None) -> dict:
    """Return a complete Split interval config, including legacy defaults."""
    normalized = default_split_interval_config()
    if not isinstance(config, dict):
        return normalized

    if "step_kmh" in config:
        normalized["step_kmh"] = config["step_kmh"]
    for interval_name in ("high", "low"):
        interval = config.get(interval_name)
        if isinstance(interval, dict):
            normalized[interval_name].update(interval)
    return normalized


def validate_split_interval_config(config: dict | None) -> list[dict]:
    """Validate interval geometry and return structured, user-facing issues."""
    normalized = normalize_split_interval_config(config)
    issues = []

    try:
        step_kmh = float(normalized["step_kmh"])
    except (TypeError, ValueError):
        step_kmh = math.nan

    if not math.isfinite(step_kmh) or step_kmh <= 0:
        return [
            {
                "code": "invalid_step",
                "message": "Coastdown interval step must be greater than zero.",
            }
        ]

    for interval_name in ("high", "low"):
        interval = normalized[interval_name]
        try:
            start = float(interval["start"])
            end = float(interval["end"])
            reference = float(interval["reference"])
        except (KeyError, TypeError, ValueError):
            issues.append(
                {
                    "code": "invalid_interval_values",
                    "interval": interval_name,
                    "message": f"{interval_name.title()} interval values must be numeric.",
                }
            )
            continue

        if not all(math.isfinite(value) for value in (start, end, reference)):
            issues.append(
                {
                    "code": "invalid_interval_values",
                    "interval": interval_name,
                    "message": f"{interval_name.title()} interval values must be finite.",
                }
            )
            continue
        if not start > end:
            issues.append(
                {
                    "code": "invalid_interval_order",
                    "interval": interval_name,
                    "message": f"{interval_name.title()} interval start must be greater than end.",
                }
            )
            continue
        if not start > reference > end:
            issues.append(
                {
                    "code": "invalid_reference",
                    "interval": interval_name,
                    "message": (
                        f"{interval_name.title()} reference speed must be between "
                        "the interval start and end."
                    ),
                }
            )

        span_kmh = start - end
        step_count = span_kmh / step_kmh
        if not math.isclose(step_count, round(step_count), rel_tol=0.0, abs_tol=1e-9):
            issues.append(
                {
                    "code": "incompatible_step",
                    "interval": interval_name,
                    "span_kmh": span_kmh,
                    "step_kmh": step_kmh,
                    "message": (
                        f"{interval_name.title()} interval span ({span_kmh:g} km/h) "
                        f"must be an exact multiple of the configured step ({step_kmh:g} km/h)."
                    ),
                }
            )

    return issues


def required_subintervals(
    start_kmh: float,
    end_kmh: float,
    step_kmh: float,
) -> list[tuple[float, float]]:
    """Build the exact descending speed bins required by the configured step."""
    span_kmh = float(start_kmh) - float(end_kmh)
    count = int(round(span_kmh / float(step_kmh)))
    return [
        (
            float(start_kmh) - index * float(step_kmh),
            float(start_kmh) - (index + 1) * float(step_kmh),
        )
        for index in range(count)
    ]


def format_speed_bin(start_kmh: float, end_kmh: float) -> str:
    """Return a stable human-readable label for one speed bin."""
    return f"{float(start_kmh):g}-{float(end_kmh):g}"


def parse_speed_bin_label(label) -> tuple[float, float] | None:
    """Parse an explicit interval label such as 100-90 or 100 -> 90."""
    text = str(label or "").strip()
    if not text:
        return None

    normalized = (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2192", "->")
    )
    match = re.search(
        r"(?<![\d.])(-?\d+(?:[.,]\d+)?)\s*(?:->|-|to)\s*(-?\d+(?:[.,]\d+)?)(?![\d.])",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    start = float(match.group(1).replace(",", "."))
    end = float(match.group(2).replace(",", "."))
    if not start > end:
        return None
    return start, end


def _rows_from_interval_measurements(
    run_data: dict,
    expected_bins: list[tuple[float, float]] | None,
    source_role: str | None,
    interval_name: str | None,
) -> tuple[list[dict], list[str]]:
    """Normalize labeled columns or role-controlled unlabeled Split columns."""
    measurements = run_data.get("interval_measurements") or []
    if not measurements:
        return [], []

    labeled_rows = []
    unlabeled_measurements = []
    available_labels = []
    for measurement in measurements:
        label = measurement.get("label") or measurement.get("column") or ""
        parsed_label = parse_speed_bin_label(label)
        try:
            time_s = float(measurement.get("time_s"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(time_s) or time_s <= 0:
            continue

        if parsed_label:
            start, end = parsed_label
            bin_label = format_speed_bin(start, end)
            labeled_rows.append(
                {
                    "start_kmh": start,
                    "end_kmh": end,
                    "time_s": time_s,
                    "label": bin_label,
                    "source_column": measurement.get("column"),
                }
            )
            available_labels.append(bin_label)
        else:
            unlabeled_measurements.append(measurement)
            available_labels.append(str(label or "unlabeled"))

    if labeled_rows:
        return labeled_rows, available_labels

    role_text = str(source_role or "").lower()
    role_matches_interval = (
        interval_name == "high"
        and role_text in {"high", "alta", "high_speed"}
    ) or (
        interval_name == "low"
        and role_text in {"low", "baixa", "low_speed"}
    )
    if not role_matches_interval or not expected_bins:
        return [], available_labels

    configured_start = expected_bins[0][0]
    configured_step = expected_bins[0][0] - expected_bins[0][1]
    rows = []
    for index, measurement in enumerate(unlabeled_measurements):
        try:
            time_s = float(measurement.get("time_s"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(time_s) or time_s <= 0:
            continue
        start = configured_start - index * configured_step
        end = start - configured_step
        rows.append(
            {
                "start_kmh": start,
                "end_kmh": end,
                "time_s": time_s,
                "label": format_speed_bin(start, end),
                "source_column": measurement.get("column"),
            }
        )
    return rows, [row["label"] for row in rows]


def normalize_run_intervals(
    run_data: dict,
    expected_bins: list[tuple[float, float]] | None = None,
    source_role: str | None = None,
    interval_name: str | None = None,
) -> list[dict]:
    """Convert cumulative or per-interval run timing data to interval rows."""
    if not isinstance(run_data, dict):
        return []

    measurement_rows, _ = _rows_from_interval_measurements(
        run_data,
        expected_bins,
        source_role,
        interval_name,
    )
    if run_data.get("interval_measurements") is not None:
        return measurement_rows

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
                "label": format_speed_bin(start, end),
            }
        )
    return rows


def inspect_interval_coverage(
    rows: list[dict],
    expected_bins: list[tuple[float, float]],
) -> dict:
    """Return exact expected/found/missing bin coverage for one run."""
    matched_rows = []
    missing_bins = []
    for expected_start, expected_end in expected_bins:
        matches = [
            row
            for row in rows
            if math.isclose(
                float(row["start_kmh"]),
                expected_start,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
            and math.isclose(
                float(row["end_kmh"]),
                expected_end,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
        ]
        if len(matches) != 1:
            missing_bins.append((expected_start, expected_end))
        else:
            matched_rows.append(matches[0])

    return {
        "complete": not missing_bins,
        "expected": [format_speed_bin(*speed_bin) for speed_bin in expected_bins],
        "found": list(dict.fromkeys(row["label"] for row in rows)),
        "missing": [format_speed_bin(*speed_bin) for speed_bin in missing_bins],
        "matched_rows": matched_rows,
    }


def extract_interval_record(
    run_id,
    run_data: dict,
    filename: str,
    source_role: str,
    interval_name: str,
    interval_config: dict,
    step_kmh: float,
) -> dict | None:
    """Extract one configured Split interval from a run with traceability."""
    start = float(interval_config["start"])
    end = float(interval_config["end"])
    reference = float(interval_config["reference"])
    expected_bins = required_subintervals(start, end, step_kmh)
    interval_rows = normalize_run_intervals(
        run_data,
        expected_bins,
        source_role,
        interval_name,
    )
    coverage = inspect_interval_coverage(interval_rows, expected_bins)
    if not coverage["complete"]:
        return None
    used_rows = coverage["matched_rows"]

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
        "step_kmh": float(step_kmh),
        "delta_v_kmh": delta_v_kmh(start, end),
        "delta_t_s": delta_t_s,
        "subintervals": [row["label"] for row in used_rows],
        "source_columns": [row.get("source_column") for row in used_rows],
        "start_timestamp": run_data.get("start_timestamp"),
        "start_time_str": run_data.get("start_time_str"),
        "warnings": warnings,
    }


def parse_split_sources(sources: list[dict], config: dict | None = None) -> dict:
    """Parse all configured Split intervals from one or more loaded CSV sources."""
    interval_config = normalize_split_interval_config(config)
    parsed = {"high": [], "low": [], "warnings": []}

    config_issues = validate_split_interval_config(interval_config)
    if config_issues:
        parsed["warnings"].extend(issue["message"] for issue in config_issues)
        return parsed

    if not sources:
        parsed["warnings"].append("No coastdown CSV source was loaded.")
        return parsed

    step_kmh = float(interval_config["step_kmh"])
    for source in sources:
        filename = source.get("filename", "N/A")
        role = source.get("role", "coastdown")
        all_run_data = source.get("all_run_data") or {}
        role_text = str(role).lower()
        parse_high = role_text not in {"low", "baixa", "low_speed"}
        parse_low = role_text not in {"high", "alta", "high_speed"}

        for run_id, run_data in all_run_data.items():
            if parse_high:
                high_expected = required_subintervals(
                    interval_config["high"]["start"],
                    interval_config["high"]["end"],
                    step_kmh,
                )
                high_record = extract_interval_record(
                    run_id,
                    run_data,
                    filename,
                    role,
                    "high",
                    interval_config["high"],
                    step_kmh,
                )
                if high_record:
                    parsed["high"].append(high_record)
                else:
                    high_rows = normalize_run_intervals(
                        run_data,
                        high_expected,
                        role,
                        "high",
                    )
                    coverage = inspect_interval_coverage(high_rows, high_expected)
                    parsed["warnings"].append(
                        _coverage_warning(
                            filename,
                            run_id,
                            "high",
                            coverage,
                            run_data,
                            role,
                        )
                    )

            if parse_low:
                low_expected = required_subintervals(
                    interval_config["low"]["start"],
                    interval_config["low"]["end"],
                    step_kmh,
                )
                low_record = extract_interval_record(
                    run_id,
                    run_data,
                    filename,
                    role,
                    "low",
                    interval_config["low"],
                    step_kmh,
                )
                if low_record:
                    parsed["low"].append(low_record)
                else:
                    low_rows = normalize_run_intervals(
                        run_data,
                        low_expected,
                        role,
                        "low",
                    )
                    coverage = inspect_interval_coverage(low_rows, low_expected)
                    parsed["warnings"].append(
                        _coverage_warning(
                            filename,
                            run_id,
                            "low",
                            coverage,
                            run_data,
                            role,
                        )
                    )

    if not parsed["high"]:
        parsed["warnings"].append("No high-speed Split interval was found.")
    if not parsed["low"]:
        parsed["warnings"].append("No low-speed Split interval was found.")

    return parsed


def _coverage_warning(
    filename: str,
    run_id,
    interval_name: str,
    coverage: dict,
    run_data: dict,
    source_role: str,
) -> str:
    """Build a controlled coverage warning with full bin traceability."""
    expected_text = ", ".join(coverage["expected"]) or "none"
    found_text = ", ".join(coverage["found"]) or "none"
    missing_text = ", ".join(coverage["missing"]) or "none"
    role_text = str(source_role or "").lower()
    measurements = run_data.get("interval_measurements") or []
    has_explicit_labels = any(
        parse_speed_bin_label(item.get("label") or item.get("column"))
        for item in measurements
    )
    label_note = ""
    if measurements and not has_explicit_labels and role_text in {
        "full_or_combined",
        "combined",
        "single_combined",
    }:
        label_note = " Combined input has no identifiable speed-bin labels."
    return (
        f"{filename} run {run_id} {interval_name}: expected bins [{expected_text}]; "
        f"found [{found_text}]; missing [{missing_text}].{label_note}"
    )

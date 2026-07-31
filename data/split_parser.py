# coding: utf-8
"""Flexible parser helpers for Coastdown Split interval extraction."""

from __future__ import annotations

import math
import re

from core.split_calculations import DEFAULT_SPLIT_INTERVAL_CONFIG, delta_v_kmh


_HIGH_SOURCE_ROLES = {"high", "alta", "high_speed"}
_LOW_SOURCE_ROLES = {"low", "baixa", "low_speed"}
_COMBINED_SOURCE_ROLES = {"full_or_combined", "combined", "single_combined"}


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


def _unnamed_column_positions(measurements: list[dict]) -> list[int] | None:
    """Return exact VBOX unnamed-column positions, or None for mixed columns."""
    positions = []
    for measurement in measurements:
        match = re.fullmatch(
            r"unnamed_col_(\d+)",
            str(measurement.get("column") or ""),
        )
        if not match:
            return None
        positions.append(int(match.group(1)))
    return positions


def _populated_interval_measurements(measurements: list[dict]) -> list[dict]:
    """Return only measurements that contain a usable positive time."""
    populated = []
    for measurement in measurements:
        try:
            time_s = float(measurement.get("time_s"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(time_s) and time_s > 0:
            populated.append(measurement)
    return populated


def _ranges_for_interval(rows, expected_ranges):
    """Return populated ranges located inside one configured interval."""
    start = expected_ranges[0][0]
    end = expected_ranges[-1][1]
    return tuple(
        (float(row["start_kmh"]), float(row["end_kmh"]))
        for row in rows
        if float(row["start_kmh"]) <= start
        and float(row["end_kmh"]) >= end
    )


def _classify_split_run(run_data, source_role, expected):
    """Classify one run once and prepare valid combined positional columns."""
    role_text = str(source_role or "").lower()
    if role_text in _HIGH_SOURCE_ROLES:
        return ("high",), run_data
    if role_text in _LOW_SOURCE_ROLES:
        return ("low",), run_data

    measurements = run_data.get("interval_measurements")
    if measurements is None:
        rows = normalize_run_intervals(run_data)
        return tuple(
            interval_name
            for interval_name in ("high", "low")
            if _ranges_for_interval(rows, expected[interval_name])
        ), run_data

    populated = _populated_interval_measurements(measurements)
    labels = [
        parse_speed_bin_label(item.get("label") or item.get("column"))
        for item in populated
    ]
    found_ranges = tuple(label for label in labels if label)
    if found_ranges:
        if len(found_ranges) != len(populated):
            return (), run_data
        rows = [
            {"start_kmh": start, "end_kmh": end}
            for start, end in found_ranges
        ]
        return tuple(
            interval_name
            for interval_name in ("high", "low")
            if _ranges_for_interval(rows, expected[interval_name])
        ), run_data

    positions = _unnamed_column_positions(populated)
    high_positions = list(range(len(expected["high"])))
    low_positions = list(
        range(len(expected["high"]), len(expected["high"]) + len(expected["low"]))
    )
    if not positions or positions == high_positions + low_positions:
        return (), run_data
    if positions[0] == 0:
        interval_name = "high"
        expected_positions = high_positions
    elif positions[0] == len(expected["high"]):
        interval_name = "low"
        expected_positions = low_positions
    else:
        return (), run_data
    if positions != expected_positions:
        return (interval_name,), run_data

    return (interval_name,), {
        **run_data,
        "interval_measurements": [
            {**measurement, "label": format_speed_bin(*speed_bin)}
            for measurement, speed_bin in zip(populated, expected[interval_name])
        ],
    }


def _source_consistency_issue(
    interval_name,
    expected_ranges,
    found_count,
    filename,
    run_id,
    *,
    found_ranges=(),
    expected_positions=(),
    found_positions=(),
) -> dict:
    """Build one concise blocking issue for the first structural mismatch."""
    if interval_name:
        detail = f"{interval_name.title()}: {len(expected_ranges)} expected, {found_count} found"
        if found_ranges and tuple(found_ranges) != tuple(expected_ranges):
            detail += (
                f"; expected [{', '.join(format_speed_bin(*item) for item in expected_ranges)}], "
                f"found [{', '.join(format_speed_bin(*item) for item in found_ranges)}]"
            )
        if found_positions:
            detail += (
                f"; expected columns [{', '.join(map(str, expected_positions))}], "
                f"found [{', '.join(map(str, found_positions))}]"
            )
    else:
        detail = f"Ambiguous interval structure: {found_count} populated columns"
    return {
        "code": "source_interval_mismatch",
        "interval": interval_name,
        "message": (
            f"Split intervals differ from the loaded file. {detail}. "
            f"Affected: {filename} run {run_id}."
        ),
    }


def validate_split_source_consistency(
    sources: list[dict],
    config: dict | None = None,
) -> list[dict]:
    """Return the first fixed-column/configuration mismatch before parsing."""
    interval_config = normalize_split_interval_config(config)
    issues = validate_split_interval_config(interval_config)
    if issues:
        return issues

    step_kmh = float(interval_config["step_kmh"])
    expected = {
        name: required_subintervals(
            interval_config[name]["start"],
            interval_config[name]["end"],
            step_kmh,
        )
        for name in ("high", "low")
    }
    source_issues = {}

    def add_issue(issue):
        source_issues.setdefault(issue["interval"] or "ambiguous", issue)

    for source in sources or []:
        filename = source.get("filename", "N/A")
        role_text = str(source.get("role", "")).lower()
        if role_text in _HIGH_SOURCE_ROLES:
            source_interval = "high"
        elif role_text in _LOW_SOURCE_ROLES:
            source_interval = "low"
        elif role_text in _COMBINED_SOURCE_ROLES:
            source_interval = None
        else:
            continue

        for run_id, run_data in (source.get("all_run_data") or {}).items():
            measurements = run_data.get("interval_measurements")
            populated = (
                _populated_interval_measurements(measurements)
                if measurements is not None
                else None
            )
            if measurements is not None and not populated:
                continue

            run_intervals, _ = _classify_split_run(run_data, role_text, expected)
            if not run_intervals:
                found_count = len(populated or normalize_run_intervals(run_data))
                add_issue(_source_consistency_issue(
                    None,
                    (),
                    found_count,
                    filename,
                    run_id,
                ))
                continue

            if measurements is None:
                rows = normalize_run_intervals(run_data)
                for interval_name in run_intervals:
                    found_ranges = _ranges_for_interval(rows, expected[interval_name])
                    if found_ranges != tuple(expected[interval_name]):
                        add_issue(_source_consistency_issue(
                            interval_name,
                            expected[interval_name],
                            len(found_ranges),
                            filename,
                            run_id,
                            found_ranges=found_ranges,
                        ))
                continue

            labels = [
                parse_speed_bin_label(item.get("label") or item.get("column"))
                for item in populated
            ]
            found_ranges = tuple(label for label in labels if label)
            if len(found_ranges) == len(populated):
                rows = [
                    {"start_kmh": start, "end_kmh": end}
                    for start, end in found_ranges
                ]
                matched_count = 0
                for interval_name in run_intervals:
                    interval_ranges = _ranges_for_interval(
                        rows,
                        expected[interval_name],
                    )
                    matched_count += len(interval_ranges)
                    if interval_ranges != tuple(expected[interval_name]):
                        add_issue(_source_consistency_issue(
                            interval_name,
                            expected[interval_name],
                            len(interval_ranges),
                            filename,
                            run_id,
                            found_ranges=interval_ranges,
                        ))
                if matched_count != len(found_ranges):
                    add_issue(_source_consistency_issue(
                        None,
                        (),
                        len(populated),
                        filename,
                        run_id,
                        found_ranges=found_ranges,
                    ))
                continue

            if found_ranges:
                add_issue(_source_consistency_issue(None, (), len(populated), filename, run_id))
                continue
            if source_interval:
                if len(populated) != len(expected[source_interval]):
                    add_issue(_source_consistency_issue(
                        source_interval,
                        expected[source_interval],
                        len(populated),
                        filename,
                        run_id,
                    ))
                continue

            positions = _unnamed_column_positions(populated)
            high_positions = list(range(len(expected["high"])))
            low_positions = list(
                range(len(expected["high"]), len(expected["high"]) + len(expected["low"]))
            )
            interval_name = run_intervals[0] if len(run_intervals) == 1 else None
            expected_positions = (
                high_positions if interval_name == "high" else low_positions
            ) if interval_name else ()
            if positions == expected_positions:
                continue
            add_issue(_source_consistency_issue(
                interval_name,
                expected.get(interval_name, ()),
                len(populated),
                filename,
                run_id,
                expected_positions=expected_positions,
                found_positions=positions or (),
            ))

    return list(source_issues.values())


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
        interval_name == "high" and role_text in _HIGH_SOURCE_ROLES
    ) or (
        interval_name == "low" and role_text in _LOW_SOURCE_ROLES
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
        "subinterval_times_s": [row["time_s"] for row in used_rows],
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
    expected = {
        interval_name: required_subintervals(
            interval_config[interval_name]["start"],
            interval_config[interval_name]["end"],
            step_kmh,
        )
        for interval_name in ("high", "low")
    }
    for source in sources:
        filename = source.get("filename", "N/A")
        role = source.get("role", "coastdown")
        all_run_data = source.get("all_run_data") or {}

        for run_id, run_data in all_run_data.items():
            run_intervals, classified_run_data = _classify_split_run(
                run_data,
                role,
                expected,
            )
            for interval_name in run_intervals or ("high", "low"):
                record = extract_interval_record(
                    run_id,
                    classified_run_data,
                    filename,
                    role,
                    interval_name,
                    interval_config[interval_name],
                    step_kmh,
                )
                if record:
                    parsed[interval_name].append(record)
                else:
                    rows = normalize_run_intervals(
                        classified_run_data,
                        expected[interval_name],
                        role,
                        interval_name,
                    )
                    coverage = inspect_interval_coverage(
                        rows,
                        expected[interval_name],
                    )
                    parsed["warnings"].append(
                        _coverage_warning(
                            filename,
                            run_id,
                            interval_name,
                            coverage,
                            classified_run_data,
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
    if measurements and not has_explicit_labels and role_text in _COMBINED_SOURCE_ROLES:
        label_note = " Combined input has no identifiable speed-bin labels."
    return (
        f"{filename} run {run_id} {interval_name}: expected bins [{expected_text}]; "
        f"found [{found_text}]; missing [{missing_text}].{label_note}"
    )

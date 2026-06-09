# coding: utf-8
"""Pure, method-neutral weather synchronization helpers."""

from __future__ import annotations

import re
from datetime import datetime, time

import pandas as pd


DEFAULT_MAX_TIME_DELTA_SECONDS = 300


def _seconds_since_midnight(value: datetime | time) -> float:
    value_time = value.time() if isinstance(value, datetime) else value
    return (
        value_time.hour * 3600
        + value_time.minute * 60
        + value_time.second
        + value_time.microsecond / 1_000_000
    )


def _clock_delta_seconds(first: datetime | time, second: datetime | time) -> float:
    delta = abs(_seconds_since_midnight(first) - _seconds_since_midnight(second))
    return min(delta, 86400.0 - delta)


def _ambiguous_date_string(value: str) -> bool:
    match = re.match(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
    if not match:
        return False
    first = int(match.group(1))
    second = int(match.group(2))
    return first <= 12 and second <= 12 and first != second


def _parse_run_datetime(value) -> tuple[datetime | time | None, list[str]]:
    if isinstance(value, dict):
        value = value.get("start_timestamp") or value.get("start_time_str")
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime(), []
    if isinstance(value, (datetime, time)):
        return value, []
    if value is None:
        return None, ["Run timestamp is not available."]

    text = str(value).strip().replace(",", ".")
    if not text:
        return None, ["Run timestamp is not available."]

    warnings = []
    if _ambiguous_date_string(text):
        warnings.append(
            f"Ambiguous run date '{text}' was interpreted using day-first order."
        )

    if re.match(r"^\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?$", text):
        for pattern in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, pattern).time(), warnings
            except ValueError:
                continue

    iso_order = bool(re.match(r"^\d{4}-\d{1,2}-\d{1,2}", text))
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=not iso_order)
    if pd.isna(parsed):
        return None, warnings + [f"Run timestamp '{text}' could not be parsed."]
    return parsed.to_pydatetime(), warnings


def _weather_records(weather_df) -> list[dict]:
    if weather_df is None:
        return []
    if isinstance(weather_df, pd.DataFrame):
        records = weather_df.to_dict("records")
    else:
        records = list(weather_df)

    valid = []
    for record in records:
        if not isinstance(record, dict):
            continue
        timestamp = record.get("timestamp") or record.get("weather_datetime")
        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        if isinstance(timestamp, datetime):
            normalized = dict(record)
            normalized["timestamp"] = timestamp
            valid.append(normalized)
    return valid


def _empty_result(run_value, warnings: list[str]) -> dict:
    return {
        "matched": False,
        "sync_method": "not_found",
        "run_datetime": run_value,
        "weather_datetime": None,
        "time_delta_seconds": None,
        "temperature": None,
        "pressure": None,
        "wind_speed": None,
        "wind_direction": None,
        "warnings": warnings,
        "weather_record": None,
    }


def _matched_result(
    run_value,
    record: dict,
    delta_seconds: float,
    method: str,
    warnings: list[str],
) -> dict:
    record_warnings = list(record.get("warnings") or [])
    timezone = record.get("timezone")
    if timezone is None:
        record_warnings.append(
            "Weather timezone is not declared; timestamps were compared as local time."
        )
    return {
        "matched": True,
        "sync_method": method,
        "run_datetime": run_value,
        "weather_datetime": record.get("timestamp"),
        "time_delta_seconds": float(delta_seconds),
        "temperature": record.get("temp_c"),
        "pressure": record.get("baro_kpa"),
        "wind_speed": record.get("wind_ms"),
        "wind_direction": record.get("wind_direction"),
        "warnings": warnings + record_warnings,
        "weather_record": record,
    }


def _closest(candidates: list[tuple[float, dict]]) -> tuple[float, dict, bool]:
    ordered = sorted(candidates, key=lambda item: item[0])
    best_delta, best_record = ordered[0]
    tied = sum(1 for delta, _ in ordered if abs(delta - best_delta) < 1e-9) > 1
    return best_delta, best_record, tied


def sync_weather_to_run(
    run_datetime,
    weather_df,
    max_time_delta_seconds: float = DEFAULT_MAX_TIME_DELTA_SECONDS,
    allow_time_only_fallback: bool = True,
) -> dict:
    """Synchronize one run to the closest weather record with full audit data."""
    parsed_run, warnings = _parse_run_datetime(run_datetime)
    if parsed_run is None:
        return _empty_result(parsed_run, warnings)

    try:
        max_delta = float(max_time_delta_seconds)
    except (TypeError, ValueError):
        max_delta = -1.0
    if max_delta < 0:
        return _empty_result(
            parsed_run,
            warnings + ["Maximum weather synchronization delta must be non-negative."],
        )

    records = _weather_records(weather_df)
    if not records:
        return _empty_result(parsed_run, warnings + ["No valid weather records are available."])

    if isinstance(parsed_run, datetime):
        datetime_candidates = [
            (abs((record["timestamp"] - parsed_run).total_seconds()), record)
            for record in records
            if (record["timestamp"].tzinfo is None) == (parsed_run.tzinfo is None)
        ]
        if datetime_candidates:
            delta, record, tied = _closest(datetime_candidates)
            if delta <= max_delta:
                if tied:
                    warnings.append(
                        "Multiple weather records were equally close; the first source record was selected."
                    )
                return _matched_result(parsed_run, record, delta, "datetime", warnings)

        if not allow_time_only_fallback:
            nearest_delta = min((item[0] for item in datetime_candidates), default=None)
            detail = (
                f"Closest weather record is {nearest_delta:.1f} s away, above the "
                f"{max_delta:.1f} s limit."
                if nearest_delta is not None
                else "No timezone-compatible weather timestamp is available."
            )
            return _empty_result(parsed_run, warnings + [detail])

        fallback_candidates = [
            (_clock_delta_seconds(parsed_run, record["timestamp"]), record)
            for record in records
        ]
        delta, record, tied = _closest(fallback_candidates)
        if delta <= max_delta:
            warnings.append(
                "Weather date differs from the run date; synchronization used time of day only."
            )
            if tied:
                warnings.append(
                    "Multiple weather records were equally close; the first source record was selected."
                )
            return _matched_result(parsed_run, record, delta, "time_only", warnings)
        return _empty_result(
            parsed_run,
            warnings
            + [
                f"No weather record is within {max_delta:.1f} s, including time-only fallback."
            ],
        )

    if not allow_time_only_fallback:
        return _empty_result(
            parsed_run,
            warnings
            + ["Run date is unavailable and time-only fallback is disabled."],
        )

    candidates = [
        (_clock_delta_seconds(parsed_run, record["timestamp"]), record)
        for record in records
    ]
    delta, record, tied = _closest(candidates)
    if delta <= max_delta:
        warnings.append(
            "Run date is unavailable; weather date was assumed from the closest time of day."
        )
        if tied:
            warnings.append(
                "Multiple weather records were equally close; the first source record was selected."
            )
        return _matched_result(
            parsed_run,
            record,
            delta,
            "manual_date_assumption",
            warnings,
        )
    return _empty_result(
        parsed_run,
        warnings + [f"No weather record is within the {max_delta:.1f} s time-only limit."],
    )

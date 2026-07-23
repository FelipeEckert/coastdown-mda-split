# coding: utf-8
"""Neutral weather-file loading and normalization helpers."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import chardet
import pandas as pd


DATETIME_ALIASES = {
    "time",
    "timestamp",
    "datetime",
    "date_time",
    "data_hora",
    "datahora",
}
DATE_ALIASES = {"date", "data"}
TIME_ALIASES = {"hour", "hora", "time_only", "horario"}
TEMPERATURE_ALIASES = {
    "temp",
    "temperature",
    "temperatura",
    "air_temp",
    "air_temperature",
}
PRESSURE_ALIASES = {
    "baro",
    "barometer",
    "pressure",
    "pressao",
    "barometric_pressure",
    "station_p",
}
WIND_SPEED_ALIASES = {
    "wind_speed",
    "windspeed",
    "velocidade_vento",
    "vento",
}
WIND_DIRECTION_ALIASES = {
    "true_dir",
    "true_direction",
    "wind_direction",
    "direcao_vento",
    "mag_dir",
    "mag_direction",
}
WIND_UNIT_MS = "m/s"
WIND_UNIT_KMH = "km/h"


def _normalize_column_name(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def _detect_encoding(path: Path) -> str:
    raw = path.read_bytes()[:65536]
    return chardet.detect(raw).get("encoding") or "utf-8"


def _find_header_index(rows: list[list]) -> int:
    for index, row in enumerate(rows):
        normalized = {_normalize_column_name(value) for value in row}
        has_datetime = bool(normalized & (DATETIME_ALIASES | DATE_ALIASES))
        has_temp = bool(normalized & TEMPERATURE_ALIASES)
        has_pressure = bool(normalized & PRESSURE_ALIASES)
        if has_datetime and has_temp and has_pressure:
            return index
    raise ValueError("Weather header with datetime, temperature and pressure was not found.")


def _detect_csv_layout(path: Path, encoding: str) -> tuple[str, int]:
    text = path.read_text(encoding=encoding, errors="replace")
    lines = text.splitlines()
    delimiters = (",", ";", "\t", "|")

    for index, line in enumerate(lines[:100]):
        delimiter = max(delimiters, key=line.count)
        if line.count(delimiter) < 2:
            continue
        row = next(csv.reader([line], delimiter=delimiter))
        normalized = {_normalize_column_name(value) for value in row}
        if (
            normalized & (DATETIME_ALIASES | DATE_ALIASES)
            and normalized & TEMPERATURE_ALIASES
            and normalized & PRESSURE_ALIASES
        ):
            return delimiter, index
    raise ValueError("Weather CSV header with datetime, temperature and pressure was not found.")


def _read_csv(path: Path) -> pd.DataFrame:
    encoding = _detect_encoding(path)
    delimiter, header_index = _detect_csv_layout(path, encoding)
    return pd.read_csv(
        path,
        skiprows=header_index,
        header=0,
        sep=delimiter,
        encoding=encoding,
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )


def _read_xlsx(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None, dtype=object)
    header_index = _find_header_index(raw.fillna("").values.tolist())
    frame = raw.iloc[header_index + 1 :].copy()
    frame.columns = [str(value) for value in raw.iloc[header_index].tolist()]
    return frame.reset_index(drop=True)


def _find_column(columns: dict[str, str], aliases: set[str]) -> str | None:
    for normalized, original in columns.items():
        if normalized in aliases:
            return original
    return None


def _find_column_with_unit(
    columns: dict[str, str],
    aliases: set[str],
) -> str | None:
    """Find a column whose normalized suffix may declare a unit."""
    for normalized, original in columns.items():
        if normalized in aliases or any(
            normalized.startswith(f"{alias}_") for alias in aliases
        ):
            return original
    return None


def _numeric(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    elif "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _numeric_status(value) -> tuple[float | None, str]:
    """Return a numeric value and distinguish missing from invalid input."""
    if value is None or pd.isna(value) or not str(value).strip():
        return None, "missing"
    numeric = _numeric(value)
    return (numeric, "valid") if numeric is not None else (None, "invalid")


def _unit_row(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Remove an optional units row and return its values by source column."""
    if frame.empty:
        return frame, {}
    first = frame.iloc[0]

    def cell_text(value) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    first_values = {
        str(column): cell_text(first.get(column))
        for column in frame.columns
    }
    time_hint = next(
        (
            value.lower()
            for column, value in first_values.items()
            if _normalize_column_name(column) in DATETIME_ALIASES
        ),
        "",
    )
    unit_tokens = {
        _normalize_column_name(value)
        for value in first_values.values()
        if value
    }
    looks_like_units = (
        "yyyy" in time_hint
        or bool(unit_tokens & {"m_s", "km_h", "celsius", "degrees", "mb", "kpa"})
    )
    if not looks_like_units:
        return frame, {}
    return frame.iloc[1:].copy(), first_values


def _wind_unit(column_name: str | None, declared_unit: str | None) -> str | None:
    """Identify supported wind units from the units row or column label."""
    text = " ".join(
        value for value in (declared_unit, column_name) if value
    ).lower()
    normalized = _normalize_column_name(text)
    if (
        re.search(r"\bkm\s*/\s*h\b", text)
        or "km_h" in normalized
        or "kmh" in normalized
        or "kph" in normalized
    ):
        return WIND_UNIT_KMH
    if re.search(r"\bm\s*/\s*s\b", text) or "m_s" in normalized or "mps" in normalized:
        return WIND_UNIT_MS
    return None


def _wind_value_ms(
    raw_value,
    unit: str | None,
    source_column: str | None,
) -> tuple[float | None, list[str]]:
    """Normalize one wind value to m/s without converting absence into zero."""
    warnings = []
    value, status = _numeric_status(raw_value)
    if source_column is None:
        return None, ["Wind speed column was not found."]
    if status == "missing":
        return None, ["Wind speed is missing."]
    if status == "invalid":
        return None, [f"Wind speed value '{raw_value}' is invalid and was not used."]
    if unit == WIND_UNIT_MS:
        return value, warnings
    if unit == WIND_UNIT_KMH:
        warnings.append("Wind speed was converted from km/h to m/s.")
        return value / 3.6, warnings
    return None, [
        f"Wind speed unit for column '{source_column}' is unknown; "
        "the value was not used."
    ]


def _date_is_ambiguous(value) -> bool:
    match = re.match(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", str(value or ""))
    if not match:
        return False
    first = int(match.group(1))
    second = int(match.group(2))
    return first <= 12 and second <= 12 and first != second


def _parse_datetime(value) -> tuple[object | None, list[str]]:
    if value is None or pd.isna(value):
        return None, []
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime(), []

    text = str(value).strip()
    if not text:
        return None, []

    warnings = []
    if _date_is_ambiguous(text):
        warnings.append(
            f"Ambiguous date '{text}' was interpreted using day-first order."
        )

    iso_order = bool(re.match(r"^\d{4}-\d{1,2}-\d{1,2}", text))
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=not iso_order)
    if pd.isna(parsed):
        return None, warnings
    return parsed.to_pydatetime(), warnings


def _parse_datetime_series(values) -> list[tuple[object | None, list[str]]]:
    """Parse weather timestamps in ISO/day-first batches with scalar fallback."""
    source = list(values)
    if int(pd.__version__.split(".", 1)[0]) < 2:
        return [_parse_datetime(value) for value in source]

    parsed_values = [(None, []) for _ in source]
    groups = {True: [], False: []}
    for index, value in enumerate(source):
        if value is None or pd.isna(value):
            continue
        if isinstance(value, pd.Timestamp):
            parsed_values[index] = (value.to_pydatetime(), [])
            continue

        text = str(value).strip()
        if not text:
            continue
        warnings = []
        if _date_is_ambiguous(text):
            warnings.append(
                f"Ambiguous date '{text}' was interpreted using day-first order."
            )
        parsed_values[index] = (None, warnings)
        iso_order = bool(re.match(r"^\d{4}-\d{1,2}-\d{1,2}", text))
        groups[iso_order].append((index, text))

    for iso_order, items in groups.items():
        if not items:
            continue
        indexes, texts = zip(*items)
        try:
            parsed = pd.to_datetime(
                pd.Series(texts, index=indexes),
                errors="coerce",
                dayfirst=not iso_order,
                format="mixed",
            )
        except (TypeError, ValueError):
            for index, text in items:
                parsed_values[index] = _parse_datetime(text)
            continue
        for index, value in parsed.items():
            parsed_values[index] = (
                None if pd.isna(value) else value.to_pydatetime(),
                parsed_values[index][1],
            )
    return parsed_values


def _normalize_weather_frame(frame: pd.DataFrame) -> list[dict]:
    frame, declared_units = _unit_row(frame)
    columns = {_normalize_column_name(column): column for column in frame.columns}
    datetime_column = _find_column(columns, DATETIME_ALIASES)
    date_column = _find_column(columns, DATE_ALIASES)
    time_column = _find_column(columns, TIME_ALIASES)
    temperature_column = _find_column(columns, TEMPERATURE_ALIASES)
    pressure_column = _find_column(columns, PRESSURE_ALIASES)
    wind_speed_column = _find_column_with_unit(columns, WIND_SPEED_ALIASES)
    wind_direction_column = _find_column(columns, WIND_DIRECTION_ALIASES)
    wind_speed_unit = _wind_unit(
        wind_speed_column,
        declared_units.get(str(wind_speed_column)),
    )

    if not temperature_column or not pressure_column:
        raise ValueError("Weather file must contain temperature and pressure columns.")
    if not datetime_column and not (date_column and time_column):
        raise ValueError("Weather file must contain datetime or separate date/time columns.")

    raw_datetimes = (
        frame[datetime_column].tolist()
        if datetime_column
        else [
            f"{date_value} {time_value}"
            for date_value, time_value in zip(
                frame[date_column],
                frame[time_column],
            )
        ]
    )
    parsed_datetimes = _parse_datetime_series(raw_datetimes)
    records = []
    for (row_index, row), (timestamp, warnings) in zip(
        frame.iterrows(),
        parsed_datetimes,
    ):
        temperature = _numeric(row.get(temperature_column))
        pressure = _numeric(row.get(pressure_column))
        if timestamp is None or temperature is None or pressure is None:
            continue

        # Kestrel exports Baro/Station P. in mb/hPa. Split stores pressure in kPa.
        pressure_kpa = pressure / 10.0 if pressure > 200.0 else pressure
        wind_speed, wind_warnings = _wind_value_ms(
            row.get(wind_speed_column) if wind_speed_column else None,
            wind_speed_unit,
            wind_speed_column,
        )
        raw_direction = row.get(wind_direction_column) if wind_direction_column else None
        wind_direction = _numeric(raw_direction)
        if wind_direction is None and raw_direction is not None and not pd.isna(raw_direction):
            wind_direction = str(raw_direction).strip() or None

        records.append(
            {
                "timestamp": timestamp,
                "temp_c": temperature,
                "baro_kpa": pressure_kpa,
                "wind_ms": wind_speed,
                "wind_direction": wind_direction,
                "wind_unit": WIND_UNIT_MS if wind_speed is not None else None,
                "wind_source_column": wind_speed_column,
                "timezone": timestamp.tzinfo.tzname(timestamp) if timestamp.tzinfo else None,
                "date_ambiguous": bool(warnings),
                "warnings": list(dict.fromkeys(warnings + wind_warnings)),
                "source_row": int(row_index) + 1,
            }
        )

    if not records:
        raise ValueError("No valid weather records were found.")
    records.sort(key=lambda record: record["timestamp"])
    return records


def read_weather_file(file_path) -> list[dict]:
    """Read CSV or XLSX weather data into neutral normalized records."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = _read_csv(path)
    elif suffix == ".xlsx":
        frame = _read_xlsx(path)
    else:
        raise ValueError("Unsupported weather format. Use CSV or XLSX.")
    records = _normalize_weather_frame(frame)
    source_file = path.name
    for record in records:
        record["source_file"] = source_file
    return records

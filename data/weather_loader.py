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
CROSSWIND_ALIASES = {"crosswind", "cross_wind"}
HEADWIND_ALIASES = {"headwind", "head_wind"}
WIND_DIRECTION_ALIASES = {
    "true_dir",
    "true_direction",
    "wind_direction",
    "direcao_vento",
    "mag_dir",
    "mag_direction",
}


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


def _normalize_weather_frame(frame: pd.DataFrame) -> list[dict]:
    columns = {_normalize_column_name(column): column for column in frame.columns}
    datetime_column = _find_column(columns, DATETIME_ALIASES)
    date_column = _find_column(columns, DATE_ALIASES)
    time_column = _find_column(columns, TIME_ALIASES)
    temperature_column = _find_column(columns, TEMPERATURE_ALIASES)
    pressure_column = _find_column(columns, PRESSURE_ALIASES)
    wind_speed_column = _find_column(columns, WIND_SPEED_ALIASES)
    crosswind_column = _find_column(columns, CROSSWIND_ALIASES)
    headwind_column = _find_column(columns, HEADWIND_ALIASES)
    wind_direction_column = _find_column(columns, WIND_DIRECTION_ALIASES)

    if not temperature_column or not pressure_column:
        raise ValueError("Weather file must contain temperature and pressure columns.")
    if not datetime_column and not (date_column and time_column):
        raise ValueError("Weather file must contain datetime or separate date/time columns.")

    records = []
    for row_index, row in frame.iterrows():
        raw_datetime = (
            row.get(datetime_column)
            if datetime_column
            else f"{row.get(date_column, '')} {row.get(time_column, '')}"
        )
        timestamp, warnings = _parse_datetime(raw_datetime)
        temperature = _numeric(row.get(temperature_column))
        pressure = _numeric(row.get(pressure_column))
        if timestamp is None or temperature is None or pressure is None:
            continue

        # Kestrel exports Baro/Station P. in mb/hPa. Split stores pressure in kPa.
        pressure_kpa = pressure / 10.0 if pressure > 200.0 else pressure
        wind_speed = _numeric(row.get(wind_speed_column)) if wind_speed_column else None
        crosswind = _numeric(row.get(crosswind_column)) if crosswind_column else None
        headwind = _numeric(row.get(headwind_column)) if headwind_column else None
        if (wind_speed is None or wind_speed == 0.0) and crosswind is not None and headwind is not None:
            component_speed = (crosswind**2 + headwind**2) ** 0.5
            if component_speed != 0.0 or wind_speed is None:
                wind_speed = component_speed

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
                "timezone": timestamp.tzinfo.tzname(timestamp) if timestamp.tzinfo else None,
                "date_ambiguous": bool(warnings),
                "warnings": warnings,
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
    return _normalize_weather_frame(frame)

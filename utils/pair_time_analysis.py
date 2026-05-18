# coding: utf-8
"""Helpers locais para tabelas de tempos dos pares selecionados."""

import math
from statistics import mean


def run_sort_key(run_id):
    """Retorna chave estavel para ordenar IDs de runs."""
    try:
        return (0, int(run_id))
    except (TypeError, ValueError):
        return (1, str(run_id))


def resolve_run_id(raw_run_id, all_run_data):
    """Resolve um ID de run vindo do estado dos pares para uma chave existente."""
    if raw_run_id in all_run_data:
        return raw_run_id

    try:
        run_as_int = int(raw_run_id)
        if run_as_int in all_run_data:
            return run_as_int
    except (TypeError, ValueError):
        pass

    run_as_str = str(raw_run_id)
    if run_as_str in all_run_data:
        return run_as_str

    return None


def resolve_pair_run_ids(pair_info, all_run_data):
    """Retorna os IDs ida/volta de um par, aceitando schemas antigos."""
    run_ida = pair_info.get("run1", pair_info.get("run_ida"))
    run_volta = pair_info.get("run2", pair_info.get("run_volta"))

    if (run_ida is None or run_volta is None) and pair_info.get("pair_id"):
        pair_id = str(pair_info.get("pair_id"))
        if "/" in pair_id and "+" not in pair_id:
            left, right = pair_id.split("/", 1)
            run_ida = run_ida if run_ida is not None else left
            run_volta = run_volta if run_volta is not None else right

    return (
        resolve_run_id(run_ida, all_run_data),
        resolve_run_id(run_volta, all_run_data),
    )


def normalize_interval_times(run_data):
    """
    Normaliza tempos de uma run para tempos por intervalo de velocidade.

    O CSV atual armazena tempos acumulados por ponto de velocidade. Tambem
    aceitamos o schema legado em que os tempos ja vinham por intervalo.
    """
    velocities = run_data.get("velocities") or []
    times = run_data.get("times") or []

    if len(velocities) < 2 or not times:
        return []

    try:
        velocities = [float(value) for value in velocities]
        times = [float(value) for value in times]
    except (TypeError, ValueError):
        return []

    if len(times) == len(velocities) - 1:
        interval_times = times
    elif len(times) == len(velocities) and abs(times[0]) < 1e-9:
        interval_times = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    else:
        return []

    interval_rows = []
    for idx, interval_time in enumerate(interval_times):
        if idx + 1 >= len(velocities):
            break
        if not math.isfinite(interval_time) or interval_time <= 0:
            continue

        v_start = velocities[idx]
        v_end = velocities[idx + 1]
        if not math.isfinite(v_start) or not math.isfinite(v_end) or v_start <= v_end:
            continue

        start_label = int(round(v_start))
        end_label = int(round(v_end))
        interval_rows.append(
            {
                "key": (start_label, end_label),
                "interval_start": start_label,
                "interval_end": end_label,
                "interval_label": f"{start_label}-{end_label}",
                "time_s": float(interval_time),
            }
        )

    return interval_rows


def calculate_delta_t_percent(time_ida, time_volta):
    """Calcula abs(T_ida - T_volta) / mean(T_ida, T_volta) * 100."""
    try:
        time_ida = float(time_ida)
        time_volta = float(time_volta)
    except (TypeError, ValueError):
        return None

    pair_mean = (time_ida + time_volta) / 2.0
    if pair_mean <= 0 or not math.isfinite(pair_mean):
        return None

    return abs(time_ida - time_volta) / pair_mean * 100.0


def build_selected_pairs_time_analysis(selected_pairs, all_run_data):
    """
    Monta dados de tempo e Delta T para os pares selecionados.

    Retorna dict com:
    - intervals: intervalos ordenados por velocidade decrescente
    - pairs: colunas de pares com tempos ida/volta e deltas por intervalo
    """
    pair_columns = []
    interval_by_key = {}

    for pair_index, pair_info in enumerate(selected_pairs, start=1):
        run_ida, run_volta = resolve_pair_run_ids(pair_info, all_run_data)
        ida_rows = normalize_interval_times(all_run_data.get(run_ida, {})) if run_ida is not None else []
        volta_rows = normalize_interval_times(all_run_data.get(run_volta, {})) if run_volta is not None else []

        ida_times = {row["key"]: row["time_s"] for row in ida_rows}
        volta_times = {row["key"]: row["time_s"] for row in volta_rows}

        for row in ida_rows + volta_rows:
            interval_by_key[row["key"]] = {
                "key": row["key"],
                "interval_start": row["interval_start"],
                "interval_end": row["interval_end"],
                "interval_label": row["interval_label"],
            }

        delta_values = {}
        for key in sorted(set(ida_times) & set(volta_times), reverse=True):
            delta = calculate_delta_t_percent(ida_times[key], volta_times[key])
            if delta is not None:
                delta_values[key] = delta

        pair_mean = mean(delta_values.values()) if delta_values else None
        pair_columns.append(
            {
                "pair_index": pair_index,
                "pair_label": f"Par {pair_index}",
                "pair_id": pair_info.get("pair_id", f"{run_ida}/{run_volta}"),
                "run_ida": run_ida,
                "run_volta": run_volta,
                "ida_times": ida_times,
                "volta_times": volta_times,
                "delta_values": delta_values,
                "mean_delta": pair_mean,
            }
        )

    intervals = sorted(
        interval_by_key.values(),
        key=lambda item: (item["interval_start"], item["interval_end"]),
        reverse=True,
    )

    return {
        "intervals": intervals,
        "pairs": pair_columns,
    }

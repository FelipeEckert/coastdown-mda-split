# coding: utf-8
"""Pure data preparation helpers for Split run visualizations."""

from __future__ import annotations

import math

from core.split_comparison import COMPLETE_PAIR_COMPONENTS, normalized_record_direction
from data.split_parser import (
    inspect_interval_coverage,
    normalize_run_intervals,
    required_subintervals,
)

SPLIT_GRAPH_PLUS_COLOR = "#3A9CFF"
SPLIT_GRAPH_MINUS_COLOR = "#F5B82E"
SPLIT_GRAPH_OTHER_COLORS = [
    "#8CC8FF",
    "#2DD36F",
    "#FF8A8A",
    "#B39DFF",
    "#4DD0E1",
    "#FFD166",
    "#F48FB1",
    "#A9B6C7",
]


def collect_split_run_options(parsed_runs: dict | None) -> list[dict]:
    """Return stable option records from the processed high/low Split runs."""
    parsed = parsed_runs if isinstance(parsed_runs, dict) else {}
    options = []
    for interval_name in ("high", "low"):
        for index, record in enumerate(parsed.get(interval_name) or []):
            options.append(
                {
                    "option_id": f"{interval_name}:{index}",
                    "interval_name": interval_name,
                    "record": record,
                }
            )
    return options


def filter_split_run_options(
    options: list[dict],
    interval_name: str = "both",
    direction: str = "both",
) -> list[dict]:
    """Filter Split run options by interval role and explicit direction."""
    filtered = []
    for option in options or []:
        if interval_name in ("high", "low") and option.get("interval_name") != interval_name:
            continue
        record_direction = normalized_record_direction(option.get("record") or {})
        if record_direction not in ("+", "-"):
            continue
        if direction in ("+", "-") and record_direction != direction:
            continue
        filtered.append(option)
    return filtered


def reconcile_split_run_selection(
    selected_ids: list[str] | tuple[str, ...] | None,
    available_ids: list[str] | tuple[str, ...] | None,
) -> list[str]:
    """Keep selected run IDs that remain available, preserving their order."""
    available = set(available_ids or [])
    return [
        option_id
        for option_id in dict.fromkeys(selected_ids or [])
        if option_id in available
    ]


def apply_split_run_selection_action(
    selected_ids: list[str] | tuple[str, ...] | None,
    available_ids: list[str] | tuple[str, ...] | None,
    action: str = "reconcile",
) -> list[str]:
    """Apply one section-local selection action to the available run IDs."""
    available = list(dict.fromkeys(available_ids or []))
    if action == "add_all":
        return available
    if action == "clear":
        return []
    if action == "reconcile":
        return reconcile_split_run_selection(selected_ids, available)
    raise ValueError(f"Unknown Split graph selection action: {action}")


def _source_run(record: dict, input_sources: list[dict]) -> dict | None:
    filename = record.get("filename")
    source_role = record.get("source_role")
    run_id = record.get("run_id")

    matching_sources = [
        source
        for source in (input_sources or [])
        if source.get("filename") == filename
        and source.get("role") == source_role
    ]
    if not matching_sources:
        matching_sources = [
            source
            for source in (input_sources or [])
            if source.get("filename") == filename
        ]

    for source in matching_sources:
        for candidate_id, run_data in (source.get("all_run_data") or {}).items():
            if candidate_id == run_id or str(candidate_id) == str(run_id):
                return run_data
    return None


def _finite_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def build_split_run_plot_series(
    record: dict | None,
    input_sources: list[dict] | None,
) -> dict | None:
    """Build measured interval-boundary points for one parsed Split run."""
    if not isinstance(record, dict):
        return None

    start_kmh = _finite_float(record.get("start_kmh"))
    end_kmh = _finite_float(record.get("end_kmh"))
    step_kmh = _finite_float(record.get("step_kmh"))
    delta_t_s = _finite_float(record.get("delta_t_s"))
    interval_name = record.get("interval_name")

    if (
        start_kmh is not None
        and end_kmh is not None
        and step_kmh is not None
        and step_kmh > 0
        and start_kmh > end_kmh
    ):
        expected_bins = required_subintervals(start_kmh, end_kmh, step_kmh)
        run_data = _source_run(record, input_sources or [])
        if run_data:
            rows = normalize_run_intervals(
                run_data,
                expected_bins,
                record.get("source_role"),
                interval_name,
            )
            coverage = inspect_interval_coverage(rows, expected_bins)
            if coverage["complete"]:
                elapsed_times = [0.0]
                speeds = [float(coverage["matched_rows"][0]["start_kmh"])]
                cumulative_time = 0.0
                for row in coverage["matched_rows"]:
                    cumulative_time += float(row["time_s"])
                    elapsed_times.append(cumulative_time)
                    speeds.append(float(row["end_kmh"]))
                return {
                    "record": record,
                    "interval_name": interval_name,
                    "direction": normalized_record_direction(record),
                    "times_s": elapsed_times,
                    "speeds_kmh": speeds,
                    "interval_rows": coverage["matched_rows"],
                    "data_mode": "interval_curve",
                }

    if (
        start_kmh is not None
        and end_kmh is not None
        and delta_t_s is not None
        and delta_t_s > 0
        and start_kmh > end_kmh
    ):
        return {
            "record": record,
            "interval_name": interval_name,
            "direction": normalized_record_direction(record),
            "times_s": [0.0, delta_t_s],
            "speeds_kmh": [start_kmh, end_kmh],
            "interval_rows": [],
            "data_mode": "aggregate",
        }
    return None


def apply_split_plotly_theme(
    fig,
    title: str,
    xaxis_title: str = "Tempo (s)",
    yaxis_title: str = "Velocidade (km/h)",
    height: int = 500,
):
    """Apply the shared dark-navy Plotly theme used by Split charts."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 15, "color": "#F4F8FC"},
        },
        xaxis={
            "title": xaxis_title,
            "color": "#D8E2EC",
            "gridcolor": "#22384F",
            "zerolinecolor": "#2A4058",
            "showgrid": True,
        },
        yaxis={
            "title": yaxis_title,
            "color": "#D8E2EC",
            "gridcolor": "#22384F",
            "zerolinecolor": "#2A4058",
            "showgrid": True,
        },
        plot_bgcolor="#0D1B2B",
        paper_bgcolor="#07111F",
        font={"color": "#F4F8FC"},
        legend={
            "bgcolor": "#112438",
            "bordercolor": "#2A4058",
            "borderwidth": 1,
            "font": {"size": 11},
        },
        hoverlabel={
            "bgcolor": "#112438",
            "bordercolor": "#3A9CFF",
            "font": {"color": "#F4F8FC"},
        },
        modebar={
            "bgcolor": "rgba(7,17,31,0.72)",
            "color": "#A9B6C7",
            "activecolor": "#3A9CFF",
        },
        hovermode="x unified",
        height=height,
        margin={"l": 60, "r": 20, "t": 50, "b": 50},
    )
    return fig


def split_graph_trace_name(record: dict | None, active: bool = False) -> str:
    """Return a compact chart legend label without file or timestamp noise."""
    source = record if isinstance(record, dict) else {}
    run_id = source.get("run_id")
    direction = normalized_record_direction(source) or "N/A"
    star = " ★" if active else ""
    return f"Run {run_id if run_id not in (None, '') else 'N/A'}{star} [{direction}]"


def format_graph_run_label(record: dict | None) -> str:
    """Return a compact Split graph selector/axis label with run and Delta t only."""
    source = record if isinstance(record, dict) else {}
    run_id = source.get("run_id")
    delta_t = _finite_float(source.get("delta_t_s"))
    run_label = f"Run {run_id if run_id not in (None, '') else 'N/A'}"
    delta_label = f"{delta_t:.2f} s" if delta_t is not None else "N/A"
    return f"{run_label} | dt={delta_label}"


def split_graph_hover_title(record: dict | None) -> str:
    """Return the first hover line for a Split speed curve."""
    source = record if isinstance(record, dict) else {}
    return split_graph_trace_name(source)


def split_active_component_runs(pair: dict | None, interval_name: str) -> dict[str, object]:
    """Return active + and - run IDs for the requested Split interval."""
    source = pair if isinstance(pair, dict) else {}
    if interval_name == "high":
        components = {"+": "high_plus", "-": "high_minus"}
    elif interval_name == "low":
        components = {"+": "low_plus", "-": "low_minus"}
    else:
        return {}

    active_runs = {}
    for direction, component in components.items():
        record = source.get(component)
        if isinstance(record, dict) and record.get("run_id") not in (None, ""):
            active_runs[direction] = record.get("run_id")
    return active_runs


def split_record_matches_active_component(record: dict | None, active_runs: dict) -> bool:
    """Return whether a parsed run belongs to the active pair component set."""
    source = record if isinstance(record, dict) else {}
    direction = normalized_record_direction(source)
    if direction not in active_runs:
        return False
    return str(source.get("run_id")) == str(active_runs.get(direction))


def split_pair_component_records(pair: dict | None) -> list[dict]:
    """Return the four Split component records stored in a comparison pair."""
    source = pair if isinstance(pair, dict) else {}
    components = []
    for component in COMPLETE_PAIR_COMPONENTS:
        record = source.get(component)
        if isinstance(record, dict) and record:
            components.append({"component": component, "record": record})
    return components

"""Split summary and measured-run report, using supplied canonical values only."""

from datetime import datetime
from html import escape
from io import BytesIO
import json
import math
from pathlib import Path

from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, LayoutError, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, TopPadder,
)

from reports.report_styles import (
    BACKGROUND_COLOR, BORDER_COLOR, FAIL_BACKGROUND_COLOR, HEADING_COLOR,
    PAGE_MARGIN, PAGE_SIZE, PASS_BACKGROUND_COLOR, TABLE_BACKGROUND_COLOR,
    build_report_styles,
)
from version import APP_NAME, APP_VERSION


LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "hyundai_logo.png"


def _text(value) -> str:
    """Format optional metadata without inventing missing values or markup."""
    if value is None:
        return "N/A"
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_text(item)}" for key, item in value.items()) or "N/A"
    if isinstance(value, (list, tuple)):
        return "; ".join(_text(item) for item in value) or "N/A"
    result = str(value).strip()
    return "N/A" if result.lower() in {"", "nan", "none", "inf", "-inf"} else result


def _number(value, precision=2) -> str:
    """Presentation rounding only; preserve signs and never fill a result."""
    if value is None or isinstance(value, bool):
        return "N/A"
    try:
        return f"{value:.{precision}f}" if math.isfinite(value) else "N/A"
    except (TypeError, ValueError):
        return "N/A"


def _mapping(value, name) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dictionary.")
    return value


def _measured_runs(pairs):
    """Project selected-pair records; deduplicate only identical identified snapshots."""
    rows = {"high": [], "low": []}
    seen = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("Each selected pair must be a dictionary.")
        ambient = _mapping(pair.get("ambient_by_component"), "ambient_by_component")
        components = _mapping(pair.get("weather_components"), "weather_components")
        synchronized = _mapping(pair.get("weather_sync"), "weather_sync")
        for interval in rows:
            for suffix, direction in (("plus", "+"), ("minus", "-")):
                component = f"{interval}_{suffix}"
                record = _mapping(pair.get(component), component)
                if not record:
                    continue
                weather = {}
                candidates = [components.get(component), record.get("weather_sync"),
                              synchronized.get(component)]
                if pair.get("ambient_mode") != "fixed":
                    candidates.append(ambient.get(component))
                for candidate in candidates:
                    snapshot = _mapping(candidate, f"{component} weather")
                    if (snapshot and snapshot.get("sync_method") != "fixed"
                            and snapshot.get("matched") is not False):
                        weather = snapshot
                        break
                labels = record.get("subintervals") or []
                if not isinstance(labels, (list, tuple)) or not all(isinstance(x, str) for x in labels):
                    raise ValueError(f"{component}.subintervals must be a list of labels.")
                stored = record.get("subinterval_times_s")
                if isinstance(stored, dict):
                    if not all(isinstance(x, str) for x in stored):
                        raise ValueError("Subinterval time mappings must use string labels.")
                    times = stored
                elif isinstance(stored, (list, tuple)):
                    if len(stored) > len(labels):
                        raise ValueError("Stored subinterval times contain unlabeled values.")
                    times = dict(zip(labels, stored))
                elif stored is None:
                    times = {}
                else:
                    raise ValueError("subinterval_times_s must be a list or dictionary.")
                if len(set(labels)) != len(labels):
                    raise ValueError("Duplicate subinterval labels cannot be rendered unambiguously.")
                if record.get("run_id") is not None and (
                    record.get("filename") or record.get("content_sha256")
                ):
                    signature = json.dumps([component, record, weather], sort_keys=True, default=str)
                    if signature in seen:
                        continue
                    seen.add(signature)
                rows[interval].append({
                    "record": record, "weather": weather, "direction": direction,
                    "labels": list(dict.fromkeys([*labels, *times])), "times": times,
                })
    return rows


def _run_label(record, direction):
    label = _text(record.get("run_id"))
    return label if label.endswith(direction) else f"{label} {direction}"


def _run_chart(series, interval, width, height, title, tr, pairs=None):
    """Vector polylines through supplied points, without fitting or rebuilding times."""
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, strokeColor=BORDER_COLOR, strokeWidth=.5,
                     fillColor=BACKGROUND_COLOR))
    drawing.add(Rect(0, height - 20, width, 20, strokeColor=BORDER_COLOR,
                     strokeWidth=.5, fillColor=TABLE_BACKGROUND_COLOR))
    drawing.add(String(7, height - 14, title, fontName="Helvetica-Bold",
                       fontSize=10, fillColor=HEADING_COLOR))
    entries = [item for item in series if item["interval_name"] == interval]
    if pairs is not None:
        def identity(record):
            return tuple(record.get(key) for key in (
                "run_id", "filename", "content_sha256", "source_role", "interval_name",
            ))
        selected = []
        for pair_index, pair in enumerate(pairs):
            for suffix, direction in (("plus", "+"), ("minus", "-")):
                record = pair.get(f"{interval}_{suffix}")
                if not record:
                    continue
                match = next((item for item in entries if item["direction"] == direction
                              and identity(item["record"]) == identity(record)), None)
                if match is not None:
                    selected.append({**match, "pair_index": pair_index})
        entries = selected
    if not entries:
        drawing.add(String(15, height / 2, tr("Curvas indisponíveis (N/A).",
                                           "Curves unavailable (N/A)."),
                           fontName="Helvetica", fontSize=9, fillColor=HEADING_COLOR))
        return drawing
    labels = [(tr("Par ", "Pair ") + str(item["pair_index"] + 1) + " | "
               if "pair_index" in item else "") + _run_label(item["record"], item["direction"]) + (
        tr(" (extremos)", " (endpoints)") if item.get("data_mode") == "aggregate" else ""
    ) for item in entries]
    legend_rows = max(1, int((height - 40) // 13))
    legend_column_width = max(stringWidth(label, "Helvetica", 8) for label in labels) + 38
    legend_width = legend_column_width * math.ceil(len(entries) / legend_rows)
    if legend_width > width * .3:
        raise ValueError("The fixed measured-data page cannot accommodate these chart labels at readable size.")
    chart = LinePlot()
    chart.x, chart.y = 52, 28
    chart.width, chart.height = width - 62 - legend_width, height - 61
    chart.data = [list(zip(item["times_s"], item["speeds_kmh"])) for item in entries]
    for axis in (chart.xValueAxis, chart.yValueAxis):
        axis.labels.fontName, axis.labels.fontSize = "Helvetica", 8
        axis.labels.fillColor = HEADING_COLOR
        axis.strokeColor = HEADING_COLOR
        axis.strokeWidth = .4
        axis.visibleGrid = True
        axis.gridStrokeColor = BORDER_COLOR
        axis.gridStrokeWidth = .4
        axis.maximumTicks = 9 if height >= 130 else 5
        axis.forceZero = False
        axis.rangeRound = "both"
    colors = [HEADING_COLOR, HexColor("#2287C9"), HexColor("#39794B"),
              HexColor("#BF681C"), HexColor("#8056A0")]
    for index, item in enumerate(entries):
        color = colors[item.get("pair_index", index // 2) % len(colors)]
        dash = [4, 2] if item["direction"] == "-" else None
        chart.lines[index].strokeColor = color
        chart.lines[index].strokeWidth = 1.3
        chart.lines[index].strokeDashArray = dash
        legend_y = height - 40 - (index % legend_rows) * 13
        legend_x = width - legend_width + 8 + (index // legend_rows) * legend_column_width
        drawing.add(Line(legend_x, legend_y, legend_x + 18, legend_y,
                         strokeColor=color, strokeWidth=1.3, strokeDashArray=dash))
        drawing.add(String(legend_x + 23, legend_y - 3, labels[index],
                           fontName="Helvetica", fontSize=8, fillColor=HEADING_COLOR))
    drawing.add(chart)
    drawing.add(String(chart.x + chart.width / 2, 8, tr("Tempo [s]", "Time [s]"),
                       textAnchor="middle", fontName="Helvetica", fontSize=9, fillColor=HEADING_COLOR))
    speed_label = String(0, 0, tr("Velocidade [km/h]", "Speed [km/h]"),
                         textAnchor="middle", fontName="Helvetica", fontSize=9, fillColor=HEADING_COLOR)
    rotated = Group(speed_label)
    rotated.rotate(90)
    rotated.translate(chart.y + chart.height / 2, -13)
    drawing.add(rotated)
    return drawing


def _run_tables(pairs, graph_series, width, paragraph, tr):
    """Selected-pair cards above tall charts; weather stays in the supplied snapshot."""
    if not isinstance(graph_series, list):
        raise ValueError("graph_series must be a list.")
    for item in graph_series:
        if not isinstance(item, dict) or item.get("interval_name") not in ("high", "low"):
            raise ValueError("Each graph series must identify a high or low interval.")
        if not isinstance(item.get("record"), dict) or item.get("direction") not in ("+", "-"):
            raise ValueError("Each graph series requires a record and +/- direction.")
        times, speeds = item.get("times_s"), item.get("speeds_kmh")
        if (not isinstance(times, (list, tuple)) or not isinstance(speeds, (list, tuple))
                or len(times) < 2 or len(times) != len(speeds)):
            raise ValueError("Graph times_s and speeds_kmh must be aligned lists of at least two points.")
        if any(_number(value) == "N/A" for value in (*times, *speeds)):
            raise ValueError("Graph points must be finite numbers.")
    story = [
        paragraph(tr("Dados medidos | Split", "Measured data | Split"), "Title"),
        paragraph(tr("Corridas dos pares selecionados. Δt em segundos; intervalos em km/h.",
                     "Runs from selected pairs. Δt in seconds; intervals in km/h."), "Body"),
    ]
    # Interval rows keep all four direction/run columns aligned across pair cards.
    card_styles = build_report_styles()
    for name in ("RunCell", "RunHeader", "TableHeader"):
        card_styles[name].alignment = 1
        card_styles[name].fontSize = 9.5 if name == "TableHeader" else 8.5
    def card_paragraph(value, style="RunCell"):
        return Paragraph(escape(_text(value)).replace("\n", "<br/>"), card_styles[style])

    components = (("high", "+"), ("low", "+"), ("high", "-"), ("low", "-"))
    snapshots = []
    labels = []
    for pair in pairs:
        measured = _measured_runs([pair])
        runs = [next((item for item in measured[interval] if item["direction"] == direction), {})
                for interval, direction in components]
        snapshots.append(runs)
        labels.extend(label for run in runs for label in run.get("labels", []))
    labels = list(dict.fromkeys(labels))
    label_width = max(stringWidth(label, "Helvetica-Bold", 8.5) for label in ["Δt total [s]", *labels]) + 4
    value_width = max([stringWidth("High+", "Helvetica-Bold", 8.5), *[
        stringWidth(_number(value, 2), "Helvetica", 8.5)
        for runs in snapshots for run in runs
        for value in [run.get("record", {}).get("delta_t_s"), *run.get("times", {}).values()]
    ]]) + 2
    columns = min(max(1, len(pairs)), max(1, int((width + 8) / (label_width + 4 * value_width + 8))))
    card_width = (width - 8 * (columns - 1)) / columns
    cards = []
    for index, runs in enumerate(snapshots):
        run_blocks = []
        for sign in ("+", "-"):
            lines = [tr("Direção ", "Direction ") + sign]
            lines.extend(interval.title() + direction + ": Run "
                         + _text(runs[i].get("record", {}).get("run_id"))
                         for i, (interval, direction) in enumerate(components) if direction == sign)
            run_blocks.append(card_paragraph("\n".join(lines)))
        run_block = Table([run_blocks], colWidths=[card_width / 2] * 2)
        run_block.setStyle(TableStyle([
            ("LINEAFTER", (0, 0), (0, -1), .4, BORDER_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        data = [[card_paragraph(tr("Par ", "Pair ") + str(index + 1), "TableHeader"), "", "", "", ""],
                [run_block, "", "", "", ""],
                [card_paragraph("km/h", "RunHeader"), *[
                    card_paragraph(interval.title() + direction, "RunHeader") for interval, direction in components]]]
        for label in labels:
            data.append([card_paragraph(label, "RunCell"), *[
                card_paragraph(_number(run.get("times", {}).get(label), 2) if label in run.get("labels", []) else "-", "RunCell")
                for run in runs
            ]])
        data.append([card_paragraph("Δt total [s]", "RunHeader"), *[
            card_paragraph(_number(run.get("record", {}).get("delta_t_s"), 2), "RunHeader") for run in runs
        ]])
        cards.append(Table(data, colWidths=[label_width, *[(card_width - label_width) / 4] * 4]))
    if cards:
        for card in cards:
            card.setStyle(TableStyle([
                ("SPAN", (0, 0), (-1, 0)), ("SPAN", (0, 1), (-1, 1)),
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_BACKGROUND_COLOR),
                ("BACKGROUND", (0, 2), (-1, 2), TABLE_BACKGROUND_COLOR),
                ("BACKGROUND", (0, -1), (-1, -1), TABLE_BACKGROUND_COLOR),
                ("GRID", (0, 2), (-1, -1), .65, HexColor("#9AADC3")),
                ("BOX", (0, 0), (-1, -1), .5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 1), (-1, 1), 0), ("RIGHTPADDING", (0, 1), (-1, 1), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
            ]))
            card.wrap(card_width, PAGE_SIZE[1])
        # Shared measured heights prevent wrapping from shifting adjacent baselines.
        heights = [max(card._rowHeights[i] for card in cards)
                   for i in range(len(cards[0]._cellvalues))]
        for card in cards:
            card._argH = heights[:]
            card._rowHeights = heights[:]
        for offset in range(0, len(cards), columns):
            row = []
            for card in cards[offset:offset + columns]:
                if row:
                    row.append("")
                row.append(card)
            table = Table([row], colWidths=[card_width if i % 2 == 0 else 8 for i in range(len(row))], hAlign="LEFT")
            table.setStyle(TableStyle([(name, (0, 0), (-1, -1), 0) for name in (
                "LEFTPADDING", "RIGHTPADDING", "TOPPADDING", "BOTTOMPADDING",
            )]))
            story.extend([table, Spacer(1, 8)])
    else:
        story.append(card_paragraph("N/A", "RunCell"))
    used_height = sum(item.wrap(width, PAGE_SIZE[1])[1] + item.getSpaceBefore()
                      + item.getSpaceAfter() for item in story)
    chart_height = (PAGE_SIZE[1] - 25 * mm - used_height - 8) / 2
    if chart_height < 140:
        raise ValueError("Page 2 cannot accommodate these measured rows and charts at readable size.")
    for interval in ("high", "low"):
        story.append(_run_chart(graph_series, interval, width, chart_height, interval.title(), tr, pairs))
        if interval == "high":
            story.append(Spacer(1, 8))
    return story


def _pair_tables(final_results, width, paragraph, tr):
    """Render stored corrected directional values and means, with shared cells."""
    pairs = final_results["selected_pairs"]
    story = [
        paragraph(tr("Pares e coeficientes | Split", "Pairs and coefficients | Split"), "Title"),
        paragraph(tr("Composição dos pares selecionados e resultados corrigidos por direção.",
                     "Selected-pair composition and corrected results by direction."), "Body"),
    ]
    if not pairs:
        story.append(paragraph(tr("Pares indisponíveis (N/A).", "Pairs unavailable (N/A).")))
    block_width = (width - 12) / 2
    blocks = []
    for pair in pairs:
        data = [[paragraph(tr("Par | ", "Pair | ") + _text(pair.get("id")), "TableHeader"), "", "", ""],
                [paragraph(label, "RunHeader") for label in (
                    "Run", tr("F0 corrigido [N]", "Corrected F0 [N]"),
                    tr("F2 corrigido [N/(km/h)²]", "Corrected F2 [N/(km/h)²]"),
                    tr("Energia [MJ/km]", "Energy [MJ/km]"),
                )]]
        for suffix, direction in (("plus", "+"), ("minus", "-")):
            for interval in ("high", "low"):
                record = _mapping(pair.get(f"{interval}_{suffix}"), f"{interval}_{suffix}")
                values = [f"{interval.title()}{direction} | {_text(record.get('run_id'))}"]
                values += ([_number(pair.get(f"F0_{suffix}"), 4),
                            _number(pair.get(f"F2_{suffix}"), 6),
                            _number(pair.get(f"energy_{suffix}"), 4)]
                           if interval == "high" else ["", "", ""])
                data.append([paragraph(value, "RunCell") if value != "" else "" for value in values])
        data.append([paragraph(value, "RunHeader") for value in (
            tr("Média", "Mean"), _number(pair.get("F0_mean"), 4),
            _number(pair.get("F2_mean"), 6), _number(pair.get("energy"), 4),
        )])
        block = Table(data, colWidths=[block_width * fraction for fraction in (.34, .22, .23, .21)])
        block.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            *[("SPAN", (column, row), (column, row + 1)) for column in (1, 2, 3) for row in (2, 4)],
            ("BACKGROUND", (0, 0), (-1, 1), TABLE_BACKGROUND_COLOR),
            ("BACKGROUND", (0, -1), (-1, -1), TABLE_BACKGROUND_COLOR),
            ("GRID", (0, 0), (-1, -1), .4, BORDER_COLOR),
            ("LINEABOVE", (0, -1), (-1, -1), .7, HEADING_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        blocks.append(block)
    pair_rows = [[item] for item in story]
    for index in range(0, len(blocks), 2):
        row = Table([[blocks[index], "", blocks[index + 1] if index + 1 < len(blocks) else ""]],
                    colWidths=[block_width, 12, block_width])
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        pair_rows.append([[row, Spacer(1, 6)]])
    pair_table = Table(pair_rows, colWidths=[width], repeatRows=2)
    pair_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    rows = [[paragraph(tr("Resultados finais", "Final results"), "Heading"), "", "", ""],
            [paragraph(label, "RunHeader") for label in (
                tr("Par", "Pair"), tr("F0 corrigido [N]", "Corrected F0 [N]"),
                tr("F2 corrigido [N/(km/h)²]", "Corrected F2 [N/(km/h)²]"),
                tr("Energia [MJ/km]", "Energy [MJ/km]"),
            )]]
    rows.extend([[paragraph(value, "RunCell") for value in (
        pair.get("id"), _number(pair.get("F0_mean"), 4),
        _number(pair.get("F2_mean"), 6), _number(pair.get("energy"), 4),
    )] for pair in pairs])
    rows.append([paragraph(value, "TableHeader") for value in (
        tr("Consolidado", "Consolidated"),
        tr("F0 final", "Final F0") + "\n" + _number(final_results.get("mean_f0"), 4),
        tr("F2 final", "Final F2") + "\n" + _number(final_results.get("mean_f2"), 6),
        tr("Energia final", "Final energy") + "\n" + _number(final_results.get("mean_energy"), 4),
    )])
    results = Table(rows, colWidths=[width * fraction for fraction in (.34, .22, .23, .21)], repeatRows=2)
    results.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), TABLE_BACKGROUND_COLOR),
        ("BACKGROUND", (0, -1), (-1, -1), TABLE_BACKGROUND_COLOR),
        ("GRID", (0, 0), (-1, -1), .4, BORDER_COLOR),
        ("LINEABOVE", (0, -1), (-1, -1), 1, HEADING_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("NOSPLIT", (0, -2), (-1, -1)),
    ]))
    # Move a complete summary to the next page when it fits there. Larger summaries
    # split between rows, with repeated headings and the final row kept with its pair.
    return [pair_table, CondPageBreak(min(results.wrap(width, PAGE_SIZE[1])[1],
                                        PAGE_SIZE[1] - 25 * mm)), TopPadder(results)]


def export_split_final_results_to_pdf(
    *,
    final_results: dict,
    vehicle_data: dict,
    deviation_analysis: dict,
    graph_series: list[dict],
    test_name: str,
    generated_at: datetime,
    test_metadata: dict | None = None,
    language: str = "pt",
) -> bytes:
    """Return the A4 landscape summary, runs and corrected-pair pages as PDF bytes.

    Inputs are a consistent caller-prepared snapshot, never mutated. Final
    results supply num_pairs, means and diagnostic CVs; time_summary supplies
    normative values, limits and pass flags. No scientific value is calculated.
    Optional test identification stays in test_metadata, apart from normalized
    vehicle masses. Missing optional values print as N/A. Software metadata
    may override version.py identity via software_name and software_version.
    graph_series supplies the exact High/Low points rendered on Page 2.

    Pages 1-2 remain fixed; pair tables and optional report details continue as needed.
    Raises ValueError for malformed inputs or unsupported fixed-page content.
    """
    for name, value in (
        ("final_results", final_results), ("vehicle_data", vehicle_data),
        ("deviation_analysis", deviation_analysis),
    ):
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be a dictionary.")
    if not isinstance(final_results.get("selected_pairs"), list):
        raise ValueError("final_results.selected_pairs must be a list.")
    if not isinstance(deviation_analysis.get("time_summary"), dict):
        raise ValueError("deviation_analysis.time_summary must be a dictionary.")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime.")
    if language not in ("pt", "en"):
        raise ValueError("language must be 'pt' or 'en'.")
    def metadata_text(value):
        if isinstance(value, dict):
            return {key: metadata_text(item) for key, item in value.items()} if value else missing
        if value is None or (isinstance(value, str) and not value.strip()):
            return missing
        return value

    missing = "Não informado" if language == "pt" else "Not provided"
    metadata = {key: metadata_text(value) for key, value in _mapping(test_metadata, "test_metadata").items()}
    for key in ("test_date", "responsible_engineer", "operator", "driver", "location",
                "service_identifier", "report_identifier", "start_time", "end_time",
                "method", "configuration", "equipment"):
        metadata.setdefault(key, missing)
    times = deviation_analysis["time_summary"]
    groups = _mapping(times.get("groups"), "time_summary.groups")
    opposite = _mapping(times.get("opposite_direction"), "time_summary.opposite_direction")
    styles = build_report_styles()
    width = PAGE_SIZE[0] - 2 * PAGE_MARGIN
    gap = 8
    column_width = (width - gap) / 2

    def tr(pt, en):
        return pt if language == "pt" else en

    def paragraph(value, style="Table"):
        return Paragraph(escape(_text(value)).replace("\n", "<br/>"), styles[style])

    details = {}

    def summary_text(value, label, available_width, height, style="Table"):
        """Keep fixed-page text readable and preserve long values in a continuation."""
        if paragraph(value, style).wrap(available_width, PAGE_SIZE[1])[1] <= height:
            return value
        details[label] = value
        return tr("Ver detalhes do relatório", "See report details")

    def status(value):
        if value is True:
            return tr("Conforme", "Conforming")
        if value is False:
            return tr("Não conforme", "Nonconforming")
        return tr("Não avaliável (N/A)", "Not evaluable (N/A)")

    def table(rows, widths):
        result = Table(rows, colWidths=widths, hAlign="LEFT")
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ]
        result.setStyle(TableStyle(commands))
        return result

    def fields(rows):
        return table([
            [paragraph(label, "TableHeader"), paragraph(summary_text(
                value, label, (column_width - 12) * .61 - 14, 12,
            ))]
            for label, value in rows
        ], [(column_width - 12) * 0.39, (column_width - 12) * 0.61])

    def columns(cells, total_width=width):
        cell_width = (total_width - gap * (len(cells) - 1)) / len(cells)
        row, widths = [], []
        for cell in cells:
            if row:
                row.append("")
                widths.append(gap)
            row.append(cell)
            widths.append(cell_width)
        result = Table([row], colWidths=widths, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return result

    def box(content, box_width, title=None, fill=BACKGROUND_COLOR, min_height=None):
        rows = [[paragraph(title, "Heading")], [content]] if title is not None else [[content]]
        result = Table(rows, colWidths=[box_width], hAlign="LEFT", cornerRadii=[4] * 4,
                       minRowHeights=[min_height] if min_height is not None else None)
        result.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER_COLOR),
            ("BACKGROUND", (0, 0), (-1, -1), fill),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        if title is not None:
            result.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_BACKGROUND_COLOR),
            ]))
        return result

    def paired_metadata(first, second):
        return f"{_text(metadata.get(first))} / {_text(metadata.get(second))}"

    test_rows = [
        (tr("Data do teste", "Test date"), metadata.get("test_date")),
        (tr("Engenheiro / operador", "Engineer / operator"),
         paired_metadata("responsible_engineer", "operator")),
        (tr("Condutor", "Driver"), metadata.get("driver")),
        (tr("Local", "Location"), metadata.get("location")),
        (tr("Serviço / relatório", "Service / report"),
         paired_metadata("service_identifier", "report_identifier")),
        (tr("Início / fim", "Start / end"), paired_metadata("start_time", "end_time")),
    ]
    vehicle_rows = [
        (tr("Modelo", "Model"), vehicle_data.get("model")),
        (tr("Identificação / VIN", "Identification / VIN"), vehicle_data.get("vin")),
        (tr("Massa em ordem de marcha", "Running-order mass"),
         _number(vehicle_data.get("running_order_mass_kg"))),
        (tr("Massa de ensaio M", "Test mass M"), _number(vehicle_data.get("test_mass_kg"))),
        (tr("Massa rotacional me", "Rotational mass me"),
         _number(vehicle_data.get("rotational_equivalent_mass_kg"))),
        (tr("Massa efetiva Me", "Effective mass Me"),
         _number(vehicle_data.get("effective_mass_kg"))),
    ]
    metric_labels = [tr("Pares selecionados", "Selected pairs"), "F0 [N]",
                     "F2 [N/(km/h)²]", tr("Energia [MJ/km]", "Energy [MJ/km]")]
    metric_values = [final_results.get("num_pairs"),
                     _number(final_results.get("mean_f0"), 4),
                     _number(final_results.get("mean_f2"), 6),
                     _number(final_results.get("mean_energy"), 4)]
    metrics = columns([
        box([paragraph(label, "TableHeader"), Spacer(1, 4), paragraph(value, "Metric")],
            (width - 3 * gap) / 4, fill=TABLE_BACKGROUND_COLOR)
        for label, value in zip(metric_labels, metric_values)
    ])

    checks = []
    for key, label in (("high_plus", "CV High +"), ("high_minus", "CV High -"),
                       ("low_plus", "CV Low +"), ("low_minus", "CV Low -")):
        group = _mapping(groups.get(key), f"time_summary.groups.{key}")
        checks.append((label, group.get("cv_pct"), times.get("cv_limit_pct"), group.get("passed")))
    for key, label in (
        ("high", tr("Dif. médias High +/-", "Mean diff. High +/-")),
        ("low", tr("Dif. médias Low +/-", "Mean diff. Low +/-")),
    ):
        group = _mapping(opposite.get(key), f"time_summary.opposite_direction.{key}")
        checks.append((label, group.get("diff_pct"), times.get("opposite_mean_limit_pct"), group.get("passed")))
    check_width = (width - 12 - 5 * gap) / 6
    check_cards = []
    for label, value, limit, passed in checks:
        badge_style, badge_fill = "Badge", TABLE_BACKGROUND_COLOR
        if passed is True:
            badge_style, badge_fill = "PassBadge", PASS_BACKGROUND_COLOR
        elif passed is False:
            badge_style, badge_fill = "FailBadge", FAIL_BACKGROUND_COLOR
        badge = box(paragraph(status(passed), badge_style), check_width - 12, fill=badge_fill)
        badge.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BOX", (0, 0), (-1, -1), 0, badge_fill),
        ]))
        check_cards.append(box([
            paragraph(label), paragraph(f"{_number(value)} %", "CheckValue"),
            paragraph(f"{tr('Limite', 'Limit')}: {_number(limit)} %"), Spacer(1, 3), badge,
        ], check_width))
    normative = box(columns(check_cards, width - 12), width,
                    tr("Validação normativa dos tempos", "Normative time validation")
                    + "  |  " + status(times.get("passed")))
    diagnostic_title = (
        tr("Diagnóstico dos coeficientes", "Coefficient diagnostics")
        + f"  |  CV F0: {_number(final_results.get('cv_f0'))} %"
        + f"  |  CV F2: {_number(final_results.get('cv_f2'))} %"
    )
    diagnostics = [
        paragraph(tr(
            "CV de F0/F2 é diagnóstico e não determina a conformidade normativa dos tempos.",
            "F0/F2 CV is diagnostic and does not determine normative time conformity.",
        )),
    ]
    for source in (final_results, times):
        warnings = source.get("warnings")
        if warnings:
            diagnostics.extend([
                paragraph(tr("Avisos fornecidos: ", "Supplied warnings: ") + _text(summary_text(
                    warnings, tr("Avisos", "Warnings") + f" {len(details) + 1}", width - 12, 24,
                ))),
            ])

    story = [
        paragraph(tr("Resumo de resultados | Split", "Results summary | Split"), "Title"),
        paragraph(summary_text(_text(test_name) + (
            " | " + tr("Comentários: ", "Comments: ") + _text(metadata["comments"])
            if "comments" in (test_metadata or {}) else ""
        ), tr("Teste / comentários", "Test / comments"), width, 14, "Body"), "Body"), metrics, Spacer(1, 6),
        columns([
            box(fields(test_rows), column_width, tr("Identificação do teste", "Test identification")),
            box(fields(vehicle_rows), column_width, tr("Veículo e massas [kg]", "Vehicle and masses [kg]")),
        ]),
        Spacer(1, 6),
        box(columns([
            box([paragraph(label, "TableHeader"), Spacer(1, 4),
                 paragraph(summary_text(_text(value).replace("; ", "\n"), label,
                                        (width - 12 - 2 * gap) / 3 - 12, 36))],
                (width - 12 - 2 * gap) / 3, min_height=62)
            for label, value in (
                (tr("Método", "Method"), metadata.get("method")),
                (tr("Configuração", "Configuration"), metadata.get("configuration")),
                (tr("Equipamentos", "Equipment"), metadata.get("equipment")),
            )
        ], width - 12), width, tr("Método Split e configuração", "Split method and configuration")),
        Spacer(1, 6), normative, Spacer(1, 6), box(diagnostics, width, diagnostic_title),
    ]
    # Preserve approved spacing when it fits; compact gaps for real supplied warnings.
    overflow = sum(item.wrap(width, PAGE_SIZE[1])[1] + item.getSpaceBefore()
                   + item.getSpaceAfter() for item in story) - (PAGE_SIZE[1] - 25 * mm)
    if overflow > 0:
        spacers = [item for item in story if isinstance(item, Spacer)]
        for item in spacers:
            item.height -= min(4, overflow / len(spacers) + .1)
    software = f"{_text(metadata.get('software_name', APP_NAME))} / {_text(metadata.get('software_version', APP_VERSION))}"
    footer_left = summary_text(software + "\n" + paired_metadata("service_identifier", "report_identifier"),
                               tr("Identificação do relatório", "Report identification"), width * .55, 18, "Footer")
    story.extend([NextPageTemplate("runs"), PageBreak(),
                  *_run_tables(final_results["selected_pairs"], graph_series, width, paragraph, tr)])
    story.extend([NextPageTemplate("pairs"), PageBreak(),
                  *_pair_tables(final_results, width, paragraph, tr)])
    if details:
        story.extend([PageBreak(), paragraph(tr("Detalhes do relatório", "Report details"), "Title")])
        for label, value in details.items():
            story.extend([paragraph(label, "Heading"), paragraph(value, "Body"), Spacer(1, 6)])

    total_pages = 0

    def decorate(canvas, doc):
        if doc.pageTemplate.id == "summary" and doc.page != 1:
            raise ValueError("Page 1 content exceeds one page; shorten metadata or warnings.")
        if doc.pageTemplate.id == "runs" and doc.page != 2:
            raise ValueError("Page 2 content exceeds one page.")
        canvas.saveState()
        canvas.setFillColor(BACKGROUND_COLOR)
        canvas.rect(0, 0, *PAGE_SIZE, fill=1, stroke=0)
        canvas.setFillColor(HEADING_COLOR)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(PAGE_MARGIN, PAGE_SIZE[1] - 5.7 * mm, APP_NAME.upper())
        canvas.drawRightString(width + PAGE_MARGIN, PAGE_SIZE[1] - 5.7 * mm,
                               tr("RELATÓRIO TÉCNICO", "TECHNICAL REPORT"))
        if LOGO_PATH.is_file():
            # The existing white artwork needs a dark backing; never recolor it.
            logo_x, logo_y = PAGE_SIZE[0] / 2 - 36, PAGE_SIZE[1] - 7.5 * mm
            canvas.roundRect(logo_x - 4, logo_y - 2, 80, 16, 3, fill=1, stroke=0)
            canvas.drawImage(str(LOGO_PATH), logo_x, logo_y, width=72, height=12,
                             preserveAspectRatio=True, mask="auto")
        canvas.setStrokeColor(HEADING_COLOR)
        canvas.setLineWidth(1)
        canvas.line(PAGE_MARGIN, PAGE_SIZE[1] - 9 * mm,
                    width + PAGE_MARGIN, PAGE_SIZE[1] - 9 * mm)
        footer = Table([[
            paragraph(footer_left, "Footer"),
            paragraph(tr("Gerado: ", "Generated: ") + generated_at.isoformat(sep=" ", timespec="seconds")
                      + "  |  " + tr("Página ", "Page ") + str(doc.page)
                      + tr(" de ", " of ") + str(total_pages), "FooterRight"),
        ]], colWidths=[width * .55, width * .45])
        footer.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, HEADING_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        _, footer_height = footer.wrap(width, 10 * mm)
        if footer_height > 10 * mm:
            raise ValueError("Report footer is too long; shorten software metadata.")
        footer.drawOn(canvas, PAGE_MARGIN, 3 * mm)
        canvas.restoreState()

    # A layout pass gives the real total without replaying canvas internals/images.
    for _ in range(2):
        output = BytesIO()
        doc = BaseDocTemplate(
            output, pagesize=PAGE_SIZE, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
            topMargin=12 * mm, bottomMargin=13 * mm,
            title=_text(test_name), author=APP_NAME, creator=software,
        )
        doc.addPageTemplates([PageTemplate(
            id=section, onPage=decorate,
            frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        ) for section in ("summary", "runs", "pairs")])
        try:
            doc.build(story[:])
        except LayoutError as exc:
            raise ValueError("An indivisible report item cannot fit a page at the approved typography.") from exc
        total_pages = doc.page
    return output.getvalue()

"""Page 1 of the Split PDF report, using supplied canonical values only."""

from datetime import datetime
from html import escape
from io import BytesIO
import math

from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, LayoutError, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from reports.report_styles import (
    BACKGROUND_COLOR, BORDER_COLOR, HEADING_COLOR, PAGE_MARGIN, PAGE_SIZE,
    TABLE_BACKGROUND_COLOR, build_report_styles,
)
from version import APP_NAME, APP_VERSION


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
    """Return one A4 landscape summary page as PDF bytes.

    Inputs are a consistent caller-prepared snapshot, never mutated. Final
    results supply num_pairs, means and diagnostic CVs; time_summary supplies
    normative values, limits and pass flags. No scientific value is calculated.
    Optional test identification stays in test_metadata, apart from normalized
    vehicle masses. Missing optional values print as N/A. Software metadata
    may override version.py identity via software_name and software_version.
    graph_series is reserved for later pages and is not rendered here.

    Raises ValueError for malformed required sections, unsupported language or
    content exceeding this single page. No clipped or partial PDF is returned.
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
    metadata = _mapping(test_metadata, "test_metadata")
    times = deviation_analysis["time_summary"]
    groups = _mapping(times.get("groups"), "time_summary.groups")
    opposite = _mapping(times.get("opposite_direction"), "time_summary.opposite_direction")
    styles = build_report_styles()
    width = PAGE_SIZE[0] - 2 * PAGE_MARGIN
    column_width = (width - 14) / 2

    def tr(pt, en):
        return pt if language == "pt" else en

    def paragraph(value, style="Table"):
        return Paragraph(escape(_text(value)).replace("\n", "<br/>"), styles[style])

    def status(value):
        if value is True:
            return tr("Conforme", "Conforming")
        if value is False:
            return tr("Não conforme", "Nonconforming")
        return tr("Não avaliável (N/A)", "Not evaluable (N/A)")

    def table(rows, widths, header=False):
        result = Table(rows, colWidths=widths, hAlign="LEFT")
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ]
        if header:
            commands.append(("BACKGROUND", (0, 0), (-1, 0), TABLE_BACKGROUND_COLOR))
        result.setStyle(TableStyle(commands))
        return result

    def fields(rows):
        return table([
            [paragraph(label, "TableHeader"), paragraph(value)]
            for label, value in rows
        ], [column_width * 0.39, column_width * 0.61])

    def columns(left, right):
        result = Table([[left, "", right]], colWidths=[column_width, 14, column_width])
        result.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
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
    metrics = table([
        [paragraph(label, "TableHeader") for label in metric_labels],
        [paragraph(value, "Metric") for value in metric_values],
    ], [width / 4] * 4, header=True)

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
    normative = table([
        [paragraph(check[0], "TableHeader") for check in checks],
        [paragraph(f"{_number(value)} %\n{tr('Limite', 'Limit')}: {_number(limit)} %")
         for _, value, limit, _ in checks],
        [paragraph(status(passed)) for _, _, _, passed in checks],
    ], [width / 6] * 6, True)
    diagnostics = [
        paragraph(
            tr("Diagnóstico dos coeficientes", "Coefficient diagnostics")
            + f"  |  CV F0: {_number(final_results.get('cv_f0'))} %"
            + f"  |  CV F2: {_number(final_results.get('cv_f2'))} %", "Status",
        ),
        paragraph(tr(
            "CV de F0/F2 é diagnóstico e não determina a conformidade normativa dos tempos.",
            "F0/F2 CV is diagnostic and does not determine normative time conformity.",
        )),
    ]
    for source in (final_results, times):
        warnings = source.get("warnings")
        if warnings:
            diagnostics.extend([
                paragraph(tr("Avisos fornecidos: ", "Supplied warnings: ") + _text(warnings)),
            ])

    story = [
        paragraph(tr("Resumo de resultados | Split", "Results summary | Split"), "Title"),
        paragraph(test_name, "Body"), metrics, Spacer(1, 10),
        columns(
            [paragraph(tr("Identificação do teste", "Test identification"), "Heading"), fields(test_rows)],
            [paragraph(tr("Veículo e massas [kg]", "Vehicle and masses [kg]"), "Heading"), fields(vehicle_rows)],
        ),
        Spacer(1, 8),
        paragraph(tr("Método Split e configuração", "Split method and configuration"), "Heading"),
        table([[paragraph(label, "TableHeader"), paragraph(value)] for label, value in (
            (tr("Método / configuração", "Method / configuration"),
             paired_metadata("method", "configuration")),
            (tr("Equipamentos", "Equipment"), metadata.get("equipment")),
        )], [width * .20, width * .80]),
        Spacer(1, 8),
        paragraph(
            tr("Validação normativa dos tempos", "Normative time validation")
            + "  |  " + status(times.get("passed")), "Heading",
        ),
        normative, Spacer(1, 8), *diagnostics,
    ]
    software = f"{_text(metadata.get('software_name', APP_NAME))} / {_text(metadata.get('software_version', APP_VERSION))}"
    footer = table([[paragraph(value, "Footer") for value in (
        tr("Página 1", "Page 1"),
        tr("Gerado: ", "Generated: ") + generated_at.isoformat(sep=" ", timespec="seconds"),
        software,
    )]], [width * .12, width * .40, width * .48])

    def decorate(canvas, doc):
        if doc.page != 1:
            raise ValueError("Page 1 content exceeds one page; shorten metadata or warnings.")
        canvas.saveState()
        canvas.setFillColor(BACKGROUND_COLOR)
        canvas.rect(0, 0, *PAGE_SIZE, fill=1, stroke=0)
        canvas.setFillColor(HEADING_COLOR)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(PAGE_MARGIN, PAGE_SIZE[1] - 12 * mm, APP_NAME.upper())
        canvas.drawRightString(width + PAGE_MARGIN, PAGE_SIZE[1] - 12 * mm,
                               tr("RELATÓRIO TÉCNICO", "TECHNICAL REPORT"))
        canvas.setStrokeColor(HEADING_COLOR)
        canvas.setLineWidth(1)
        canvas.line(PAGE_MARGIN, PAGE_SIZE[1] - 15 * mm,
                    width + PAGE_MARGIN, PAGE_SIZE[1] - 15 * mm)
        _, footer_height = footer.wrap(width, 12 * mm)
        if footer_height > 12 * mm:
            raise ValueError("Page 1 footer is too long; shorten software metadata.")
        footer.drawOn(canvas, PAGE_MARGIN, 6 * mm)
        canvas.restoreState()

    output = BytesIO()
    doc = BaseDocTemplate(
        output, pagesize=PAGE_SIZE, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=19 * mm, bottomMargin=20 * mm,
        title=_text(test_name), author=APP_NAME, creator=software,
    )
    doc.addPageTemplates(PageTemplate(
        id="summary", onPage=decorate,
        frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ))
    try:
        doc.build(story)
    except LayoutError as exc:
        raise ValueError("Page 1 content exceeds one page; shorten metadata or warnings.") from exc
    return output.getvalue()

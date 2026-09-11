"""Print styles for the planned A4 landscape Split report."""

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm


PAGE_SIZE = landscape(A4)
PAGE_MARGIN = 8 * mm
BACKGROUND_COLOR = HexColor("#FFFFFF")
HEADING_COLOR = HexColor("#0B184B")
TEXT_COLOR = HexColor("#405579")
TABLE_BACKGROUND_COLOR = HexColor("#EDF3F7")
BORDER_COLOR = HexColor("#CDDEEE")
PASS_BACKGROUND_COLOR = HexColor("#E4F5E5")
PASS_TEXT_COLOR = HexColor("#18703A")
FAIL_BACKGROUND_COLOR = HexColor("#FCE8E8")
FAIL_TEXT_COLOR = HexColor("#9C2727")


def build_report_styles() -> StyleSheet1:
    """Return fresh paragraph styles so one report cannot restyle another."""
    styles = StyleSheet1()
    styles.add(ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=10, leading=14,
        textColor=TEXT_COLOR, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Title", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=24, leading=28, textColor=HEADING_COLOR, spaceAfter=4,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "Heading", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=HEADING_COLOR, spaceAfter=0,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "Table", parent=styles["Body"], fontSize=9, leading=12, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "TableHeader", parent=styles["Table"], fontName="Helvetica-Bold",
        textColor=HEADING_COLOR,
    ))
    styles.add(ParagraphStyle(
        "Metric", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=HEADING_COLOR, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "Status", parent=styles["Body"], fontName="Helvetica-Bold",
        textColor=HEADING_COLOR,
    ))
    styles.add(ParagraphStyle(
        "CheckValue", parent=styles["Metric"], fontSize=14, leading=18,
    ))
    styles.add(ParagraphStyle(
        "Badge", parent=styles["TableHeader"], alignment=1,
    ))
    styles.add(ParagraphStyle(
        "PassBadge", parent=styles["Badge"], textColor=PASS_TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        "FailBadge", parent=styles["Badge"], textColor=FAIL_TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        "Footer", parent=styles["Table"], fontSize=7, leading=9,
    ))
    styles.add(ParagraphStyle(
        "FooterRight", parent=styles["Footer"], alignment=2,
    ))
    styles.add(ParagraphStyle(
        "RunCell", parent=styles["Table"], fontSize=8, leading=10,
    ))
    styles.add(ParagraphStyle(
        "RunHeader", parent=styles["RunCell"], fontName="Helvetica-Bold",
        textColor=HEADING_COLOR,
    ))
    return styles

"""Print styles for the planned A4 landscape Split report."""

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm


PAGE_SIZE = landscape(A4)
PAGE_MARGIN = 15 * mm
BACKGROUND_COLOR = HexColor("#FFFFFF")
HEADING_COLOR = HexColor("#16324F")
TEXT_COLOR = HexColor("#202B36")
TABLE_BACKGROUND_COLOR = HexColor("#F1F4F7")
BORDER_COLOR = HexColor("#CBD5DF")


def build_report_styles() -> StyleSheet1:
    """Return fresh paragraph styles so one report cannot restyle another."""
    styles = StyleSheet1()
    styles.add(ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=10, leading=14,
        textColor=TEXT_COLOR, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Title", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=HEADING_COLOR, spaceAfter=6,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "Heading", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=13, leading=17, textColor=HEADING_COLOR, spaceAfter=8,
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
        fontSize=18, leading=22, textColor=HEADING_COLOR, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "Status", parent=styles["Body"], fontName="Helvetica-Bold",
        textColor=HEADING_COLOR,
    ))
    styles.add(ParagraphStyle(
        "Footer", parent=styles["Table"], fontSize=8, leading=10,
    ))
    return styles

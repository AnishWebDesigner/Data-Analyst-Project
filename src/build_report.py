"""Builds the two PDFs with ReportLab: the visual report and the code snapshot.

The roll number is printed in the footer of every page of both files. The student
name, roll number and GitHub link are on the cover of both.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

import config
from src.metrics import compute_kpis
from src.visualizations import CHAPTERS, CHARTS

# matplotlib ships DejaVu fonts, so the rupee sign prints on any computer
_FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for name, file in [("Body", "DejaVuSans.ttf"), ("BodyBold", "DejaVuSans-Bold.ttf"), ("Mono", "DejaVuSansMono.ttf"), ("BodyItalic", "DejaVuSans-Oblique.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(_FONTS / file)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="BodyItalic", boldItalic="BodyBold")

NAVY, TEAL, CORAL, SLATE = (colors.HexColor(c) for c in (config.NAVY, config.TEAL, config.CORAL, config.SLATE))
PALE = colors.HexColor("#F3F6F9")
LINE = colors.HexColor("#DDE3EA")

H1 = ParagraphStyle("h1", fontName="BodyBold", fontSize=17, textColor=NAVY, spaceBefore=4, spaceAfter=8, leading=21)
H2 = ParagraphStyle("h2", fontName="BodyBold", fontSize=11.5, textColor=TEAL, spaceBefore=8, spaceAfter=5)
BODY = ParagraphStyle("body", fontName="Body", fontSize=9.6, leading=14.2, textColor=colors.HexColor("#222B36"), spaceAfter=6)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.3, leading=11, textColor=SLATE)
FIGLABEL = ParagraphStyle("fig", fontName="BodyBold", fontSize=8.5, textColor=SLATE, spaceBefore=8, spaceAfter=3)
CAPTION = ParagraphStyle("cap", parent=BODY, fontSize=9.3, leading=13.4, textColor=colors.HexColor("#222B36"), spaceAfter=0)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.6, leading=11.6, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="BodyBold", textColor=colors.white)
CODE = ParagraphStyle("code", fontName="Mono", fontSize=6.9, leading=8.7, textColor=colors.HexColor("#1B2733"))

FOOTERS_DRAWN = []     # one entry per page, filled while building (the tests read this)


def _footer(label):
    def draw(canvas, doc):
        text = f"{config.ROLL_NO}  |  {config.STUDENT_NAME}  |  {label}"
        FOOTERS_DRAWN.append((label, doc.page, text))
        width = doc.pagesize[0]
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
        canvas.setFont("Body", 7.8)
        canvas.setFillColor(SLATE)
        canvas.drawString(18 * mm, 10.5 * mm, text)
        canvas.drawRightString(width - 18 * mm, 10.5 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def _cover(title, subtitle):
    band = Table([[Paragraph('<font color="#E9A23B" size="9"><b>' + config.PROGRAM.upper() + "</b></font>", BODY)],
                  [Paragraph(f'<font color="white" size="24"><b>{title}</b></font>', ParagraphStyle("t", leading=29))],
                  [Paragraph(f'<font color="#D6E4F0" size="11.5">{subtitle}</font>', ParagraphStyle("s", leading=16))]],
                 colWidths=[174 * mm])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 14 * mm),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 12 * mm), ("TOPPADDING", (0, 0), (0, 0), 14 * mm),
                              ("BOTTOMPADDING", (0, -1), (-1, -1), 14 * mm), ("BOTTOMPADDING", (0, 0), (-1, -2), 4)]))
    rows = [["Student name", config.STUDENT_NAME], ["Roll number", config.ROLL_NO], ["Programme", config.PROGRAM + ", Mini Project 2"],
            ["GitHub", f'<link href="{config.GITHUB_URL}" color="#1F3A5F"><u>{config.GITHUB_URL}</u></link>']]
    info = Table([[Paragraph(f"<b>{a}</b>", CELL), Paragraph(b, ParagraphStyle("v", parent=CELL, fontSize=10))] for a, b in rows],
                 colWidths=[38 * mm, 136 * mm])
    info.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 7),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("TEXTCOLOR", (0, 0), (0, -1), SLATE)]))
    return [Spacer(1, 45 * mm), band, Spacer(1, 16 * mm), info, PageBreak()]


def _caption_box(text):
    box = Table([[Paragraph("<b>Insight.</b> " + text, CAPTION)]], colWidths=[170 * mm])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F9FB")), ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
                             ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                             ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return box


def _image(path, max_width_mm=160, max_height_mm=88):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(max_width_mm / w, max_height_mm / h)
    return Image(str(path), width=w * scale * mm, height=h * scale * mm, hAlign="CENTER")


def _table(header, rows, widths):
    data = [[Paragraph(h, CELLB) for h in header]] + [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), PALE))
    t.setStyle(TableStyle(style))
    return t


def _kpi_cards(df):
    k = compute_kpis(df)
    items = [(f"\u20b9{k['total_sales'] / 1e6:,.2f} M", "Total sales"), (f"\u20b9{k['total_profit'] / 1e6:,.2f} M", "Total profit"),
             (f"{k['profit_margin']:.1f}%", "Profit margin"), (f"\u20b9{k['avg_order_value']:,.0f}", "Average order value")]
    cells = [[Paragraph(f'<para align="center"><font size="15" color="#1F3A5F"><b>{v}</b></font><br/><font size="8" color="#6B7A8F">{l}</font></para>', BODY) for v, l in items]]
    t = Table(cells, colWidths=[43.5 * mm] * 4)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F9FB")),
                           ("LINEABOVE", (0, 0), (-1, 0), 2.2, TEAL), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return t


QUESTIONS = {
    "01_monthly_sales_line": "How did sales move over the two years?", "02_sales_by_region_bar": "Which region sells the most?",
    "03_sales_by_category_bar": "Which product categories carry the business?", "04_age_histogram": "How old are the customers?",
    "05_income_histogram": "What do customers earn?", "06_segment_share_donut": "Which segment brings in the sales?",
    "07_sales_by_category_box": "How do order sizes differ between categories?", "08_sales_vs_profit_scatter": "Does profit follow sales?",
    "09_discount_vs_profit_scatter": "Do discounts eat into profit?", "10_correlation_heatmap": "Which numbers move together?",
    "11_category_region_heatmap": "Is order size about the product or the place?", "12_returns_by_satisfaction_bar": "What is linked to returns?",
    "13_delivery_time_box": "Do faster delivery modes arrive faster?",
}
TAKEAWAYS = [
    ("Sales are flat and have no repeating season (Figure 1)", "Growth has to come from new customers, products or prices, not from timing campaigns."),
    ("Electronics and Furniture bring in most of the sales (Figures 3, 7, 11)", "Protect stock, delivery and service in those two categories first."),
    ("Regions differ by about ten percent at most (Figures 2, 11)", "Set regional targets from each region's category mix."),
    ("Age and income say nothing about spending (Figures 4, 5, 10)", "Targeting by age or income is unlikely to pay off; product and price matter more."),
    ("Profit follows sales, and deeper discounts only weakly cut profit per order (Figures 8, 9)", "Try smaller discounts and see whether order sizes really change."),
    ("Unhappy customers return seven times as many orders (Figure 12)", "Find out what makes customers unhappy; that is the best route to fewer returns."),
    ("Same-Day orders arrive no faster than Standard ones (Figure 13)", "Check the delivery promise and how delivery dates are recorded."),
]


def build_report(df, captions, charts_dir, pdf_path):
    """Compile the visual report. Returns a dict describing what went in (the tests use it)."""
    FOOTERS_DRAWN[:] = []
    story = _cover("Retail Sales: A Visual Story", "Thirteen charts, each with an insight caption, for the sales and marketing team")
    story += [Paragraph("About this report", H1),
              Paragraph("The sales and marketing team does not have time to read a spreadsheet of seven thousand rows. "
                        "I took two years of the company's retail orders (January 2023 to December 2024, four regions of India) and turned them "
                        "into thirteen charts. Each chart answers one question, has a title that states what it found, and carries a short "
                        "caption that says why it matters.", BODY),
              Spacer(1, 3), _kpi_cards(df), Spacer(1, 8),
              Paragraph("The raw file was not ready to chart, so I did a small amount of cleaning first. There were 84 duplicated transactions, "
                        "dates in four different styles, eight spellings of two genders, twelve labels for four regions, a few impossible ages and "
                        "discounts, and nine incomes that were ten times too high. After cleaning, 7,000 unique orders remain. "
                        "Missing customer ratings and delivery dates were left empty, because filling them in would mean making up numbers.", BODY),
              Paragraph("How the charts are ordered", H2)]
    rows = []
    for number, chapter in CHAPTERS.items():
        keys = [k for k, _, _, ch in CHARTS if ch == number]
        figs = ", ".join(str([k for k, *_ in CHARTS].index(x) + 1) for x in keys)
        rows.append([f"{number}. {chapter}", figs])
    story += [_table(["Chapter", "Figures"], rows, [140, 30]), Spacer(1, 8),
              Paragraph("Colours mean the same thing on every page: navy is the normal colour, teal marks the leading group, and coral marks the "
                        "point being made (the weakest region, unhappy customers, the Same-Day mode).", BODY), PageBreak()]
    n_images = n_captions = 0
    number = 0
    current = None
    for key, _, kind, chapter in CHARTS:
        number += 1
        heading = []
        if chapter != current:
            heading = [Paragraph(f"{chapter}. {CHAPTERS[chapter]}", H1), HRFlowable(width="100%", thickness=0.8, color=TEAL, spaceAfter=4)]
            current = chapter
        block = heading + [Paragraph(f"Figure {number}  |  {kind}  |  {QUESTIONS[key]}", FIGLABEL), _image(Path(charts_dir) / f"{key}.png"),
                           Spacer(1, 4), _caption_box(captions[key]), Spacer(1, 10)]
        story.append(KeepTogether(block))      # heading, chart and caption never get split across pages
        n_images += 1
        n_captions += 1
    story += [PageBreak(), Paragraph("Summary: what the charts say together", H1),
              Paragraph("Taken together, the charts describe a steady business whose results depend on what it sells, not on where it sells "
                        "or who buys.", BODY),
              _table(["What the charts show", "What it means for the business"], TAKEAWAYS, [88, 82]), Spacer(1, 10),
              Paragraph("How this report was made", H2),
              Paragraph(f"Every chart, caption and number in this report comes from the Python code in the project repository, so it can be rebuilt "
                        f"with one command (<font name='Mono'>python run_all.py</font>). The interactive version of these charts is the Streamlit "
                        f"dashboard in <font name='Mono'>dashboard/app.py</font>. Repository: "
                        f'<link href="{config.GITHUB_URL}" color="#1F3A5F"><u>{config.GITHUB_URL}</u></link>', BODY)]
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm,
                            title=f"{config.PROJECT_TITLE} - {config.STUDENT_NAME} ({config.ROLL_NO})", author=config.STUDENT_NAME)
    label = "Data Visualization Report"
    doc.build(story, onFirstPage=_footer(label), onLaterPages=_footer(label))
    return {"figures": n_images, "captions": n_captions, "pages": len(FOOTERS_DRAWN)}


# ----------------------------------------------------------------------------- code snapshot
CODE_FILES = ["config.py", "run_all.py", "requirements.txt", "src/data_cleaning.py", "src/visualizations.py", "src/captions.py",
              "src/metrics.py", "src/build_report.py", "dashboard/app.py", "tests/test_data_cleaning.py", "tests/test_visualizations.py",
              "tests/test_report.py", "tests/test_dashboard.py"]


def _numbered(text, width=160):
    import textwrap
    out = []
    for i, line in enumerate(text.rstrip("\n").split("\n"), 1):
        parts = textwrap.wrap(line.replace("\t", "    "), width, subsequent_indent="        ", drop_whitespace=False, replace_whitespace=False) or [""]
        out.append(f"{i:4d}  {parts[0]}")
        out += [f"      {p}" for p in parts[1:]]
    return "\n".join(out)


def build_code_snapshot(pdf_path, root=None):
    """A PDF that contains every source file of the project, with line numbers."""
    root = Path(root or config.ROOT)
    FOOTERS_DRAWN[:] = []
    story = _cover("Code Snapshot", "Complete Python source of the Data Visualization project") [:-1]
    story = [Spacer(1, 25 * mm)] + story[1:]
    index = []
    for f in CODE_FILES:
        index.append([f, len((root / f).read_text(encoding="utf-8").split("\n"))])
    story += [Paragraph("Files in this snapshot", H1), _table(["File", "Lines"], index, [140, 30])]
    included = []
    for f in CODE_FILES:
        text = (root / f).read_text(encoding="utf-8")
        story += [PageBreak(), Paragraph(f, ParagraphStyle("fn", fontName="BodyBold", fontSize=11, textColor=colors.white, backColor=NAVY,
                                                           borderPadding=(5, 6, 5, 6), spaceAfter=10)), Preformatted(_numbered(text), CODE)]
        included.append(f)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm, bottomMargin=20 * mm,
                            title=f"Code Snapshot - {config.STUDENT_NAME} ({config.ROLL_NO})", author=config.STUDENT_NAME)
    doc.build(story, onFirstPage=_footer("Code Snapshot"), onLaterPages=_footer("Code Snapshot"))
    return {"files": included, "pages": len(FOOTERS_DRAWN)}

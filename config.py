"""Settings used by every script in the project.

Student details, file paths and the colour palette live here so that they are
changed in one place only.
"""
from pathlib import Path

# ---- student details (printed on the report cover and in every page footer) ----
STUDENT_NAME = "Anish Kumar"
ROLL_NO = "2026M01410002"
GITHUB_URL = "https://github.com/AnishWebDesigner/Data-Analyst-Project"
PROGRAM = "Data Analyst Training Program"
PROJECT_TITLE = "Data Visualization: Turning Retail Sales Data into a Visual Story"

# ---- paths ----
ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / "data" / "retail_customer_sales_dataset.csv"
CLEAN_CSV = ROOT / "data" / "retail_customer_sales_cleaned.csv"
OUT_DIR = ROOT / "outputs"
CHART_DIR = OUT_DIR / "charts"
FILE_PREFIX = f"{ROLL_NO}_{STUDENT_NAME.replace(' ', '-')}"
REPORT_PDF = OUT_DIR / f"{FILE_PREFIX}_Data_Visualization_Report.pdf"
SNAPSHOT_PDF = OUT_DIR / f"{FILE_PREFIX}_Code_Snapshot.pdf"
TEST_RESULTS = OUT_DIR / "test_results.txt"

# ---- colour palette (same colours in every chart, report and dashboard) ----
NAVY = "#1F3A5F"      # default colour for bars, lines and histograms
TEAL = "#2A9D8F"      # the best / leading group
CORAL = "#E76F51"     # the point being made (weakest region, unhappy customers ...)
AMBER = "#E9A23B"     # second accent
SLATE = "#6B7A8F"     # secondary text, reference lines
GREY = "#C5CED8"      # groups that are not the focus

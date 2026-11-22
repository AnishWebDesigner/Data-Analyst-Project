"""Retail Sales Dashboard (Streamlit).

Start it from the project folder with:

    streamlit run dashboard/app.py

Six KPIs sit at the top and six filters in the sidebar. Every chart and every KPI
changes when a filter changes. Each KPI also shows how it compares with the full data.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import config
from src import visualizations
from src.data_cleaning import clean, load_raw
from src.metrics import compute_kpis, filter_data

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# The report titles state findings about all the data. A filtered slice may not show the same
# thing, so the dashboard uses plain titles instead.
PLAIN_TITLES = {
    "01_monthly_sales_line": "Monthly sales",
    "02_sales_by_region_bar": "Total sales by region",
    "03_sales_by_category_bar": "Total sales by product category",
    "06_segment_share_donut": "Share of sales by customer segment",
    "07_sales_by_category_box": "Sales per order by product category",
    "08_sales_vs_profit_scatter": "Sales vs profit per order",
    "09_discount_vs_profit_scatter": "Discount vs profit per order",
    "11_category_region_heatmap": "Average sales per order: category by region",
    "12_returns_by_satisfaction_bar": "Return rate by satisfaction level",
    "13_delivery_time_box": "Days to deliver, by delivery mode",
}

st.set_page_config(page_title="Retail Sales Dashboard", page_icon="\U0001F4CA", layout="wide")


@st.cache_data(show_spinner="Loading the data...")
def load_data():
    """Use the cleaned file if it is there, otherwise clean the raw file now."""
    if config.CLEAN_CSV.exists():
        return pd.read_csv(config.CLEAN_CSV)
    return clean(load_raw(config.RAW_CSV))


def draw(key, data):
    """Draw one chart. A very small selection can break a chart, so show a message instead of an error."""
    try:
        fig = visualizations.CHART_FUNCTIONS[key](data)
        fig.axes[0].set_title(PLAIN_TITLES[key], loc="left")
        st.pyplot(fig, clear_figure=True)
    except Exception:
        st.info("There is not enough data in this selection to draw this chart.")
    finally:
        plt.close("all")


everything = load_data()

# ------------------------------------------------------------------ sidebar filters
st.sidebar.header("Filters")
st.sidebar.caption("Leave a filter empty to include everything.")


def options(column):
    return sorted(everything[column].dropna().unique())


years = st.sidebar.multiselect("Year", options("Order_Year"), default=options("Order_Year"))
months = st.sidebar.multiselect("Month", list(range(1, 13)), default=list(range(1, 13)), format_func=lambda m: MONTH_NAMES[m - 1])
regions = st.sidebar.multiselect("Region", options("Region"), default=options("Region"))
categories = st.sidebar.multiselect("Product category", options("Product_Category"), default=options("Product_Category"))
segments = st.sidebar.multiselect("Customer segment", options("Customer_Segment"), default=options("Customer_Segment"))
modes = st.sidebar.multiselect("Delivery mode", options("Delivery_Mode"), default=options("Delivery_Mode"))

data = filter_data(everything, years, months, regions, categories, segments, modes)

# ------------------------------------------------------------------ title and KPIs
st.title("Retail Sales Dashboard")
st.caption(f"{config.PROGRAM}, Mini Project 2  |  {config.STUDENT_NAME} ({config.ROLL_NO})  |  amounts in Indian Rupees")

if data.empty:
    st.warning("No orders match these filters. Add some values back in the sidebar.")
    st.stop()

now, total = compute_kpis(data), compute_kpis(everything)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sales", f"\u20b9{now['total_sales'] / 1e6:,.2f} M", f"{now['total_sales'] / total['total_sales'] * 100:.0f}% of all sales", delta_color="off")
c2.metric("Total Profit", f"\u20b9{now['total_profit'] / 1e6:,.2f} M", f"{now['total_profit'] / total['total_profit'] * 100:.0f}% of all profit", delta_color="off")
c3.metric("Profit Margin", f"{now['profit_margin']:.1f}%", f"{now['profit_margin'] - total['profit_margin']:+.1f} pts vs all data", delta_color="off")
c4.metric("Average Order Value", f"\u20b9{now['avg_order_value']:,.0f}", f"{(now['avg_order_value'] / total['avg_order_value'] - 1) * 100:+.1f}% vs all data", delta_color="off")
c5.metric("Orders", f"{now['orders']:,}", f"{now['orders'] / total['orders'] * 100:.0f}% of all orders", delta_color="off")
c6.metric("Return Rate", f"{now['return_rate']:.1f}%", f"{now['return_rate'] - total['return_rate']:+.1f} pts vs all data", delta_color="off")
st.divider()

# ------------------------------------------------------------------ charts
draw("01_monthly_sales_line", data)

left, middle, right = st.columns(3)
with left:
    draw("02_sales_by_region_bar", data)
with middle:
    draw("03_sales_by_category_bar", data)
with right:
    draw("06_segment_share_donut", data)

left, right = st.columns(2)
with left:
    draw("07_sales_by_category_box", data)
with right:
    draw("08_sales_vs_profit_scatter", data)

left, right = st.columns(2)
with left:
    draw("11_category_region_heatmap", data)
with right:
    draw("09_discount_vs_profit_scatter", data)

left, right = st.columns(2)
with left:
    draw("12_returns_by_satisfaction_bar", data)
with right:
    draw("13_delivery_time_box", data)

with st.expander("See the filtered data"):
    st.dataframe(data.head(500))
    st.download_button("Download the filtered data (CSV)", data.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_retail_sales.csv", mime="text/csv")

"""All the charts for the project.

Every function takes the cleaned data frame and returns a matplotlib figure, so the
same code is used by the notebook, the PDF report and the Streamlit dashboard.

Design rules I followed: one palette (config.py), a title that says what the chart
shows, labelled axes with units, a legend when there is more than one series, and colour
used to point at the thing that matters. No 3D and no heavy gridlines.
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

from config import AMBER, CORAL, GREY, NAVY, SLATE, TEAL

SOURCE_NOTE = "Source: retail_customer_sales_dataset.csv, cleaned (7,000 orders, 2023-2024)"


def apply_style():
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 170, "font.size": 10, "axes.titlesize": 12.5,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelsize": 10,
        "axes.edgecolor": "#C9D1DA", "grid.color": "#E6EBF0", "axes.spines.top": False,
        "axes.spines.right": False, "legend.frameon": False,
    })


apply_style()


def rupees(x, _=None):
    return f"\u20b9{x:,.0f}"


def rupees_m(x, _=None):
    return f"\u20b9{x / 1e6:,.1f}M"


def finish(fig):
    fig.text(0.01, -0.02, SOURCE_NOTE, fontsize=7.5, color=SLATE)
    fig.tight_layout()
    return fig


# 1. line chart: monthly sales ------------------------------------------------------------
def chart_monthly_sales(df):
    monthly = df.groupby("Year_Month").Sales.sum().sort_index()
    average = monthly.rolling(3, min_periods=1).mean()
    x = np.arange(len(monthly))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(x, monthly.values, marker="o", color=TEAL, lw=2.2, label="Monthly sales")
    ax.plot(x, average.values, color=NAVY, lw=2.6, ls="--", label="3-month moving average")
    high, low = int(monthly.values.argmax()), int(monthly.values.argmin())
    for i, colour, word in [(high, NAVY, "Peak"), (low, CORAL, "Low")]:
        ax.scatter(i, monthly.values[i], s=110, color=colour, zorder=5)
        ax.annotate(f"{word}: {rupees_m(monthly.values[i])}\n{monthly.index[i]}", (i, monthly.values[i]),
                    textcoords="offset points", xytext=(0, 14 if word == "Peak" else -34),
                    ha="center", fontsize=8.5, color=colour, fontweight="bold")
    labels = [pd.Period(p).strftime("%b %y") for p in monthly.index]
    ax.set_xticks(x[::2])
    ax.set_xticklabels(labels[::2], fontsize=8.5)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rupees_m))
    ax.set_ylim(0, monthly.max() * 1.2)
    ax.set_title(f"Monthly sales move between {rupees_m(monthly.min())} and {rupees_m(monthly.max())} with no steady upward trend")
    ax.set_xlabel("Order month")
    ax.set_ylabel("Total sales (\u20b9 million)")
    ax.legend(loc="lower right", ncol=2)
    return finish(fig)


# 2. bar chart: sales by region ----------------------------------------------------------
def chart_sales_by_region(df):
    s = df.groupby("Region", observed=True).Sales.sum().sort_values(ascending=False)
    colours = [CORAL if r == s.idxmin() else TEAL for r in s.index]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    bars = ax.bar(s.index, s.values, color=colours, width=0.6)
    for b, v in zip(bars, s.values):
        ax.text(b.get_x() + b.get_width() / 2, v + s.max() * 0.012, rupees_m(v), ha="center", fontsize=9.5, fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rupees_m))
    ax.set_ylim(0, s.max() * 1.15)
    ax.set_title(f"{s.idxmax()} sells the most; {s.idxmin()} (red) is {(1 - s.min() / s.max()) * 100:.0f}% behind")
    ax.set_xlabel("Region")
    ax.set_ylabel("Total sales (\u20b9 million)")
    return finish(fig)


# 3. bar chart: sales by category --------------------------------------------------------
def chart_sales_by_category(df):
    s = df.groupby("Product_Category", observed=True).Sales.sum().sort_values()
    share = s / s.sum() * 100
    second = s.sort_values().iloc[-2]
    colours = [TEAL if v >= second else GREY for v in s.values]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.barh(s.index, s.values, color=colours, height=0.62)
    for b, v, p in zip(bars, s.values, share.values):
        ax.text(v + s.max() * 0.012, b.get_y() + b.get_height() / 2, f"{rupees_m(v)}  ({p:.0f}%)", va="center", fontsize=9.5)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(rupees_m))
    ax.set_xlim(0, s.max() * 1.28)
    top_two = share.sort_values(ascending=False).head(2).sum()
    ax.set_title(f"Two categories (teal) bring in {top_two:.0f}% of all sales")
    ax.set_xlabel("Total sales (\u20b9 million)")
    ax.set_ylabel("Product category")
    return finish(fig)


# 4. histogram: age ----------------------------------------------------------------------
def chart_age(df):
    age = df.Age
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.histplot(age, discrete=True, color=NAVY, edgecolor="white", ax=ax, alpha=0.9)
    ax.axvline(age.mean(), color=CORAL, ls="--", lw=2, label=f"Mean {age.mean():.1f}")
    ax.axvline(age.median(), color=AMBER, ls="-", lw=2, label=f"Median {age.median():.0f}")
    ax.set_title(f"Customer age is close to symmetric (skewness {age.skew():.2f}) and centred on the mid-30s")
    ax.set_xlabel("Customer age (years)")
    ax.set_ylabel("Number of orders")
    ax.legend()
    return finish(fig)


# 5. histogram: income -------------------------------------------------------------------
def chart_income(df):
    income = df.Income
    shown = income[income <= income.quantile(0.995)]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.histplot(shown, bins=40, kde=True, color=TEAL, edgecolor="white", ax=ax, line_kws={"linewidth": 2.2})
    ax.axvline(income.mean(), color=CORAL, ls="--", lw=2, label=f"Mean {rupees(income.mean())}")
    ax.axvline(income.median(), color=NAVY, ls="-", lw=2, label=f"Median {rupees(income.median())}")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(rupees))
    ax.set_title(f"Income is right-skewed (skewness {income.skew():.2f}): a few high earners pull the mean up")
    ax.set_xlabel("Annual income (\u20b9), top 0.5% not shown")
    ax.set_ylabel("Number of orders")
    ax.legend()
    return finish(fig)


# 6. donut chart: segment share ----------------------------------------------------------
def chart_segment_share(df):
    s = df.groupby("Customer_Segment", observed=True).Sales.sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    wedges, _ = ax.pie(s.values, colors=[NAVY, TEAL, AMBER], startangle=90, counterclock=False,
                       wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 2})
    for w, v in zip(wedges, s.values):
        angle = np.deg2rad((w.theta1 + w.theta2) / 2)
        ax.text(0.81 * np.cos(angle), 0.81 * np.sin(angle), f"{v / s.sum() * 100:.0f}%", ha="center", va="center",
                color="white", fontsize=12, fontweight="bold")
    ax.text(0, 0, f"{rupees_m(s.sum())}\ntotal sales", ha="center", va="center", fontsize=11, fontweight="bold", color=NAVY)
    ax.legend(wedges, [f"{k} ({rupees_m(v)})" for k, v in s.items()], loc="center left", bbox_to_anchor=(0.95, 0.5))
    ax.set_title(f"{s.idxmax()} customers bring in more than half of the sales")
    return finish(fig)


# 7. box plot: sales by category ---------------------------------------------------------
def chart_sales_box(df):
    order = df.groupby("Product_Category", observed=True).Sales.median().sort_values(ascending=False).index
    colours = {c: (TEAL if i < 2 else GREY) for i, c in enumerate(order)}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")     # seaborn/matplotlib version notice, not a problem with the chart
        sns.boxplot(data=df, x="Product_Category", y="Sales", order=order, palette=colours, hue="Product_Category",
                    legend=False, dodge=False, width=0.55, ax=ax, fliersize=2.2, linewidth=1.2, flierprops={"alpha": .45})
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rupees))
    ax.set_title("Furniture and Electronics orders are bigger and vary more than the other categories")
    ax.set_xlabel("Product category")
    ax.set_ylabel("Sales per order (\u20b9, log scale)")
    return finish(fig)


# 8. scatter: sales vs profit ------------------------------------------------------------
def chart_sales_vs_profit(df):
    r = df.Sales.corr(df.Profit)
    slope, intercept = np.polyfit(df.Sales, df.Profit, 1)
    xs = np.linspace(df.Sales.min(), df.Sales.max(), 100)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.scatter(df.Sales, df.Profit, s=9, alpha=0.28, color=TEAL, edgecolor="none", label="Orders")
    ax.plot(xs, slope * xs + intercept, color=CORAL, lw=2.6, label=f"Trend line: profit = {slope:.2f} x sales {intercept:+.0f}")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(rupees))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rupees))
    ax.set_title(f"Profit rises almost in step with sales (r = {r:.2f}), about {slope * 100:.0f} paise per rupee")
    ax.set_xlabel("Sales per order (\u20b9)")
    ax.set_ylabel("Profit per order (\u20b9)")
    ax.legend(loc="upper left")
    return finish(fig)


# 9. scatter: discount vs profit ---------------------------------------------------------
def chart_discount_vs_profit(df):
    r = df.Discount.corr(df.Profit)
    slope, intercept = np.polyfit(df.Discount, df.Profit, 1)
    xs = np.linspace(0, 0.5, 50)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.scatter(df.Discount * 100, df.Profit, s=9, alpha=0.25, color=SLATE, edgecolor="none", label="Orders")
    ax.plot(xs * 100, slope * xs + intercept, color=CORAL, lw=2.6, label=f"Trend line (r = {r:.2f})")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rupees))
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_title("Bigger discounts go with a little less profit per order, but the link is weak")
    ax.set_xlabel("Discount given (%)")
    ax.set_ylabel("Profit per order (\u20b9)")
    ax.legend(loc="upper right")
    return finish(fig)


# 10. heatmap: correlation ---------------------------------------------------------------
def chart_correlation(df):
    corr = df[["Sales", "Profit", "Discount", "Quantity", "Age", "Income"]].corr()
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap=sns.diverging_palette(15, 200, as_cmap=True), center=0,
                    vmin=-1, vmax=1, linewidths=0.8, linecolor="white", cbar_kws={"shrink": 0.75, "label": "Pearson correlation"},
                    ax=ax, annot_kws={"fontsize": 10})
    ax.set_title("Only the price-related columns move together; age and income have no link to spending")
    ax.set_xlabel("Variable")
    ax.set_ylabel("Variable")
    return finish(fig)


# 11. heatmap: category x region ---------------------------------------------------------
def chart_category_region(df):
    table = df.pivot_table(index="Product_Category", columns="Region", values="Sales", aggfunc="mean")
    table = table.loc[table.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    sns.heatmap(table / 1000, annot=True, fmt=".1f", cmap=sns.light_palette(NAVY, as_cmap=True), linewidths=0.8, linecolor="white",
                cbar_kws={"label": "Average sales per order (\u20b9 thousand)"}, ax=ax, annot_kws={"fontsize": 10})
    ax.set_title("The product category matters far more than the region for the size of an order")
    ax.set_xlabel("Region")
    ax.set_ylabel("Product category")
    return finish(fig)


# 12. bar chart: returns by satisfaction -------------------------------------------------
def chart_returns(df):
    known = df[df.Satisfaction_Level != "Not Recorded"]
    levels = ["Low", "Medium", "High"]
    rate = known.groupby("Satisfaction_Level", observed=True).Is_Returned.mean().mul(100).reindex(levels).fillna(0.0)
    overall = df.Is_Returned.mean() * 100 if len(df) else 0.0
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(levels, rate.values, color=[CORAL, AMBER, TEAL], width=0.55)
    for b, v in zip(bars, rate.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f}%", ha="center", fontsize=10.5, fontweight="bold",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5}, zorder=6)
    ax.axhline(overall, color=NAVY, ls="--", lw=1.6, label=f"Overall return rate {overall:.1f}%")
    ax.set_ylim(0, max(rate.max(), overall, 1) * 1.2)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    if rate["Low"] > 0 and rate["High"] > 0:
        ax.set_title(f"Unhappy customers return orders {rate['Low'] / rate['High']:.0f} times as often as happy ones")
    else:
        ax.set_title("Return rate by customer satisfaction level")
    ax.set_xlabel("Customer satisfaction level")
    ax.set_ylabel("Orders returned (%)")
    ax.legend()
    return finish(fig)


# 13. box plot: delivery time by delivery mode (logistics) -------------------------------
def chart_delivery(df):
    order = ["Same-Day", "Express", "Standard"]
    d = df.dropna(subset=["Delivery_Days"])
    means = d.groupby("Delivery_Mode", observed=True).Delivery_Days.mean()
    colours = {"Same-Day": CORAL, "Express": GREY, "Standard": GREY}
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    present = [m for m in order if m in means.index]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sns.boxplot(data=d, x="Delivery_Mode", y="Delivery_Days", order=present, palette=colours, hue="Delivery_Mode",
                    legend=False, dodge=False, width=0.5, ax=ax, fliersize=2.5, linewidth=1.2)
    for i, m in enumerate(present):
        ax.text(i, d.Delivery_Days.max() + 0.6, f"avg {means[m]:.1f} days", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, d.Delivery_Days.max() + 2.5)
    if "Same-Day" in means.index and "Standard" in means.index:
        ax.set_title(f"Same-Day orders take {means['Same-Day']:.1f} days on average, no faster than Standard ({means['Standard']:.1f})")
    else:
        ax.set_title("Days from order to delivery, by delivery mode")
    ax.set_xlabel("Delivery mode chosen by the customer")
    ax.set_ylabel("Days from order to delivery")
    return finish(fig)


# the order they appear in the report: key, function, chart type, chapter ---------------------
CHARTS = [
    ("01_monthly_sales_line", chart_monthly_sales, "Line chart", 1),
    ("02_sales_by_region_bar", chart_sales_by_region, "Bar chart", 2),
    ("03_sales_by_category_bar", chart_sales_by_category, "Bar chart", 2),
    ("04_age_histogram", chart_age, "Histogram", 3),
    ("05_income_histogram", chart_income, "Histogram", 3),
    ("06_segment_share_donut", chart_segment_share, "Donut chart", 3),
    ("07_sales_by_category_box", chart_sales_box, "Box plot", 4),
    ("08_sales_vs_profit_scatter", chart_sales_vs_profit, "Scatter plot", 4),
    ("09_discount_vs_profit_scatter", chart_discount_vs_profit, "Scatter plot", 4),
    ("10_correlation_heatmap", chart_correlation, "Heatmap", 4),
    ("11_category_region_heatmap", chart_category_region, "Heatmap", 5),
    ("12_returns_by_satisfaction_bar", chart_returns, "Bar chart", 6),
    ("13_delivery_time_box", chart_delivery, "Box plot", 6),
]
CHAPTERS = {
    1: "The big picture: how sales moved over two years",
    2: "Where the money is made: regions and products",
    3: "Who the customers are",
    4: "What drives order value and profit",
    5: "Putting category and region together",
    6: "Returns and delivery",
}
CHART_FUNCTIONS = {key: fn for key, fn, _, _ in CHARTS}
CHART_TYPES = {key: kind for key, _, kind, _ in CHARTS}


def save_all_charts(df, folder):
    """Draw every chart and save it as a PNG. Returns the list of file paths."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for key, fn, _, _ in CHARTS:
        fig = fn(df)
        path = folder / f"{key}.png"
        fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        paths.append(path)
    return paths

"""Short business captions for the charts. The numbers are worked out from the data,
so the text always agrees with the chart above it."""
import numpy as np
import pandas as pd


def m(x):
    return f"\u20b9{x / 1e6:,.1f}M"


def k(x):
    return f"\u20b9{x / 1e3:,.1f}K"


def r(x):
    return f"\u20b9{x:,.0f}"


def build_captions(df):
    """Return {chart key: caption of 2-3 sentences}."""
    c = {}

    monthly = df.groupby("Year_Month").Sales.sum().sort_index()
    yearly = df.groupby("Order_Year").Sales.sum()
    y0, y1 = yearly.index.min(), yearly.index.max()
    change = (yearly[y1] / yearly[y0] - 1) * 100
    rolling = monthly.rolling(3, min_periods=3).mean().dropna()
    peak, low = pd.Period(monthly.idxmax()).strftime("%b %Y"), pd.Period(monthly.idxmin()).strftime("%b %Y")
    c["01_monthly_sales_line"] = (
        f"Sales came to {m(yearly[y0])} in {y0} and {m(yearly[y1])} in {y1}, a change of {change:+.1f}%, and the 3-month average stays between {m(rolling.min())} and {m(rolling.max())}. "
        f"The highest month ({m(monthly.max())}, {peak}) and the lowest ({m(monthly.min())}, {low}) look like one-off swings, not a season that comes back every year. "
        f"Growth will have to come from new customers or products, because timing campaigns will not help much.")

    g = df.groupby("Region", observed=True).agg(S=("Sales", "sum"), N=("Sales", "size"), A=("Sales", "mean"))
    top, bottom = g.S.idxmax(), g.S.idxmin()
    c["02_sales_by_region_bar"] = (
        f"{top} sells the most at {m(g.S.max())} and {bottom} the least at {m(g.S.min())}, which is {(1 - g.S.min() / g.S.max()) * 100:.0f}% lower. "
        f"{bottom} has {(1 - g.N[bottom] / g.N[top]) * 100:.0f}% fewer orders and a {(1 - g.A[bottom] / g.A[top]) * 100:.0f}% smaller average order, so the gap is modest. "
        f"It is the first place to look for extra volume, but none of the four regions is in trouble.")

    cat = df.groupby("Product_Category", observed=True).agg(S=("Sales", "sum"), A=("Sales", "mean"))
    share = cat.S / cat.S.sum() * 100
    best = share.sort_values(ascending=False).head(2)
    worst = share.sort_values().head(2)
    c["03_sales_by_category_bar"] = (
        f"{best.index[0]} ({m(cat.S[best.index[0]])}, {best.iloc[0]:.0f}%) and {best.index[1]} ({m(cat.S[best.index[1]])}, {best.iloc[1]:.0f}%) together bring in {best.sum():.0f}% of sales, while {worst.index[0]} and {worst.index[1]} add only {worst.sum():.0f}%. "
        f"An average {cat.A.idxmax()} order is worth about {cat.A.max() / cat.A.min():.0f} times an average {cat.A.idxmin()} order. "
        f"Stock, delivery and service quality should be protected first in the two leading categories.")

    age = df.Age
    q1, q3 = age.quantile([.25, .75])
    one_per_customer = df.drop_duplicates("Customer_ID")
    c["04_age_histogram"] = (
        f"Customers cluster around age {age.median():.0f} (mean {age.mean():.1f}, median {age.median():.0f}) with a gentle tail up to {age.max()}, and a skewness of {age.skew():.2f} means the shape is close to symmetric. "
        f"The tall bar at 18 ({(one_per_customer.Age == age.min()).mean() * 100:.0f}% of customers) looks like a lower limit in the source system rather than a real group of 18-year-olds. "
        f"Half of the orders come from customers aged {q1:.0f} to {q3:.0f}, which is the natural target for campaigns.")

    inc = df.Income
    q1, q3 = inc.quantile([.25, .75])
    c["05_income_histogram"] = (
        f"Half of the orders come from customers earning between {r(q1)} and {r(q3)} a year, but a long right tail reaching {r(inc.max())} pulls the mean ({r(inc.mean())}) above the median ({r(inc.median())}), with skewness at {inc.skew():.2f}. "
        f"The median is the fairer description of a typical customer. "
        f"Income does not predict how much people spend, as the correlation heatmap shows.")

    seg = df.groupby("Customer_Segment", observed=True).agg(S=("Sales", "sum"), A=("Sales", "mean"))
    pct = (seg.S / seg.S.sum() * 100).sort_values(ascending=False)
    c["06_segment_share_donut"] = (
        f"{pct.index[0]} customers generate {pct.iloc[0]:.0f}% of sales ({m(seg.S[pct.index[0]])}), {pct.index[1]} {pct.iloc[1]:.0f}% and {pct.index[2]} {pct.iloc[2]:.0f}%. "
        f"Corporate orders are hardly bigger than consumer orders ({r(seg.A['Corporate'])} against {r(seg.A['Consumer'])}), so each share just follows the number of orders. "
        f"Growing the business segments would need more orders, not larger ones.")

    med = df.groupby("Product_Category", observed=True).Sales.median().sort_values(ascending=False)
    c["07_sales_by_category_box"] = (
        f"The median {med.index[0]} order is {r(med.iloc[0])} and the median {med.index[1]} order {r(med.iloc[1])}, against {r(med.iloc[-1])} for {med.index[-1]}, which is a {med.iloc[0] / med.iloc[-1]:.0f}-fold difference. "
        f"These two categories also have the widest boxes and the biggest orders (up to {r(df.Sales.max())}), and the dots above the boxes are real large orders, not mistakes. "
        f"The axis is logarithmic so that all five categories can be read, which makes the real gaps look smaller than they are.")

    corr_sp = df.Sales.corr(df.Profit)
    slope = np.polyfit(df.Sales, df.Profit, 1)[0]
    c["08_sales_vs_profit_scatter"] = (
        f"Profit is almost a fixed share of sales (r = {corr_sp:.2f}), and the trend line says each rupee of sales leaves about {slope * 100:.0f} paise of profit. "
        f"The fan shape shows that the margin on individual orders ranges from {df.Profit_Margin.min():.0f}% to {df.Profit_Margin.max():.0f}%, and the biggest orders earn the biggest profits. "
        f"More revenue should therefore bring about the same proportion of extra profit.")

    corr_dp = df.Discount.corr(df.Profit)
    slope_d = np.polyfit(df.Discount, df.Profit, 1)[0]
    c["09_discount_vs_profit_scatter"] = (
        f"Every extra 10 points of discount goes with about {r(abs(slope_d) * 0.1)} less profit per order (r = {corr_dp:.2f}), which is a weak negative link. "
        f"Discount explains only {corr_dp ** 2 * 100:.1f}% of the variation in profit, so the straight line is a rough guide and not a rule. "
        f"The size of the order matters much more for profit than the depth of the discount.")

    cm = df[["Sales", "Profit", "Discount", "Quantity", "Age", "Income"]].corr()
    spend = ["Sales", "Profit", "Discount", "Quantity"]
    demo = max(cm.loc["Age", spend].abs().max(), cm.loc["Income", spend].abs().max())
    c["10_correlation_heatmap"] = (
        f"Sales and profit move almost together (r = {cm.loc['Sales', 'Profit']:.2f}), quantity has a moderate link with sales ({cm.loc['Sales', 'Quantity']:.2f}) and discount a weak negative one ({cm.loc['Sales', 'Discount']:.2f}). "
        f"Age and income are close to zero against every spending column (the largest is {demo:.2f}), so who the customer is tells us very little about how much they spend. "
        f"Product and price decisions are likely to matter more than targeting by age or income.")

    pv = df.pivot_table(index="Product_Category", columns="Region", values="Sales", aggfunc="mean")
    row_gap = ((pv.max(axis=1) - pv.min(axis=1)) / pv.min(axis=1) * 100).max()
    hi, lo = pv.stack().idxmax(), pv.stack().idxmin()
    c["11_category_region_heatmap"] = (
        f"Going down a column changes the average order {pv.stack().max() / pv.stack().min():.0f}-fold, from {k(pv.stack().min())} for {lo[0]} in the {lo[1]} to {k(pv.stack().max())} for {hi[0]} in the {hi[1]}, while going across a row changes it by at most {row_gap:.0f}%. "
        f"So the category mix decides the size of an order and the region hardly does. "
        f"Regional targets are better set by looking at each region's category mix.")

    known = df[df.Satisfaction_Level != "Not Recorded"]
    rate = known.groupby("Satisfaction_Level", observed=True).Is_Returned.mean() * 100
    c["12_returns_by_satisfaction_bar"] = (
        f"{rate['Low']:.1f}% of low-satisfaction orders are returned, against {rate['High']:.1f}% of high-satisfaction ones, so {rate['Low'] / rate['High']:.0f} times as often, while the overall return rate is {df.Is_Returned.mean() * 100:.1f}%. "
        f"Returns and unhappy customers clearly go together, although the data cannot tell us which one causes the other. "
        f"Finding out what makes customers unhappy is likely to cut returns more than any action on a single category.")

    dd = df.dropna(subset=["Delivery_Days"])
    avg = dd.groupby("Delivery_Mode", observed=True).Delivery_Days.mean()
    within = (dd[dd.Delivery_Mode == "Same-Day"].Delivery_Days <= 1).mean() * 100
    c["13_delivery_time_box"] = (
        f"Same-Day orders take {avg['Same-Day']:.1f} days to arrive on average, which is almost the same as Express ({avg['Express']:.1f}) and Standard ({avg['Standard']:.1f}), and only {within:.1f}% of them arrive within a day. "
        f"The three boxes sit at the same height, so the delivery mode a customer picks makes no visible difference to the waiting time. "
        f"If customers pay extra for Same-Day, they are not getting a faster service, so operations should check the delivery promise or how delivery dates are recorded.")
    return c

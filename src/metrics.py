"""KPI numbers and filters. The Streamlit dashboard and the tests both use these functions."""


def compute_kpis(df):
    """The six headline numbers for whatever rows are passed in. Safe for an empty selection."""
    orders = len(df)
    sales, profit = float(df.Sales.sum()), float(df.Profit.sum())
    return {
        "total_sales": sales,
        "total_profit": profit,
        "profit_margin": profit / sales * 100 if sales else 0.0,
        "avg_order_value": sales / orders if orders else 0.0,
        "orders": orders,
        "return_rate": float(df.Is_Returned.mean() * 100) if orders else 0.0,
    }


def filter_data(df, years=None, months=None, regions=None, categories=None, segments=None, delivery_modes=None):
    """Keep the rows that match every filter. A filter left empty (None or []) keeps everything."""
    keep = df.index == df.index
    pairs = [("Order_Year", years), ("Order_Month", months), ("Region", regions), ("Product_Category", categories),
             ("Customer_Segment", segments), ("Delivery_Mode", delivery_modes)]
    for column, wanted in pairs:
        if wanted:
            keep &= df[column].isin(list(wanted)).to_numpy()
    return df[keep]

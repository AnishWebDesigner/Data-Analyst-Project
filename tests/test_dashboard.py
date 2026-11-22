"""Tests for the dashboard logic and for dashboard/app.py.

Streamlit is replaced by a small stand-in that records what the app asks for. That checks the
app's own code (filters, KPIs, charts, empty selection) without needing a browser.
"""
import itertools
import runpy
import sys
import types
import unittest

import pandas as pd

import config
from helpers import ROOT, clean_data, ensure_clean_csv, make_raw
from src.data_cleaning import clean
from src.metrics import compute_kpis, filter_data


class Column:
    """Acts like one Streamlit column: it has .metric() and can be used in a with block."""

    def __init__(self, fake):
        self.fake = fake

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def metric(self, label, value, delta=None, **kwargs):
        self.fake.metrics[label] = value
        self.fake.deltas[label] = delta


class FakeStreamlit(types.ModuleType):
    def __init__(self, picks=None):
        super().__init__("streamlit")
        self.picks = picks or {}
        self.metrics, self.deltas, self.filters = {}, {}, []
        self.charts = self.messages = self.warnings = 0
        self.stopped = False
        self.sidebar = self

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None          # title, caption, divider, dataframe ... do nothing

    def cache_data(self, *a, **k):
        return lambda f: f

    def multiselect(self, label, options, default=None, format_func=None):
        self.filters.append(label)
        return self.picks.get(label, list(default if default is not None else options))

    def columns(self, n):
        return [Column(self) for _ in range(n)]

    def pyplot(self, fig, **k):
        self.charts += 1

    def info(self, *a, **k):
        self.messages += 1

    def warning(self, *a, **k):
        self.warnings += 1

    def stop(self):
        self.stopped = True
        raise SystemExit

    def expander(self, *a, **k):
        return Column(self)


def run_app(picks=None):
    ensure_clean_csv()
    fake = FakeStreamlit(picks)
    before = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake
    try:
        try:
            runpy.run_path(str(ROOT / "dashboard" / "app.py"), run_name="__main__")
        except SystemExit:
            pass
    finally:
        if before is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = before
    return fake


class KpiAndFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = make_raw(
            {"Transaction_ID": "T1", "Customer_ID": "C1", "Region": "North", "Order_Date": "2023-01-10", "Delivery_Date": "2023-01-14",
             "Quantity": 2, "Unit_Price": 1000.0, "Discount": 0.10, "Sales": 1800.0, "Cost": 1200.0, "Profit": 600.0, "Returned": "No"},
            {"Transaction_ID": "T2", "Customer_ID": "C1", "Region": "South", "Order_Date": "2024-02-05", "Delivery_Date": "2024-02-11",
             "Quantity": 1, "Unit_Price": 2000.0, "Discount": 0.00, "Sales": 2000.0, "Cost": 1500.0, "Profit": 500.0, "Returned": "Yes"},
            {"Transaction_ID": "T3", "Customer_ID": "C2", "Region": "North", "Order_Date": "2024-02-20", "Delivery_Date": "2024-02-22",
             "Quantity": 4, "Unit_Price": 500.0, "Discount": 0.50, "Sales": 1000.0, "Cost": 700.0, "Profit": 300.0, "Returned": "No"})
        cls.small = clean(raw)

    def test_kpis_on_three_known_orders(self):
        """Sales 4800, profit 1400, margin 29.17%, average order 1600, 3 orders, one returned."""
        k = compute_kpis(self.small)
        self.assertAlmostEqual(k["total_sales"], 4800.0)
        self.assertAlmostEqual(k["total_profit"], 1400.0)
        self.assertAlmostEqual(k["profit_margin"], 1400 / 4800 * 100)
        self.assertAlmostEqual(k["avg_order_value"], 1600.0)
        self.assertEqual(k["orders"], 3)
        self.assertAlmostEqual(k["return_rate"], 100 / 3)

    def test_an_empty_selection_gives_zeros(self):
        """If no order matches, the KPIs are zero and nothing divides by zero."""
        k = compute_kpis(filter_data(self.small, regions=["East"]))
        self.assertEqual((k["total_sales"], k["profit_margin"], k["avg_order_value"], k["return_rate"]), (0.0, 0.0, 0.0, 0.0))

    def test_filters_combine_and_empty_means_everything(self):
        """Filters work together (AND). A filter left empty keeps all rows."""
        self.assertEqual(len(filter_data(self.small)), 3)
        self.assertEqual(len(filter_data(self.small, regions=["North"])), 2)
        self.assertEqual(len(filter_data(self.small, regions=["North"], years=[2024])), 1)
        self.assertEqual(len(filter_data(self.small, months=[2], years=[2024])), 2)

    def test_every_filter_narrows_the_real_data(self):
        """Each of the six filters removes some rows when one value is picked."""
        df = clean_data()
        picks = {"years": [2024], "months": [1], "regions": ["East"], "categories": ["Furniture"],
                 "segments": ["Corporate"], "delivery_modes": ["Same-Day"]}
        for name, value in picks.items():
            with self.subTest(filter=name):
                part = filter_data(df, **{name: value})
                self.assertTrue(0 < len(part) < len(df))


class DashboardPageTests(unittest.TestCase):
    def test_page_shows_six_kpis(self):
        """The page shows six KPIs, including the four the brief asks for."""
        page = run_app()
        self.assertEqual(len(page.metrics), 6)
        for label in ["Total Sales", "Total Profit", "Profit Margin", "Average Order Value"]:
            self.assertIn(label, page.metrics)

    def test_page_has_six_filters(self):
        """The sidebar offers six filters; the brief asks for at least three."""
        self.assertEqual(run_app().filters, ["Year", "Month", "Region", "Product category", "Customer segment", "Delivery mode"])

    def test_kpis_match_the_data(self):
        """With no filters, the numbers on the page are the real totals."""
        page = run_app()
        k = compute_kpis(clean_data())
        self.assertEqual(page.metrics["Total Sales"], f"\u20b9{k['total_sales'] / 1e6:,.2f} M")
        self.assertEqual(page.metrics["Profit Margin"], f"{k['profit_margin']:.1f}%")
        self.assertEqual(page.metrics["Orders"], "7,000")

    def test_all_ten_charts_are_drawn(self):
        """Ten charts are drawn and none of them fell back to the error message."""
        page = run_app()
        self.assertEqual((page.charts, page.messages), (10, 0))

    def test_choosing_a_region_changes_the_numbers(self):
        """Picking only the East changes total sales and the order count, and the page still draws all charts."""
        full, east = run_app(), run_app({"Region": ["East"]})
        self.assertNotEqual(full.metrics["Total Sales"], east.metrics["Total Sales"])
        self.assertEqual(east.metrics["Orders"], f"{(clean_data().Region == 'East').sum():,}")
        self.assertEqual(east.charts, 10)

    def test_kpis_say_how_they_compare_with_all_data(self):
        """Each KPI has a small comparison line with the full data."""
        page = run_app({"Region": ["East"]})
        self.assertTrue(all(page.deltas[label] for label in page.metrics))

    def test_empty_selection_shows_a_warning(self):
        """If no order matches the filters, the page shows one warning, stops, and draws no charts."""
        df = clean_data()
        keys = ["Order_Year", "Order_Month", "Region", "Product_Category", "Customer_Segment", "Delivery_Mode"]
        seen = set(map(tuple, df[keys].astype(object).to_numpy()))
        empty = next(c for c in itertools.product(*[sorted(df[k].unique()) for k in keys]) if c not in seen)
        picks = dict(zip(["Year", "Month", "Region", "Product category", "Customer segment", "Delivery mode"], [[v] for v in empty]))
        page = run_app(picks)
        self.assertTrue(page.stopped)
        self.assertEqual((page.warnings, page.charts, len(page.metrics)), (1, 0, 0))

    def test_a_tiny_selection_does_not_crash(self):
        """One region, one category, one month and one year still gives a page without an exception."""
        page = run_app({"Region": ["East"], "Product category": ["Furniture"], "Month": [3], "Year": [2024]})
        self.assertEqual(len(page.metrics), 6)
        self.assertEqual(page.charts + page.messages, 10)


if __name__ == "__main__":
    unittest.main()

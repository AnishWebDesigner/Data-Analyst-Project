"""Tests for the charts and their captions."""
import re
import tempfile
import unittest
from pathlib import Path

import matplotlib.pyplot as plt

import config
from helpers import clean_data
from src.captions import build_captions
from src.metrics import filter_data
from src.visualizations import CHAPTERS, CHARTS, CHART_FUNCTIONS, CHART_TYPES, chart_sales_by_category, chart_sales_by_region, save_all_charts

REQUIRED_TYPES = {"Line chart", "Bar chart", "Histogram", "Box plot", "Scatter plot", "Donut chart", "Heatmap"}


def same_colour(patch_colour, hex_colour):
    from matplotlib.colors import to_hex
    return to_hex(patch_colour).lower() == hex_colour.lower()


class ChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = clean_data()

    def tearDown(self):
        plt.close("all")

    def test_there_are_thirteen_charts(self):
        """The project has 13 charts, which is more than the 10 the brief asks for."""
        self.assertEqual(len(CHARTS), 13)

    def test_all_seven_required_chart_types_are_there(self):
        """Line, bar, histogram, box, scatter, donut and heatmap are all used."""
        self.assertTrue(REQUIRED_TYPES.issubset(set(CHART_TYPES.values())))

    def test_every_chart_has_a_descriptive_title(self):
        """Titles are sentences that say something, not just a column name."""
        for key, fn in CHART_FUNCTIONS.items():
            with self.subTest(chart=key):
                title = fn(self.df).axes[0].get_title(loc="left") or fn(self.df).axes[0].get_title()
                self.assertGreater(len(title.split()), 4)

    def test_axes_have_labels(self):
        """Every chart except the donut has a label on both axes."""
        for key, fn in CHART_FUNCTIONS.items():
            if CHART_TYPES[key] == "Donut chart":
                continue
            with self.subTest(chart=key):
                ax = fn(self.df).axes[0]
                self.assertTrue(ax.get_xlabel().strip() and ax.get_ylabel().strip())

    def test_charts_with_more_than_one_series_have_a_legend(self):
        """The line chart, both scatter plots and the two histograms show a legend."""
        for key in ["01_monthly_sales_line", "04_age_histogram", "05_income_histogram", "08_sales_vs_profit_scatter",
                    "09_discount_vs_profit_scatter"]:
            with self.subTest(chart=key):
                self.assertIsNotNone(CHART_FUNCTIONS[key](self.df).axes[0].get_legend())

    def test_nothing_is_three_dimensional(self):
        """No chart uses 3D axes."""
        for key, fn in CHART_FUNCTIONS.items():
            with self.subTest(chart=key):
                self.assertFalse(any(getattr(a, "name", "") == "3d" for a in fn(self.df).axes))

    def test_the_weakest_region_is_the_only_red_bar(self):
        """In the region chart exactly one bar is coral, and it is the region with the lowest sales."""
        ax = chart_sales_by_region(self.df).axes[0]
        coral = [i for i, p in enumerate(ax.patches) if same_colour(p.get_facecolor(), config.CORAL)]
        labels = [t.get_text() for t in ax.get_xticklabels()]
        self.assertEqual(len(coral), 1)
        self.assertEqual(labels[coral[0]], self.df.groupby("Region", observed=True).Sales.sum().idxmin())

    def test_two_leading_categories_are_teal_and_the_rest_grey(self):
        """In the category chart two bars are teal and three are grey."""
        ax = chart_sales_by_category(self.df).axes[0]
        teal = sum(same_colour(p.get_facecolor(), config.TEAL) for p in ax.patches)
        grey = sum(same_colour(p.get_facecolor(), config.GREY) for p in ax.patches)
        self.assertEqual((teal, grey), (2, 3))

    def test_charts_still_draw_after_filtering(self):
        """With one region and one year selected every chart still draws."""
        part = filter_data(self.df, years=[2024], regions=["East"])
        self.assertGreater(len(part), 100)
        for key, fn in CHART_FUNCTIONS.items():
            with self.subTest(chart=key):
                self.assertIsNotNone(fn(part))

    def test_a_very_small_selection_does_not_crash_the_returns_and_delivery_charts(self):
        """One category, one region and one month still leaves enough rows for these two charts."""
        part = filter_data(self.df, regions=["East"], categories=["Furniture"], years=[2024], months=[3])
        self.assertGreater(len(part), 0)
        for key in ["12_returns_by_satisfaction_bar", "13_delivery_time_box"]:
            self.assertIsNotNone(CHART_FUNCTIONS[key](part))

    def test_png_files_are_saved(self):
        """save_all_charts writes 13 non-empty PNG files."""
        with tempfile.TemporaryDirectory() as folder:
            paths = save_all_charts(self.df, folder)
            self.assertEqual(len(paths), 13)
            self.assertTrue(all(Path(p).stat().st_size > 5000 for p in paths))

    def test_chapters_follow_the_story_order(self):
        """The charts are ordered by chapter: trend, regions and products, customers, drivers, heatmap, returns and delivery."""
        chapters = [c for *_, c in CHARTS]
        self.assertEqual(chapters, sorted(chapters))
        self.assertEqual(CHARTS[0][2], "Line chart")
        self.assertEqual(set(chapters), set(CHAPTERS))


class CaptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = clean_data()
        cls.captions = build_captions(cls.df)

    def test_every_chart_has_a_caption(self):
        """There is one caption for each of the 13 charts."""
        self.assertEqual(set(self.captions), set(CHART_FUNCTIONS))

    def test_captions_are_two_or_three_sentences(self):
        """The brief asks for 2 to 3 sentences under every chart."""
        for key, text in self.captions.items():
            with self.subTest(chart=key):
                sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\u20b9])", text.strip())
                self.assertIn(len(sentences), (2, 3))

    def test_captions_have_no_empty_numbers(self):
        """No caption contains 'nan' or 'inf'."""
        for key, text in self.captions.items():
            with self.subTest(chart=key):
                self.assertNotRegex(text.lower(), r"\bnan\b|\binf\b")

    def test_region_caption_names_the_right_regions(self):
        """The region caption names the region with the highest sales and the one with the lowest."""
        sales = self.df.groupby("Region", observed=True).Sales.sum()
        text = self.captions["02_sales_by_region_bar"]
        self.assertIn(sales.idxmax(), text)
        self.assertIn(sales.idxmin(), text)
        self.assertIn(f"{sales.max() / 1e6:,.1f}M", text)

    def test_returns_caption_matches_the_data(self):
        """The returns caption quotes the real return rate of low-satisfaction orders."""
        known = self.df[self.df.Satisfaction_Level != "Not Recorded"]
        low = known[known.Satisfaction_Level == "Low"].Is_Returned.mean() * 100
        self.assertIn(f"{low:.1f}%", self.captions["12_returns_by_satisfaction_bar"])

    def test_delivery_caption_matches_the_data(self):
        """The delivery caption quotes the real average days for Same-Day orders."""
        avg = self.df.dropna(subset=["Delivery_Days"]).groupby("Delivery_Mode", observed=True).Delivery_Days.mean()["Same-Day"]
        self.assertIn(f"{avg:.1f} days", self.captions["13_delivery_time_box"])


if __name__ == "__main__":
    unittest.main()

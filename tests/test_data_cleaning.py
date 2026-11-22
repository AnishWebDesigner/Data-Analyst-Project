"""Tests for src/data_cleaning.py: does the cleaning do what I say it does?"""
import unittest

import numpy as np
import pandas as pd

from helpers import clean_data, make_raw, raw_data
from src.data_cleaning import audit, check, clean, drop_duplicates, implied_discount, parse_mixed_dates, clean_gender, clean_region


class DateTests(unittest.TestCase):
    def test_iso_date(self):
        """2024-07-22 is read as 22 July 2024."""
        self.assertEqual(parse_mixed_dates(pd.Series(["2024-07-22"])).iloc[0], pd.Timestamp("2024-07-22"))

    def test_day_first_with_slashes(self):
        """22/07/2024 is read day first."""
        self.assertEqual(parse_mixed_dates(pd.Series(["22/07/2024"])).iloc[0], pd.Timestamp("2024-07-22"))

    def test_month_first_with_dashes(self):
        """07-22-2024 is read month first."""
        self.assertEqual(parse_mixed_dates(pd.Series(["07-22-2024"])).iloc[0], pd.Timestamp("2024-07-22"))

    def test_month_name_date(self):
        """22-Jul-2024 is read correctly."""
        self.assertEqual(parse_mixed_dates(pd.Series(["22-Jul-2024"])).iloc[0], pd.Timestamp("2024-07-22"))

    def test_unclear_dash_date_is_month_first(self):
        """05-03-2024 could be two dates; the file's pattern says month first, so it is 3 May."""
        self.assertEqual(parse_mixed_dates(pd.Series(["05-03-2024"])).iloc[0], pd.Timestamp("2024-05-03"))

    def test_missing_date_stays_missing(self):
        """An empty date stays empty and is not filled with anything."""
        self.assertTrue(pd.isna(parse_mixed_dates(pd.Series([np.nan])).iloc[0]))


class LabelTests(unittest.TestCase):
    def test_gender_spellings(self):
        """All eight spellings end up as Male or Female."""
        raw = pd.Series(["Male", "MALE", "male", "M", "Female", "FEMALE", "female", "F"])
        self.assertEqual(clean_gender(raw).tolist(), ["Male"] * 4 + ["Female"] * 4)

    def test_region_spellings(self):
        """Short forms such as Sth and Nort are mapped to the right region."""
        raw = pd.Series(["north", "NORTH", "Nort", "Sth", "south", "east", "WEST", "West"])
        self.assertEqual(clean_region(raw).tolist(), ["North"] * 3 + ["South"] * 2 + ["East", "West", "West"])

    def test_unknown_region_raises_an_error(self):
        """A region name I do not know stops the cleaning instead of being dropped quietly."""
        with self.assertRaises(ValueError):
            clean(make_raw({"Region": "Atlantis"}))


class RuleTests(unittest.TestCase):
    def test_raw_data_is_not_changed(self):
        """Cleaning works on a copy, so the raw frame is the same afterwards."""
        raw = make_raw({"Region": "north", "Gender": "M"})
        before = raw.copy()
        clean(raw)
        pd.testing.assert_frame_equal(raw, before)

    def test_duplicate_keeps_the_fuller_copy(self):
        """When a transaction appears twice, the copy with fewer empty cells is kept."""
        out = drop_duplicates(make_raw({"Age": np.nan}, {}))
        self.assertEqual(len(out), 1)
        self.assertEqual(out.Age.iloc[0], 35.0)

    def test_discount_is_worked_out_from_sales(self):
        """Quantity 3, price 1000 and sales 2400 means the discount must have been 0.20."""
        raw = make_raw({"Quantity": 3, "Unit_Price": 1000.0, "Sales": 2400.0, "Discount": np.nan, "Cost": 1600.0, "Profit": 800.0})
        self.assertAlmostEqual(implied_discount(raw).iloc[0], 0.20)
        self.assertAlmostEqual(clean(raw).Discount.iloc[0], 0.20)

    def test_impossible_discount_is_replaced(self):
        """A discount of 1.5 is impossible, so it is replaced by the value the sale implies."""
        raw = make_raw({"Discount": 1.5})
        self.assertAlmostEqual(clean(raw).Discount.iloc[0], 0.10)

    def test_impossible_age_comes_from_the_same_customer(self):
        """An age of 999 is replaced by the age on the same customer's other order."""
        raw = make_raw({"Transaction_ID": "T1", "Age": 999.0}, {"Transaction_ID": "T2", "Age": 41.0})
        self.assertEqual(clean(raw).Age.tolist(), [41, 41])

    def test_income_typo_is_fixed(self):
        """An income twelve times the customer's usual one is treated as a typing error."""
        raw = make_raw({"Transaction_ID": "T1", "Income": 600000.0}, {"Transaction_ID": "T2", "Income": 50000.0},
                       {"Transaction_ID": "T3", "Income": 50000.0})
        self.assertEqual(clean(raw).Income.tolist(), [50000.0] * 3)

    def test_delivery_before_order_is_removed(self):
        """A delivery date before the order date is impossible, so the date is emptied."""
        out = clean(make_raw({"Order_Date": "2024-03-10", "Delivery_Date": "2024-03-07"}))
        self.assertTrue(pd.isna(out.Delivery_Date.iloc[0]))
        self.assertTrue(pd.isna(out.Delivery_Days.iloc[0]))

    def test_missing_rating_is_not_invented(self):
        """A missing customer rating stays missing."""
        self.assertTrue(pd.isna(clean(make_raw({"Customer_Rating": np.nan})).Customer_Rating.iloc[0]))

    def test_missing_satisfaction_gets_its_own_label(self):
        """A missing satisfaction level becomes 'Not Recorded'."""
        out = clean(make_raw({"Satisfaction_Level": np.nan}))
        self.assertEqual(str(out.Satisfaction_Level.iloc[0]), "Not Recorded")


class WholeFileTests(unittest.TestCase):
    def test_numbers_found_in_the_raw_file(self):
        """The audit finds 84 repeated IDs, 8 gender labels, 12 region labels and 6 impossible ages."""
        a = audit(raw_data())
        self.assertEqual((a["raw_rows"], a["duplicate_ids"], a["gender_labels"], a["region_labels"], a["impossible_ages"]),
                         (7084, 84, 8, 12, 6))

    def test_seven_thousand_unique_orders_remain(self):
        """After cleaning there are 7,000 rows and every Transaction_ID is different."""
        df = clean_data()
        self.assertEqual(len(df), 7000)
        self.assertTrue(df.Transaction_ID.is_unique)

    def test_every_rule_passes(self):
        """All nine rules in check() hold for the cleaned data."""
        results = check(clean_data())
        self.assertEqual(len(results), 9)
        self.assertEqual([r for r, ok in results.items() if not ok], [])

    def test_every_order_date_was_understood(self):
        """No Order_Date is left empty, so all four date styles were parsed, and they cover 2023 and 2024."""
        df = clean_data()
        self.assertEqual(int(df.Order_Date.isna().sum()), 0)
        self.assertEqual(sorted(df.Order_Year.unique()), [2023, 2024])

    def test_delivery_days_are_never_negative(self):
        """Delivery_Days is empty or zero and above, never negative."""
        self.assertTrue((clean_data().Delivery_Days.dropna() >= 0).all())

    def test_four_regions_and_two_genders(self):
        """Region has exactly 4 values and Gender exactly 2."""
        df = clean_data()
        self.assertEqual(sorted(df.Region.unique()), ["East", "North", "South", "West"])
        self.assertEqual(sorted(df.Gender.unique()), ["Female", "Male"])


if __name__ == "__main__":
    unittest.main()

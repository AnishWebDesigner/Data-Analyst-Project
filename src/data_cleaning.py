"""Minimum cleaning needed so that the charts are not distorted by bad data.

I kept the same rule for every problem in the file:
  1. if the right value can be worked out from other columns, work it out;
  2. if it cannot, use a sensible estimate and mark the row;
  3. if any guess would be made up (a customer's rating, a delivery date), leave it empty.
"""
import numpy as np
import pandas as pd

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y"]
REGION_MAP = {"nor": "North", "sou": "South", "sth": "South", "eas": "East", "wes": "West"}
CATEGORY_COLUMNS = ["Gender", "Region", "State", "City", "Customer_Segment", "Product_Category", "Product",
                    "Payment_Method", "Delivery_Mode", "Returned"]


def load_raw(path):
    return pd.read_csv(path)


def parse_mixed_dates(series):
    """Turn a column holding four different date styles into real dates.

    2024-07-22 (ISO), 22/07/2024 (day first), 07-22-2024 (month first) and 22-Jul-2024.
    The slash dates are day-first because their first number goes up to 31 while the
    second never passes 12. The dash dates are the other way round, so they are month-first.
    """
    text = series.astype("string").str.strip()
    result = pd.Series(pd.NaT, index=text.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        todo = result.isna() & text.notna()
        result.loc[todo] = pd.to_datetime(text[todo], format=fmt, errors="coerce")
    return result


def clean_gender(series):
    return series.str.strip().str.upper().str[0].map({"M": "Male", "F": "Female"})


def clean_region(series):
    return series.str.strip().str.lower().str[:3].map(REGION_MAP)


def drop_duplicates(df):
    """One row per Transaction_ID. If a transaction appears twice, keep the more complete copy."""
    out = df.copy()
    out["_empty_cells"] = out.isna().sum(axis=1)
    out = (out.sort_values(["Transaction_ID", "_empty_cells"]).drop_duplicates("Transaction_ID")
              .sort_index().drop(columns="_empty_cells").reset_index(drop=True))
    return out


def implied_discount(df):
    """Discount worked out from the sale: 1 - Sales / (Quantity x Unit_Price)."""
    return (1 - df.Sales / (df.Quantity * df.Unit_Price)).round(2)


def audit(raw):
    """Count the problems in the raw file (used in the report and the README)."""
    iso = r"\d{4}-\d{2}-\d{2}"
    od, dd = raw.Order_Date.astype(str), raw.Delivery_Date.astype(str)
    cust_min = raw.groupby("Customer_ID").Income.transform("min")
    return {
        "raw_rows": len(raw),
        "duplicate_ids": int(raw.Transaction_ID.duplicated().sum()),
        "exact_duplicates": int(raw.duplicated().sum()),
        "rows_with_odd_dates": int(((~od.str.fullmatch(iso)) | (raw.Delivery_Date.notna() & ~dd.str.fullmatch(iso))).sum()),
        "gender_labels": int(raw.Gender.nunique()),
        "region_labels": int(raw.Region.nunique()),
        "bad_gender_rows": int((~raw.Gender.isin(["Male", "Female"])).sum()),
        "bad_region_rows": int((~raw.Region.isin(["North", "South", "East", "West"])).sum()),
        "impossible_ages": int(((raw.Age < 18) | (raw.Age > 100)).sum()),
        "missing_age": int(raw.Age.isna().sum()),
        "missing_discount": int(raw.Discount.isna().sum()),
        "impossible_discounts": int(((raw.Discount < 0) | (raw.Discount > 0.5)).sum()),
        "income_spikes": int((raw.Income > 5 * cust_min).sum()),
        "missing_income": int(raw.Income.isna().sum()),
        "missing_rating": int(raw.Customer_Rating.isna().sum()),
        "missing_delivery_date": int(raw.Delivery_Date.isna().sum()),
    }


def clean(raw):
    """Return the cleaned data frame (raw is not touched)."""
    df = raw.copy()

    df["Order_Date"] = parse_mixed_dates(df["Order_Date"])
    df["Delivery_Date"] = parse_mixed_dates(df["Delivery_Date"])

    df["Gender"] = clean_gender(df.Gender)
    df["Region"] = clean_region(df.Region)
    if df.Gender.isna().any() or df.Region.isna().any():
        raise ValueError("found a Gender or Region label I do not know how to map")

    # duplicates are removed after the dates are fixed, because some copies only
    # differ in how the date was typed
    df = drop_duplicates(df)

    # age: impossible values become empty, then come back from the same customer's other orders
    df.loc[(df.Age < 18) | (df.Age > 100), "Age"] = np.nan
    df["Age"] = df.Age.fillna(df.groupby("Customer_ID").Age.transform("median"))
    df["Age"] = df.Age.fillna(df.drop_duplicates("Customer_ID").Age.median()).round().astype(int)

    # income: a customer's income does not change between orders, so a value more than
    # five times their own lowest income is a typing error
    spike = df.Income > 5 * df.groupby("Customer_ID").Income.transform("min")
    df.loc[spike, "Income"] = np.nan
    df["Income"] = df.Income.fillna(df.groupby("Customer_ID").Income.transform("median"))
    df["Income"] = df.Income.fillna(df.drop_duplicates("Customer_ID").Income.median())

    # discount: Sales already contains the discount, so it can be worked out exactly
    wrong = df.Discount.isna() | (df.Discount < 0) | (df.Discount > 0.5)
    df.loc[wrong, "Discount"] = implied_discount(df)[wrong]

    # a delivery cannot happen before the order
    df.loc[df.Delivery_Date < df.Order_Date, "Delivery_Date"] = pd.NaT

    # ratings are not guessed, but a missing satisfaction level gets its own label
    df["Satisfaction_Level"] = pd.Categorical(df.Satisfaction_Level.fillna("Not Recorded"),
                                              ["Low", "Medium", "High", "Not Recorded"], ordered=True)
    for col in CATEGORY_COLUMNS:
        df[col] = df[col].astype("category")

    # columns the charts need
    df["Order_Year"] = df.Order_Date.dt.year
    df["Order_Month"] = df.Order_Date.dt.month
    df["Year_Month"] = df.Order_Date.dt.to_period("M").astype(str)
    df["Delivery_Days"] = (df.Delivery_Date - df.Order_Date).dt.days
    df["Profit_Margin"] = df.Profit / df.Sales * 100
    df["Is_Returned"] = (df.Returned == "Yes").astype(int)
    return df


def check(df):
    """Rules the cleaned data has to follow. Every value in the result should be True."""
    return {
        "one row per Transaction_ID": bool(df.Transaction_ID.is_unique),
        "no empty Age, Income or Discount": bool(df[["Age", "Income", "Discount"]].notna().all().all()),
        "Age between 18 and 100": bool(df.Age.between(18, 100).all()),
        "Discount between 0 and 0.5": bool(df.Discount.between(0, 0.5).all()),
        "Sales = Quantity x Unit_Price x (1 - Discount)": bool(((df.Quantity * df.Unit_Price * (1 - df.Discount) - df.Sales).abs() < 0.01).all()),
        "Profit = Sales - Cost": bool(((df.Sales - df.Cost - df.Profit).abs() < 0.011).all()),
        "no delivery before the order": bool((df.Delivery_Date.isna() | (df.Delivery_Date >= df.Order_Date)).all()),
        "2 genders and 4 regions": bool(df.Gender.nunique() == 2 and df.Region.nunique() == 4),
        "largest income is realistic": bool(df.Income.max() < 500_000),
    }


def prepare(path=None):
    """Load the raw file, clean it and return (clean_df, audit_numbers)."""
    from config import RAW_CSV
    raw = load_raw(path or RAW_CSV)
    return clean(raw), audit(raw)

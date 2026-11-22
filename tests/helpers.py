"""Small helpers shared by the test files."""
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import pandas as pd

import config
from src.data_cleaning import clean, load_raw

_cache = {}

# one ordinary, valid order. Tests change only the columns they care about.
BASE_ROW = dict(
    Transaction_ID="TXN200001", Customer_ID="CUST10001", Order_Date="2024-03-10", Delivery_Date="2024-03-15",
    Age=35.0, Gender="Male", Income=50000.0, Region="North", State="Delhi", City="Rohini",
    Customer_Segment="Consumer", Product_Category="Electronics", Product="USB-C Hub", Quantity=2,
    Unit_Price=1000.0, Discount=0.10, Sales=1800.0, Cost=1200.0, Profit=600.0,
    Payment_Method="UPI", Delivery_Mode="Standard", Customer_Rating=4.0, Satisfaction_Level="High", Returned="No",
)


def make_raw(*changes):
    """A small raw data frame. Every dict in `changes` becomes one row (BASE_ROW plus those changes)."""
    return pd.DataFrame([{**BASE_ROW, **c} for c in changes])


def raw_data():
    if "raw" not in _cache:
        _cache["raw"] = load_raw(config.RAW_CSV)
    return _cache["raw"]


def clean_data():
    """The cleaned data for the whole file (done once, then reused)."""
    if "clean" not in _cache:
        _cache["clean"] = clean(raw_data())
    return _cache["clean"]


def ensure_clean_csv():
    """The dashboard reads data/retail_customer_sales_cleaned.csv. Make sure it exists."""
    if not config.CLEAN_CSV.exists():
        clean_data().to_csv(config.CLEAN_CSV, index=False, date_format="%Y-%m-%d")

# Data Visualization: Turning Retail Sales Data into a Visual Story

**Data Analyst Training Program: Mini Project 2 (Data Visualization)**

| | |
|---|---|
| **Student name** | Anish Kumar |
| **Roll number** | 2026M01410002 |
| **Repository** | https://github.com/AnishWebDesigner/Data-Analyst-Project |

---

## 1. Problem statement

The sales and marketing team of a retail company wants to see what is happening in the business without reading a spreadsheet of seven thousand rows. This project takes about 7,000 retail orders from 2023 and 2024 (four regions of India) and turns them into:

1. **13 charts** of seven different types. Every chart has a title that says what it found, labelled axes, a legend where needed, one colour palette and a 2 to 3 sentence business caption.
2. **A compiled PDF report** that tells the story in order: the trend, where the money is made, who the customers are, what drives profit, and finally returns and delivery.
3. **A Streamlit dashboard** (bonus) with 6 KPIs and 6 filters.

The project also has an SRS (with a section on logistics: delivery time and returns), a project report, a synopsis, a code snapshot and 63 automated tests.

## 2. Project structure

```
Data-Analyst-Project/
├── config.py                  # name, roll number, GitHub link, paths, colour palette
├── run_all.py                 # one command: clean data, draw charts, build both PDFs, run tests
├── requirements.txt
├── data/
│   ├── retail_customer_sales_dataset.csv     # raw dataset, exactly as provided
│   └── retail_customer_sales_cleaned.csv     # produced by the cleaning step
├── src/
│   ├── data_cleaning.py       # dates, labels, duplicates, impossible values, checks
│   ├── visualizations.py      # the 13 charts
│   ├── captions.py            # captions written from the data
│   ├── metrics.py             # KPIs and filters (used by the dashboard and the tests)
│   └── build_report.py        # builds the report PDF and the code snapshot PDF
├── notebooks/
│   └── 2026M01410002_AnishKumar_Data_Visualization.ipynb
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── tests/                     # 63 automated tests
├── docs/
│   ├── 2026M01410002_Anish-Kumar_SRS.pdf / .docx
│   ├── 2026M01410002_Anish-Kumar_Project_Report.pdf / .docx
│   └── 2026M01410002_Anish-Kumar_Project_Synopsis.pdf / .docx
└── outputs/
    ├── charts/                # the 13 PNG charts
    ├── test_results.txt       # output of the latest test run
    ├── run_all_output.txt     # what run_all.py printed
    ├── dashboard_layout_preview.png
    ├── 2026M01410002_Anish-Kumar_Data_Visualization_Report.pdf
    └── 2026M01410002_Anish-Kumar_Code_Snapshot.pdf
```

## 3. How to run

Requires Python 3.10 or newer.

```bash
# 1. get the project
git clone https://github.com/AnishWebDesigner/Data-Analyst-Project.git
cd Data-Analyst-Project

# 2. (optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. install the libraries
pip install -r requirements.txt

# 4. clean the data, draw all charts, build both PDFs and run the tests
python run_all.py

# 5. open the interactive dashboard (opens http://localhost:8501)
streamlit run dashboard/app.py
```

To work in the notebook instead, run `jupyter lab` and open the file in `notebooks/`.

### Testing

The project has **63 automated tests** written with Python's built-in `unittest`, so nothing extra has to be installed. `run_all.py` runs them and saves the result in `outputs/test_results.txt`. To run them yourself:

```bash
python -m unittest discover -s tests -v
```

| Test file | Tests | What is checked |
|---|---|---|
| `tests/test_data_cleaning.py` | 24 | All four date styles are read correctly (including the unclear `05-03-2024`). Gender and Region labels are tidied and an unknown label raises an error. 7,000 unique orders remain. Impossible ages and discounts, income typos and deliveries before the order are fixed. Ratings are never invented. The raw data is not changed. All nine data rules pass. |
| `tests/test_visualizations.py` | 18 | 13 charts and all 7 required chart types. Every chart has a descriptive title and labelled axes, with a legend where there are several series. No 3D. The weakest region is the only red bar; the two leading categories are teal. Charts still draw on filtered and tiny selections. Captions are 2 to 3 sentences and quote the right numbers. |
| `tests/test_report.py` | 9 | The PDF is real and has all 13 charts and captions. The roll number is on every page. The cover shows name, roll number and GitHub link. File names start with the roll number. The code snapshot contains every source file. |
| `tests/test_dashboard.py` | 12 | The page runs without errors and shows 6 KPIs (at least 4 needed) and 6 filters (at least 3 needed). KPI values match the data. Every filter narrows the data. A region filter changes the numbers. An empty selection shows a warning instead of crashing. |

The dashboard tests run `app.py` against a stand-in for Streamlit, so they check the app's own code without a browser. Start the real app once with the command above to see the page.

## 4. Data preparation (summary)

The raw file is messy on purpose. `src/data_cleaning.py` does only as much cleaning as the charts need. The rule I followed: if the right value can be worked out from other columns, work it out; if it cannot, use a sensible estimate; if any guess would be made up, leave it empty.

| Issue found | Action |
|---|---|
| 84 repeated `Transaction_ID`s (only 61 are exact copies; 23 differ in how the date is typed) | Dates fixed first, then duplicates removed. **7,000 unique orders** remain |
| 4 date styles (`2024-07-22`, `22/07/2024`, `07-22-2024`, `22-Jul-2024`) | Parsed style by style. Slash dates are day-first, dash dates month-first (checked from the data) |
| 15 deliveries dated before the order | Delivery date emptied |
| Gender in 8 spellings, Region in 12 labels | Reduced to Male / Female and North / South / East / West |
| Impossible ages (-12, 150, 180, 999) | Replaced with the same customer's age from another order |
| 6 impossible and 71 missing discounts | Worked out from `Sales = Quantity x Unit_Price x (1 - Discount)` |
| 9 incomes about ten times too high | Replaced with the same customer's normal income |
| Missing age (142) and income (253) | Taken from the same customer's other orders where possible |
| Missing ratings (428) and delivery dates (106) | Left empty, not invented |

Nine checks run on the cleaned data (unique IDs, valid ranges, the Sales and Profit formulas, no delivery before the order and so on), and the pipeline stops if one fails.

## 5. Charts and chart-type coverage

| # | Chart | Type | Question answered |
|---|---|---|---|
| 1 | Monthly sales, 2023 to 2024 | **Line** | Are sales growing? |
| 2 | Total sales by region | **Bar** | Which region is weakest? |
| 3 | Total sales by product category | **Bar** | Which categories carry the business? |
| 4 | Age distribution | **Histogram** | How old are the customers? (skewness) |
| 5 | Income distribution | **Histogram** | What do they earn? (skewness) |
| 6 | Sales share by customer segment | **Donut** | Who buys? |
| 7 | Sales per order by category | **Box plot** | How do order sizes differ and where are the outliers? |
| 8 | Sales vs profit | **Scatter + trend line** | Does profit follow sales? |
| 9 | Discount vs profit | **Scatter + trend line** | Do discounts eat into profit? |
| 10 | Correlation matrix | **Heatmap** | Which numbers move together? |
| 11 | Average sales: category by region | **Heatmap (pivot)** | Is order size about the product or the place? |
| 12 | Return rate by satisfaction level | **Bar** | What is linked to returns? |
| 13 | Delivery days by delivery mode | **Box plot** | Are faster delivery modes really faster? |

**Design standards:** one palette everywhere (navy is the normal colour, teal marks the leading group, coral marks the point being made), descriptive titles, units on the axes, no 3D and no heavy gridlines, and the roll number in the footer of every PDF page.

## 6. Key insights

- **Flat business:** 2024 sales finished 1.5% below 2023, and the monthly ups and downs do not repeat from one year to the next.
- **North is the weakest region** (23.5% of sales, about 10% behind East). Its average order is on par with the other regions, so the gap comes mostly from fewer orders.
- **Electronics + Furniture = 83% of sales.** Grocery and Office Supplies together are under 7%.
- **Margin is steady at about 33%** (Sales and Profit have r = 0.97), so growing order value grows profit.
- **Deeper discounts do not bring bigger orders.** Orders with 40 to 50% discount earn about 45% less profit per order than orders under 10%, while units per order stay near 3.
- **Age and income do not predict spending** (correlation close to 0).
- **Returns are expensive:** returned orders are worth ₹9.04 M (about ₹90 lakh, 11.8% of sales). Low-satisfaction orders are returned 27% of the time against 4% for high-satisfaction ones.
- **Logistics:** Same-Day orders take 5.8 days on average, no faster than Standard (5.6), and only 6.9% of them arrive within a day.

## 7. Interactive dashboard (bonus)

```bash
streamlit run dashboard/app.py
```

- **KPIs (6):** Total Sales, Total Profit, Profit Margin, Average Order Value, Orders and Return Rate. Each one also says how it compares with the unfiltered data.
- **Filters (6):** Year, Month, Region, Product category, Customer segment and Delivery mode.
- **Charts (10):** monthly sales, sales by region and category, segment donut, sales box plot, sales vs profit, category by region heatmap, discount vs profit, returns by satisfaction and delivery days by mode. All of them follow the filters.
- A table of the filtered data with a CSV download, and a warning (not an error) when no order matches the filters.

A layout preview is in `outputs/dashboard_layout_preview.png`.

## 8. Documents

| File | What it is |
|---|---|
| `outputs/2026M01410002_Anish-Kumar_Data_Visualization_Report.pdf` | The compiled visual report: 13 charts with captions, a summary and recommendations |
| `outputs/2026M01410002_Anish-Kumar_Code_Snapshot.pdf` | All source code with line numbers |
| `docs/..._Project_Report.pdf` | Statement of the problem, SRS summary, Python code, test cases, conclusion |
| `docs/..._SRS.pdf` | Software Requirements Specification, including logistics requirements |
| `docs/..._Project_Synopsis.pdf` | The project synopsis |
| `outputs/test_results.txt`, `outputs/run_all_output.txt` | Execution output |

## 9. Tools and libraries

Python, pandas, NumPy, Matplotlib, Seaborn, Streamlit, ReportLab, Jupyter, unittest.

## 10. References

Official documentation for pandas, Matplotlib, Seaborn, Streamlit and ReportLab, and the Mini Project 2 brief of the Data Analyst Training Program.

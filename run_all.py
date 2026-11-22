"""One command for everything:  python run_all.py

1. cleans the data and saves data/retail_customer_sales_cleaned.csv
2. draws the 13 charts into outputs/charts/
3. builds the visual report PDF
4. builds the code snapshot PDF
5. runs the tests and saves their output to outputs/test_results.txt
"""
import subprocess
import sys
import time

import matplotlib

matplotlib.use("Agg")

import config
from src.build_report import build_code_snapshot, build_report
from src.captions import build_captions
from src.data_cleaning import audit, check, clean, load_raw
from src.visualizations import save_all_charts


def main():
    start = time.time()
    config.OUT_DIR.mkdir(exist_ok=True)

    print("Step 1 of 5: cleaning the data")
    raw = load_raw(config.RAW_CSV)
    found = audit(raw)
    df = clean(raw)
    print(f"  raw rows {found['raw_rows']:,} -> clean rows {len(df):,} "
          f"({found['duplicate_ids']} duplicates removed, {found['impossible_ages']} impossible ages, "
          f"{found['impossible_discounts'] + found['missing_discount']} discounts recomputed, {found['income_spikes']} income typos fixed)")
    results = check(df)
    for rule, ok in results.items():
        print(f"  {'ok  ' if ok else 'FAIL'} {rule}")
    if not all(results.values()):
        sys.exit("the cleaned data broke a rule, stopping")
    df.to_csv(config.CLEAN_CSV, index=False, date_format="%Y-%m-%d")

    print("Step 2 of 5: drawing the charts")
    paths = save_all_charts(df, config.CHART_DIR)
    print(f"  {len(paths)} charts saved in {config.CHART_DIR.relative_to(config.ROOT)}")

    print("Step 3 of 5: building the visual report")
    info = build_report(df, build_captions(df), config.CHART_DIR, config.REPORT_PDF)
    print(f"  {config.REPORT_PDF.name}: {info['pages']} pages, {info['figures']} charts, {info['captions']} captions")

    print("Step 4 of 5: building the code snapshot")
    info = build_code_snapshot(config.SNAPSHOT_PDF)
    print(f"  {config.SNAPSHOT_PDF.name}: {len(info['files'])} files, {info['pages']} pages")

    print("Step 5 of 5: running the tests")
    run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=config.ROOT, capture_output=True, text=True)
    config.TEST_RESULTS.write_text(run.stdout + run.stderr, encoding="utf-8")
    last = (run.stderr.strip().splitlines() or [""])[-1]
    print(f"  {last}  (full output in outputs/test_results.txt)")
    print(f"Done in {time.time() - start:.1f} seconds.")
    return run.returncode


if __name__ == "__main__":
    sys.exit(main())

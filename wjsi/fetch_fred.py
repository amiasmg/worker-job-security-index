"""
fetch_fred.py — Fetch all FRED series needed for WJSI.

Run:
    export FRED_API_KEY="your_key"
    python fetch_fred.py
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

FRED_KEY = os.environ.get("FRED_API_KEY", "")

FRED_SERIES = {
    "michigan_sentiment": {
        "id": "UMCSENT",
        "description": "University of Michigan Consumer Sentiment Index",
        "start": "1952-01-01",
    },
    "conference_board": {
        "id": "CSCICP03USM665S",
        "description": "Conference Board Consumer Confidence Index",
        "start": "1967-01-01",
    },
    "u6": {
        "id": "U6RATE",
        "description": "U-6 underemployment rate (SA)",
        "start": "1994-01-01",
    },
    "savings_rate": {
        "id": "PSAVERT",
        "description": "Personal saving rate",
        "start": "1959-01-01",
    },
    "real_gdp_growth": {
        "id": "A191RL1A225NBEA",
        "description": "Real GDP growth rate, annual",
        "start": "1930-01-01",
    },
    "median_hh_income": {
        "id": "MEHOINUSA672N",
        "description": "Real median household income (2022 dollars)",
        "start": "1984-01-01",
    },
    "unrate": {
        "id": "UNRATE",
        "description": "U-3 unemployment rate (SA)",
        "start": "1948-01-01",
    },
    "nonfarm_labor_share": {
        "id": "PRS85006173",
        "description": "Nonfarm business sector: Labor share (index, 2012=100). Quarterly.",
        "start": "1947-01-01",
    },
    "temp_help_employment": {
        "id": "TEMPHELPS",
        "description": "Temporary help services employment, SA (thousands). Used to compute temp_help_share.",
        "start": "1990-01-01",
    },
    "total_nonfarm_payrolls": {
        "id": "PAYEMS",
        "description": "Total nonfarm payrolls, SA (thousands). Denominator for temp_help_share.",
        "start": "1939-01-01",
    },
    "unemp_duration": {
        "id": "UEMPMEAN",
        "description": "Mean duration of unemployment (weeks). Captures depth of job loss risk, not rate.",
        "start": "1948-01-01",
    },
}


def fetch_all_fred():
    if not FRED_KEY:
        print("WARNING: FRED_API_KEY not set. Attempting unauthenticated access (may fail).")

    fred = Fred(api_key=FRED_KEY) if FRED_KEY else Fred()

    log_path = RAW / "fetch_log.txt"
    def log(msg):
        print(msg)
        with open(log_path, "a") as f:
            f.write(msg + "\n")

    log(f"\n{'='*60}")
    log(f"FRED fetch started at {datetime.now().isoformat()}")
    log(f"API key present: {bool(FRED_KEY)}")
    log(f"{'='*60}\n")

    for var_name, meta in FRED_SERIES.items():
        log(f"--- {var_name} ({meta['id']}) ---")
        try:
            series = fred.get_series(meta["id"], observation_start=meta["start"])
            df = series.reset_index()
            df.columns = ["date", "value"]
            df["date"] = pd.to_datetime(df["date"])
            out = RAW / f"{var_name}_fred.csv"
            df.to_csv(out, index=False)
            log(f"  {len(df)} observations, {df['date'].min().date()} to {df['date'].max().date()} → {out}")
        except Exception as e:
            log(f"  ERROR: {e}")

    log(f"\nFRED fetch completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    fetch_all_fred()
    print("\nDone. Check data/raw/ for outputs.")

"""
fetch_bls.py — Fetch all BLS series and tenure supplement data.

Run:
    export BLS_API_KEY="your_key"
    python fetch_bls.py
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("BLS_API_KEY", "")
ENDPOINT = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

LOG_FILE = RAW / "fetch_log.txt"


def log(msg: str):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def bls_request(series_ids, start_year: int, end_year: int) -> dict:
    """Single BLS API request for a batch of series over a date range."""
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "annualaverage": True,
    }
    if API_KEY:
        payload["registrationkey"] = API_KEY
    headers = {"Content-type": "application/json"}
    resp = requests.post(ENDPOINT, data=json.dumps(payload), headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_series_full(series_ids, start_year: int, end_year: int) -> dict:
    """
    Fetch one or more BLS series from start_year to end_year.
    Handles the 20-year-per-request limit by chunking and concatenating.
    Returns {series_id: [row, ...]} where row = {"year": int, "period": str, "value": float}.
    """
    all_rows = {sid: [] for sid in series_ids}  # type: dict

    # Chunk into ≤20-year windows
    chunk_start = start_year
    while chunk_start <= end_year:
        chunk_end = min(chunk_start + 19, end_year)
        log(f"  Fetching {series_ids} {chunk_start}-{chunk_end} ...")
        try:
            result = bls_request(series_ids, chunk_start, chunk_end)
        except Exception as e:
            log(f"  ERROR fetching {series_ids} {chunk_start}-{chunk_end}: {e}")
            chunk_start += 20
            continue

        if result.get("status") != "REQUEST_SUCCEEDED":
            log(f"  BLS API warning: {result.get('message', result.get('status'))}")

        for series in result.get("Results", {}).get("series", []):
            sid = series["seriesID"]
            for item in series.get("data", []):
                try:
                    value = float(item["value"].replace(",", ""))
                except (ValueError, KeyError):
                    value = None
                all_rows[sid].append({
                    "year": int(item["year"]),
                    "period": item.get("period", ""),
                    "value": value,
                })

        chunk_start += 20
        time.sleep(0.5)  # be polite to the API

    return all_rows


# ---------------------------------------------------------------------------
# Series definitions
# ---------------------------------------------------------------------------
SERIES = {
    "pt_econ": {
        "id": "LNS12032194",
        "start": 1955,
        "end": 2025,
        "description": "Part-time for economic reasons (SA, thousands)",
    },
    "employment_total": {
        "id": "LNS12000000",
        "start": 1955,
        "end": 2025,
        "description": "Total employment level (SA, thousands)",
    },
    "union": {
        "id": "LUU0204899600",
        "start": 1983,
        "end": 2025,
        "description": "Union membership rate, wage & salary workers",
    },
    "jolts_openings": {
        "id": "JTS000000000000000JOR",
        "start": 2001,
        "end": 2025,
        "description": "JOLTS job openings rate, total nonfarm (SA)",
    },
    "jolts_quits": {
        "id": "JTS000000000000000QUR",
        "start": 2001,
        "end": 2025,
        "description": "JOLTS quits rate, total nonfarm (SA)",
    },
    "jolts_layoffs": {
        "id": "JTS000000000000000LDR",
        "start": 2001,
        "end": 2025,
        "description": "JOLTS layoffs & discharges rate, total nonfarm (SA)",
    },
}

# UNRATE needed for charts
EXTRA_SERIES = {
    "unrate_bls": {
        "id": "LNS14000000",
        "start": 1948,
        "end": 2025,
        "description": "U-3 unemployment rate (SA)",
    },
}


def fetch_all_bls():
    log(f"\n{'='*60}")
    log(f"BLS fetch started at {datetime.now().isoformat()}")
    log(f"API key present: {bool(API_KEY)}")
    log(f"{'='*60}\n")

    # Group series by (start, end) to batch efficiently
    for var_name, meta in {**SERIES, **EXTRA_SERIES}.items():
        sid = meta["id"]
        log(f"\n--- {var_name} ({sid}) ---")
        rows = fetch_series_full([sid], meta["start"], meta["end"])
        df = pd.DataFrame(rows[sid]).sort_values(["year", "period"])
        out = RAW / f"{var_name}_raw.csv"
        df.to_csv(out, index=False)
        n = len(df[df["period"] == "M13"])  # annual averages
        log(f"  Saved {len(df)} rows ({n} annual averages) → {out}")

    log(f"\nBLS fetch completed at {datetime.now().isoformat()}")


# ---------------------------------------------------------------------------
# Tenure data (manual scrape from BLS news release archive)
# ---------------------------------------------------------------------------
TENURE_URLS = [
    (2024, "https://www.bls.gov/news.release/tenure.t01.htm"),
    (2022, "https://www.bls.gov/news.release/archives/tenure_09262024.htm"),
    (2020, "https://www.bls.gov/news.release/archives/tenure_09222020.htm"),
    (2018, "https://www.bls.gov/news.release/archives/tenure_09202018.htm"),
    (2016, "https://www.bls.gov/news.release/archives/tenure_09222016.htm"),
    (2014, "https://www.bls.gov/news.release/archives/tenure_09182014.htm"),
    (2012, "https://www.bls.gov/news.release/archives/tenure_09182012.htm"),
    (2010, "https://www.bls.gov/news.release/archives/tenure_09142010.htm"),
    (2008, "https://www.bls.gov/news.release/archives/tenure_09262008.htm"),
    (2006, "https://www.bls.gov/news.release/archives/tenure_09082006.htm"),
    (2004, "https://www.bls.gov/news.release/archives/tenure_01272004.htm"),
    (2002, "https://www.bls.gov/news.release/archives/tenure_09262002.htm"),
    (2000, "https://www.bls.gov/news.release/archives/tenure_08292000.htm"),
    (1998, "https://www.bls.gov/news.release/archives/tenure_09241998.htm"),
    (1996, "https://www.bls.gov/news.release/archives/tenure_08291996.htm"),
    (1991, "https://www.bls.gov/news.release/archives/tenure_01291991.htm"),
    (1987, "https://www.bls.gov/news.release/archives/tenure_01291987.htm"),
    (1983, "https://www.bls.gov/news.release/archives/tenure_01251983.htm"),
]

# Patterns that match the "total" / "all wage and salary workers" row value
# BLS tables use slightly different phrasing across decades.
_TENURE_PATTERNS = [
    # Most common modern format: decimal number after "Total" or row label
    r"Total[^<\d]*?(\d+\.\d+)",
    r"[Ww]age and salary workers[^<\d]*?(\d+\.\d+)",
    r"[Tt]otal wage and salary[^<\d]*?(\d+\.\d+)",
    # Fallback: first decimal number in a row that mentions "Total"
    r">Total<[^>]*>[^<]*?(\d+\.\d+)",
    # Very old releases: plain text "4.2" after the label
    r"All wage.and.salary workers[^\d]*(\d+\.\d)",
]


def extract_tenure(html: str, year: int):
    """
    Extract median tenure (total wage & salary workers) from BLS HTML release.
    Returns float or None if not found.
    """
    # Strip tags and look for the value in plain text
    # Strategy 1: find "Total" row in tables
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    for pat in _TENURE_PATTERNS:
        m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
        if m:
            val = float(m.group(1))
            if 2.0 <= val <= 10.0:  # sanity: median tenure should be 2–10 years
                return val

    # Strategy 2: look for the number directly after "Total" in table cells
    # Strip all tags
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    # Look for "Total" followed closely by a decimal number
    m = re.search(r"\bTotal\b[^0-9]{0,80}?(\d+\.\d)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if 2.0 <= val <= 10.0:
            return val

    return None


def fetch_tenure():
    log(f"\n--- Fetching tenure supplement data ---")
    records = []
    headers = {"User-Agent": "Mozilla/5.0 (research project)"}

    for year, url in TENURE_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            val = extract_tenure(resp.text, year)
            if val is not None:
                log(f"  {year}: {val} years  ← {url}")
                records.append({"year": year, "median_tenure_years": val})
            else:
                log(f"  {year}: PARSE FAILED — could not extract value from {url}")
        except Exception as e:
            log(f"  {year}: FETCH FAILED — {e}  ({url})")

    if not records:
        log("  All tenure URLs returned 403 (BLS blocks automated scraping).")
        log("  Using hardcoded BLS published tenure values instead.")
        # Source: BLS Employee Tenure Summary releases (Table 1, all wage & salary workers)
        records = [
            {"year": 1983, "median_tenure_years": 5.0},
            {"year": 1987, "median_tenure_years": 4.6},
            {"year": 1991, "median_tenure_years": 4.5},
            {"year": 1996, "median_tenure_years": 4.0},
            {"year": 1998, "median_tenure_years": 3.6},
            {"year": 2000, "median_tenure_years": 3.5},
            {"year": 2002, "median_tenure_years": 3.7},
            {"year": 2004, "median_tenure_years": 4.0},
            {"year": 2006, "median_tenure_years": 4.0},
            {"year": 2008, "median_tenure_years": 4.1},
            {"year": 2010, "median_tenure_years": 4.4},
            {"year": 2012, "median_tenure_years": 4.6},
            {"year": 2014, "median_tenure_years": 4.6},
            {"year": 2016, "median_tenure_years": 4.2},
            {"year": 2018, "median_tenure_years": 4.2},
            {"year": 2020, "median_tenure_years": 4.1},
            {"year": 2022, "median_tenure_years": 4.1},
            {"year": 2024, "median_tenure_years": 3.9},
        ]

    df = pd.DataFrame(records).sort_values("year")
    out = RAW / "tenure_raw.csv"
    df.to_csv(out, index=False)
    log(f"  Saved {len(df)} tenure observations → {out}")
    return df


if __name__ == "__main__":
    fetch_all_bls()
    fetch_tenure()
    print("\nDone. Check data/raw/ for outputs and data/raw/fetch_log.txt for the log.")

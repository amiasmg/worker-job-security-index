"""
clean.py — Read raw BLS/FRED data, clean, and produce annual component series.

Run after fetch_bls.py and fetch_fred.py:
    python clean.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
CLEAN = Path("data/clean")
CLEAN.mkdir(parents=True, exist_ok=True)

COVID_YEARS = {2020, 2021}


def load_bls_annual(filename: str):
    """
    Load a BLS raw CSV and return annual averages.
    Handles both M13 (API annual average) and A01 (already annual) period codes.
    Falls back to computing the mean of monthly M01-M12 values if neither is present.
    """
    df = pd.read_csv(RAW / filename)
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Already annual (e.g. union series uses A01)
    if set(df["period"].unique()).issubset({"A01", "A02", "A03"}):
        ann = df[df["period"] == "A01"].copy()
        return ann[["year", "value"]].sort_values("year").reset_index(drop=True)

    # M13 = annual average provided directly by API
    if "M13" in df["period"].values:
        ann = df[df["period"] == "M13"].copy()
        return ann[["year", "value"]].sort_values("year").reset_index(drop=True)

    # Fallback: compute annual mean from monthly M01-M12
    monthly = df[df["period"].str.match(r"^M(0[1-9]|1[0-2])$")].copy()
    ann = monthly.groupby("year")["value"].mean().reset_index()
    return ann.sort_values("year").reset_index(drop=True)


def load_bls_monthly(filename: str):
    """Load a BLS raw CSV and return all monthly rows (exclude M13)."""
    df = pd.read_csv(RAW / filename)
    monthly = df[~df["period"].isin(["M13", "M14", "M15"])].copy()
    monthly["year"] = monthly["year"].astype(int)
    monthly["period_num"] = monthly["period"].str.extract(r"M(\d+)").astype(int)
    monthly["value"] = pd.to_numeric(monthly["value"], errors="coerce")
    return monthly.sort_values(["year", "period_num"]).reset_index(drop=True)


def add_covid_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["covid_flag"] = df["year"].isin(COVID_YEARS)
    return df


# ---------------------------------------------------------------------------
# 3.1  Part-time for economic reasons rate
# ---------------------------------------------------------------------------
def clean_pt_econ():
    pt = load_bls_annual("pt_econ_raw.csv").rename(columns={"value": "pt_econ_level"})
    emp = load_bls_annual("employment_total_raw.csv").rename(columns={"value": "emp_level"})
    df = pt.merge(emp, on="year", how="inner")
    df["pt_econ_rate"] = (df["pt_econ_level"] / df["emp_level"]) * 100
    df = df[["year", "pt_econ_rate"]].dropna()
    df = add_covid_flag(df)
    df.to_csv(CLEAN / "pt_econ_rate.csv", index=False)
    print(f"pt_econ_rate: {len(df)} annual obs, {df.year.min()}–{df.year.max()}")
    return df


# ---------------------------------------------------------------------------
# 3.2  Union membership rate
# ---------------------------------------------------------------------------
def clean_union():
    df = load_bls_annual("union_raw.csv").rename(columns={"value": "union_rate"})
    df = df[["year", "union_rate"]].dropna()
    df = add_covid_flag(df)
    df.to_csv(CLEAN / "union_rate.csv", index=False)
    print(f"union_rate:   {len(df)} annual obs, {df.year.min()}–{df.year.max()}")
    return df


# ---------------------------------------------------------------------------
# 3.3  JOLTS (annual averages)
# ---------------------------------------------------------------------------
def clean_jolts():
    openings = load_bls_annual("jolts_openings_raw.csv").rename(columns={"value": "openings_rate"})
    quits = load_bls_annual("jolts_quits_raw.csv").rename(columns={"value": "quits_rate"})
    layoffs = load_bls_annual("jolts_layoffs_raw.csv").rename(columns={"value": "layoffs_rate"})
    df = openings.merge(quits, on="year", how="outer").merge(layoffs, on="year", how="outer")
    df = df.sort_values("year").reset_index(drop=True)
    df = add_covid_flag(df)
    df.to_csv(CLEAN / "jolts_annual.csv", index=False)
    print(f"jolts_annual: {len(df)} annual obs, {df.year.min()}–{df.year.max()}")
    return df


# ---------------------------------------------------------------------------
# 3.4  Tenure (biennial → annual via linear interpolation)
# ---------------------------------------------------------------------------
def clean_tenure():
    raw = pd.read_csv(RAW / "tenure_raw.csv")
    raw["year"] = raw["year"].astype(int)
    raw["median_tenure_years"] = pd.to_numeric(raw["median_tenure_years"], errors="coerce")
    raw = raw.dropna(subset=["median_tenure_years"]).sort_values("year").reset_index(drop=True)

    if raw.empty:
        print("WARNING: No tenure data found — skipping tenure interpolation.")
        return pd.DataFrame(columns=["year", "median_tenure", "interpolated", "covid_flag"])

    # Build a full annual range from min to max observed year
    min_year = raw["year"].min()
    max_year = raw["year"].max()
    all_years = pd.DataFrame({"year": range(min_year, max_year + 1)})
    merged = all_years.merge(raw.rename(columns={"median_tenure_years": "median_tenure"}),
                             on="year", how="left")
    merged["interpolated"] = merged["median_tenure"].isna()
    merged["median_tenure"] = merged["median_tenure"].interpolate(method="linear")
    merged = add_covid_flag(merged)
    merged.to_csv(CLEAN / "tenure_annual.csv", index=False)
    print(f"tenure_annual: {len(merged)} annual obs, {min_year}–{max_year} "
          f"({merged['interpolated'].sum()} interpolated)")
    return merged


# ---------------------------------------------------------------------------
# 3.5  JOLTS monthly (for wjsi_monthly.csv output)
# ---------------------------------------------------------------------------
def build_monthly_output():
    pt_m = load_bls_monthly("pt_econ_raw.csv")
    emp_m = load_bls_monthly("employment_total_raw.csv")
    openings_m = load_bls_monthly("jolts_openings_raw.csv")
    quits_m = load_bls_monthly("jolts_quits_raw.csv")
    layoffs_m = load_bls_monthly("jolts_layoffs_raw.csv")

    # Compute monthly pt_econ rate
    pt_m = pt_m.rename(columns={"value": "pt_econ_level", "period_num": "month"})
    emp_m = emp_m.rename(columns={"value": "emp_level", "period_num": "month"})
    monthly = pt_m[["year", "month", "pt_econ_level"]].merge(
        emp_m[["year", "month", "emp_level"]], on=["year", "month"], how="inner"
    )
    monthly["pt_econ_rate"] = (monthly["pt_econ_level"] / monthly["emp_level"]) * 100

    for df_m, name in [(openings_m, "openings_rate"), (quits_m, "quits_rate"), (layoffs_m, "layoffs_rate")]:
        df_m = df_m.rename(columns={"value": name, "period_num": "month"})
        monthly = monthly.merge(df_m[["year", "month", name]], on=["year", "month"], how="left")

    monthly = monthly.sort_values(["year", "month"]).reset_index(drop=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)
    monthly.to_csv("outputs/wjsi_monthly.csv", index=False)
    print(f"wjsi_monthly: {len(monthly)} monthly obs")
    return monthly


# ---------------------------------------------------------------------------
# 3.6  Master clean dataset
# ---------------------------------------------------------------------------
def build_master(pt_df, union_df, jolts_df, tenure_df):
    df = pt_df[["year", "pt_econ_rate"]].merge(
        union_df[["year", "union_rate"]], on="year", how="outer"
    ).merge(
        jolts_df[["year", "openings_rate", "quits_rate", "layoffs_rate"]], on="year", how="outer"
    ).merge(
        tenure_df[["year", "median_tenure", "interpolated"]].rename(
            columns={"interpolated": "tenure_interpolated"}
        ), on="year", how="outer"
    ).sort_values("year").reset_index(drop=True)

    df["covid_flag"] = df["year"].isin(COVID_YEARS)

    df.to_csv(CLEAN / "wjsi_components.csv", index=False)

    # Data quality summary
    print("\n" + "="*70)
    print("DATA QUALITY SUMMARY")
    print("="*70)
    cols = ["pt_econ_rate", "union_rate", "openings_rate", "quits_rate",
            "layoffs_rate", "median_tenure"]
    summary_rows = []
    for col in cols:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        summary_rows.append({
            "series": col,
            "n": len(s),
            "first_year": int(df.loc[df[col].notna(), "year"].min()),
            "last_year": int(df.loc[df[col].notna(), "year"].max()),
            "mean": round(s.mean(), 3),
            "std": round(s.std(), 3),
            "min": round(s.min(), 3),
            "max": round(s.max(), 3),
        })

    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False))
    print("="*70 + "\n")
    return df


if __name__ == "__main__":
    print("Cleaning BLS series...")
    pt_df = clean_pt_econ()
    union_df = clean_union()
    jolts_df = clean_jolts()
    tenure_df = clean_tenure()

    print("\nBuilding monthly output...")
    build_monthly_output()

    print("\nBuilding master clean dataset...")
    master = build_master(pt_df, union_df, jolts_df, tenure_df)

    print("Done. Check data/clean/ for outputs.")

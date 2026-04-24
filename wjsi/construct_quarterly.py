"""
construct_quarterly.py — Build the WJSI Quarterly Index.

Components (6 total — same conceptual set as annual index):
  1. openings_rate   JOLTS job openings rate, monthly → quarterly avg      [inverted]
  2. quits_rate      JOLTS quits rate, monthly → quarterly avg
  3. layoffs_rate    JOLTS layoffs rate, monthly → quarterly avg            [inverted]
  4. labor_share     Nonfarm business labor share (PRS85006173), quarterly (native)
  5. union_rate      Union membership rate — annual, linearly interpolated to quarterly
                     (anchored at Q2 of each survey year)
  6. median_tenure   Median years of tenure — biennial (odd years), linearly interpolated
                     to quarterly (anchored at Q1 of each survey year)

Note on interpolation: union and tenure are slow-moving structural series.
Linear interpolation tracks their trend without inventing cyclical variation.
Interpolated quarters are flagged in the output CSV.

pt_econ_rate excluded: high structural overlap with unemployment (r ≈ 0.81 with U-6);
adds no independent signal.

JOLTS weight: 3/6 = 50%, consistent with annual index.

Run after clean.py and construct.py:
    python construct_quarterly.py

Output:
    outputs/wjsi_quarterly.csv
    outputs/charts/wjsi_quarterly_history.png
    outputs/charts/wjsi_quarterly_vs_annual.png
    outputs/charts/wjsi_quarterly_components.png
    outputs/charts/wjsi_quarterly_sentiment_lead.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RAW    = Path("data/raw")
CLEAN  = Path("data/clean")
OUT    = Path("outputs")
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

# NBER recession quarters: (start_year, start_q, end_year, end_q)
RECESSION_QUARTERS = [
    (2001, 1, 2001, 3),   # Mar 2001 – Nov 2001
    (2007, 4, 2009, 2),   # Dec 2007 – Jun 2009
    (2020, 1, 2020, 2),   # Feb 2020 – Apr 2020
]

BASE_YEAR = 2005  # consistent with annual index

COMPONENTS_Q = [
    "openings_z", "quits_z", "layoffs_z", "labor_share_z", "union_z", "tenure_z",
]

COVID_QUARTERS = {(y, q) for y in (2020, 2021) for q in range(1, 5)}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ydec(year, q):
    """Year + quarter → decimal year for plotting."""
    return year + (q - 1) / 4


def shade_recessions(ax):
    for sy, sq, ey, eq in RECESSION_QUARTERS:
        ax.axvspan(ydec(sy, sq), ydec(ey, eq) + 0.25, alpha=0.15, color="grey", zorder=0)


def _all_quarters(min_year: int, max_year: int) -> pd.DataFrame:
    """Build a complete (year, quarter) grid."""
    return pd.DataFrame(
        [{"year": y, "quarter": q}
         for y in range(min_year, max_year + 1)
         for q in range(1, 5)]
    )


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def bls_monthly_to_quarterly(filename: str, value_col: str) -> pd.DataFrame:
    """Load BLS monthly raw CSV → quarterly average (year, quarter, value_col)."""
    df = pd.read_csv(RAW / filename)
    df["year"]  = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    monthly = df[df["period"].str.match(r"^M(0[1-9]|1[0-2])$")].copy()
    monthly["month"]   = monthly["period"].str.extract(r"M(\d+)").astype(int)
    monthly["quarter"] = ((monthly["month"] - 1) // 3) + 1
    qtr = (monthly.groupby(["year", "quarter"])["value"]
                  .mean()
                  .reset_index()
                  .rename(columns={"value": value_col}))
    return qtr.sort_values(["year", "quarter"]).reset_index(drop=True)


def fred_to_quarterly(filename: str, value_col: str) -> pd.DataFrame:
    """Load FRED CSV (monthly or quarterly) → quarterly average (year, quarter, value_col)."""
    p = RAW / filename
    if not p.exists():
        print(f"WARNING: {filename} not found — skipping {value_col}.")
        return pd.DataFrame(columns=["year", "quarter", value_col])
    df = pd.read_csv(p)
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"]  = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    qtr = (df.groupby(["year", "quarter"])["value"]
             .mean()
             .reset_index()
             .rename(columns={"value": value_col}))
    return qtr.sort_values(["year", "quarter"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Interpolated slow-moving series
# ---------------------------------------------------------------------------

def union_rate_quarterly() -> pd.DataFrame:
    """
    Annual union membership rate (BLS CPS) → quarterly via linear interpolation.

    Each annual observation is anchored at Q2 of its survey year (calendar midpoint).
    All other quarters are filled by linear interpolation between anchors.
    Quarters outside the observed range are held flat (ffill/bfill).
    """
    ann = pd.read_csv(CLEAN / "union_rate.csv")[["year", "union_rate"]].dropna()
    ann = ann.sort_values("year").reset_index(drop=True)

    min_year = int(ann["year"].min())
    max_year = int(ann["year"].max())
    grid = _all_quarters(min_year, max_year)

    # Anchor each annual value at Q2
    anchors = ann.copy()
    anchors["quarter"] = 2

    merged = grid.merge(anchors, on=["year", "quarter"], how="left")
    merged["union_interpolated"] = merged["union_rate"].isna()
    merged["union_rate"] = merged["union_rate"].interpolate(method="linear")
    merged["union_rate"] = merged["union_rate"].ffill().bfill()

    return merged[["year", "quarter", "union_rate", "union_interpolated"]]


def tenure_quarterly() -> pd.DataFrame:
    """
    Biennial median tenure (BLS CPS, odd years) → quarterly via linear interpolation.

    Each biennial observation is anchored at Q1 of its survey year.
    All other quarters are filled by linear interpolation between anchors.
    Quarters outside the observed range are held flat.
    """
    raw = pd.read_csv(RAW / "tenure_raw.csv")
    raw["year"] = raw["year"].astype(int)
    raw["median_tenure_years"] = pd.to_numeric(raw["median_tenure_years"], errors="coerce")
    raw = (raw.dropna(subset=["median_tenure_years"])
              .sort_values("year")
              .reset_index(drop=True)
              .rename(columns={"median_tenure_years": "median_tenure"}))

    if raw.empty:
        print("WARNING: tenure_raw.csv empty — skipping median tenure.")
        return pd.DataFrame(columns=["year", "quarter", "median_tenure", "tenure_interpolated"])

    min_year = int(raw["year"].min())
    max_year = int(raw["year"].max())
    grid = _all_quarters(min_year, max_year)

    # Anchor each biennial value at Q1
    anchors = raw[["year", "median_tenure"]].copy()
    anchors["quarter"] = 1

    merged = grid.merge(anchors, on=["year", "quarter"], how="left")
    merged["tenure_interpolated"] = merged["median_tenure"].isna()
    merged["median_tenure"] = merged["median_tenure"].interpolate(method="linear")
    merged["median_tenure"] = merged["median_tenure"].ffill().bfill()

    return merged[["year", "quarter", "median_tenure", "tenure_interpolated"]]


# ---------------------------------------------------------------------------
# Component loading
# ---------------------------------------------------------------------------

def load_components() -> pd.DataFrame:
    """Load and merge all quarterly components."""

    # JOLTS — monthly BLS → quarterly
    openings = bls_monthly_to_quarterly("jolts_openings_raw.csv", "openings_rate")
    quits    = bls_monthly_to_quarterly("jolts_quits_raw.csv",    "quits_rate")
    layoffs  = bls_monthly_to_quarterly("jolts_layoffs_raw.csv",  "layoffs_rate")

    # Labor share — quarterly native FRED (PRS85006173, 1947-present)
    ls = fred_to_quarterly("nonfarm_labor_share_fred.csv", "labor_share")

    # Slow-moving structural series — linearly interpolated to quarterly
    union  = union_rate_quarterly()
    tenure = tenure_quarterly()

    # Merge everything on (year, quarter)
    df = (openings
          .merge(quits,   on=["year", "quarter"], how="outer")
          .merge(layoffs,  on=["year", "quarter"], how="outer")
          .merge(ls,       on=["year", "quarter"], how="outer")
          .merge(union,    on=["year", "quarter"], how="outer")
          .merge(tenure,   on=["year", "quarter"], how="outer")
          .sort_values(["year", "quarter"])
          .reset_index(drop=True))

    df["ydec"]       = df.apply(lambda r: ydec(r["year"], r["quarter"]), axis=1)
    df["covid_flag"] = df.apply(lambda r: (r["year"], r["quarter"]) in COVID_QUARTERS, axis=1)
    return df


# ---------------------------------------------------------------------------
# Normalisation and direction alignment
# ---------------------------------------------------------------------------

def zscore(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mapping = {
        "openings_rate": "openings_z",
        "quits_rate":    "quits_z",
        "layoffs_rate":  "layoffs_z",
        "labor_share":   "labor_share_z",
        "union_rate":    "union_z",
        "median_tenure": "tenure_z",
    }
    for raw_col, z_col in mapping.items():
        if raw_col not in df.columns:
            continue
        col = df[raw_col].dropna()
        if len(col) < 2 or col.std() == 0:
            continue
        df[z_col] = (df[raw_col] - col.mean()) / col.std()
    return df


def align_direction(df: pd.DataFrame) -> pd.DataFrame:
    """Flip series so higher z-score always means more job security."""
    df = df.copy()
    # More layoffs = less secure
    if "layoffs_z" in df.columns:
        df["layoffs_z"] *= -1
    # Higher openings = ambiguous-negative (consistent with annual index convention)
    if "openings_z" in df.columns:
        df["openings_z"] *= -1
    # union_z, tenure_z, quits_z, labor_share_z: positive direction already correct
    return df


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------

def build_index(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict to JOLTS era (2001+), compute composite, index to base year."""
    full = df[df["year"] >= 2001].copy()
    full = full.dropna(subset=["openings_z", "quits_z", "layoffs_z"]).reset_index(drop=True)

    # Equal-weighted average of available components each quarter
    full["composite"] = full[COMPONENTS_Q].mean(axis=1)

    # Shift so minimum = 1.0 (prevents division-by-near-zero when indexing)
    comp_min = full["composite"].min()
    full["composite_shifted"] = full["composite"] + (-comp_min + 1.0)

    # Base: average of BASE_YEAR quarters
    base_rows = full[full["year"] == BASE_YEAR]
    if base_rows.empty:
        raise ValueError(f"Base year {BASE_YEAR} not in quarterly data.")
    base_val = base_rows["composite_shifted"].mean()

    full["wjsi_q"] = (full["composite_shifted"] / base_val) * 100

    # 4-quarter centred moving average for smoothed display
    full = full.sort_values(["year", "quarter"]).reset_index(drop=True)
    full["wjsi_q_ma4"] = full["wjsi_q"].rolling(4, min_periods=2, center=True).mean()

    # Print table
    print(f"\nBase year: {BASE_YEAR} (average of 4 quarters = 100)")
    print(f"Components ({len(COMPONENTS_Q)}): {', '.join(COMPONENTS_Q)}")
    print(f"Quarterly obs: {len(full)}  "
          f"({int(full['year'].min())} Q{int(full['quarter'].iloc[0])} – "
          f"{int(full['year'].max())} Q{int(full['quarter'].iloc[-1])})")

    print(f"\n{'Year':>6} {'Q':>3} {'WJSI-Q':>8} {'4Q MA':>8}")
    print("-" * 30)
    for _, r in full.iterrows():
        flag = " *" if r["covid_flag"] else ""
        print(f"{int(r.year):>6} {int(r.quarter):>3} {r.wjsi_q:>8.1f} {r.wjsi_q_ma4:>8.1f}{flag}")

    return full


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_outputs(df: pd.DataFrame):
    raw_cols = ["openings_rate", "quits_rate", "layoffs_rate",
                "labor_share", "union_rate", "median_tenure",
                "union_interpolated", "tenure_interpolated"]
    cols = (["year", "quarter", "ydec", "wjsi_q", "wjsi_q_ma4", "composite"]
            + COMPONENTS_Q
            + [c for c in raw_cols if c in df.columns]
            + ["covid_flag"])
    df[[c for c in cols if c in df.columns]].to_csv(OUT / "wjsi_quarterly.csv", index=False)
    print(f"\nSaved: outputs/wjsi_quarterly.csv  ({len(df)} rows)")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def chart_quarterly_history(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(13, 5))
    shade_recessions(ax)

    ax.plot(df["ydec"], df["wjsi_q"],
            color="#1f4e79", lw=0.8, alpha=0.35, label="Quarterly")
    ax.plot(df["ydec"], df["wjsi_q_ma4"],
            color="#1f4e79", lw=2.2, label="4-quarter moving average")
    ax.axhline(100, color="black", lw=0.8, ls="--", alpha=0.5,
               label=f"Base ({BASE_YEAR} = 100)")

    events = {
        (2001, 3): ("9/11 +\nDot-com", "down"),
        (2009, 1): ("GFC\ntrough", "down"),
        (2020, 2): ("COVID\nshock", "down"),
        (2021, 4): ("Great\nResignation", "up"),
    }
    for (yr, q), (lbl, direction) in events.items():
        row = df[(df["year"] == yr) & (df["quarter"] == q)]
        if row.empty:
            continue
        x = row["ydec"].values[0]
        y = row["wjsi_q"].values[0]
        offset = 9 if direction == "up" else -11
        ax.annotate(lbl, xy=(x, y), xytext=(x, y + offset),
                    fontsize=7.5, ha="center",
                    va="bottom" if direction == "up" else "top",
                    arrowprops=dict(arrowstyle="-", color="grey", lw=0.8))

    ax.set_title(
        f"Worker Job Security Index — Quarterly, 2001–Present  (Base {BASE_YEAR} = 100)",
        fontsize=12, fontweight="bold")
    ax.set_xlabel("Quarter")
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_quarterly_history.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart: wjsi_quarterly_history.png")


def chart_quarterly_vs_annual(df_q: pd.DataFrame):
    """Overlay quarterly (4Q MA) against the annual 6-component index."""
    annual_path = OUT / "wjsi_annual.csv"
    if not annual_path.exists():
        print("Chart: quarterly_vs_annual skipped — run construct.py first.")
        return

    ann = pd.read_csv(annual_path)[["year", "wjsi"]]

    fig, ax = plt.subplots(figsize=(13, 5))
    shade_recessions(ax)

    ax.plot(df_q["ydec"], df_q["wjsi_q"],
            color="#1f4e79", lw=0.7, alpha=0.3)
    ax.plot(df_q["ydec"], df_q["wjsi_q_ma4"],
            color="#1f4e79", lw=2.2,
            label="Quarterly WJSI (4Q MA) — same 6 components")
    ax.step(ann["year"], ann["wjsi"],
            color="#e67e22", lw=1.8, ls="--", where="post",
            label="Annual WJSI — 6-component")

    ax.axhline(100, color="black", lw=0.7, ls=":", alpha=0.5,
               label=f"Base ({BASE_YEAR} = 100)")

    ax.text(0.01, 0.04,
            "Note: union rate and median tenure are linearly interpolated\n"
            "from annual/biennial observations to quarterly frequency.",
            transform=ax.transAxes, fontsize=7.5, color="#666666", va="bottom")

    ax.set_title(f"WJSI: Quarterly vs. Annual  (Base {BASE_YEAR} = 100)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_quarterly_vs_annual.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart: wjsi_quarterly_vs_annual.png")


def chart_quarterly_components(df: pd.DataFrame):
    labels = {
        "openings_z":    "Job openings rate (inverted)",
        "quits_z":       "Quits rate",
        "layoffs_z":     "Layoffs rate (inverted)",
        "labor_share_z": "Nonfarm business labor share (PRS85006173)",
        "union_z":       "Union membership rate (interpolated from annual)",
        "tenure_z":      "Median tenure (interpolated from biennial)",
    }
    z_cols = [c for c in COMPONENTS_Q if c in df.columns]
    n = len(z_cols)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.3 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, col in zip(axes, z_cols):
        shade_recessions(ax)
        ax.plot(df["ydec"], df[col], color="#1f4e79", lw=1.2)
        ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
        ax.set_ylabel("Z-score", fontsize=8)
        ax.set_title(labels.get(col, col), fontsize=9)

    axes[-1].set_xlabel("Quarter")
    fig.suptitle(
        "WJSI Quarterly — Component Z-scores (positive = more job security)",
        fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_quarterly_components.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart: wjsi_quarterly_components.png")


def chart_lead_lag_quarterly(df: pd.DataFrame):
    sent_path = RAW / "michigan_sentiment_fred.csv"
    if not sent_path.exists():
        print("Lead/lag chart skipped — michigan_sentiment_fred.csv not found.")
        return

    sent = pd.read_csv(sent_path)
    sent["date"]    = pd.to_datetime(sent["date"])
    sent["year"]    = sent["date"].dt.year
    sent["quarter"] = sent["date"].dt.quarter
    sent_q = (sent.groupby(["year", "quarter"])["value"]
                  .mean()
                  .reset_index()
                  .rename(columns={"value": "sentiment"}))

    merged = (df[["year", "quarter", "ydec", "wjsi_q"]]
              .merge(sent_q, on=["year", "quarter"], how="inner")
              .sort_values(["year", "quarter"])
              .reset_index(drop=True))

    print("\n--- Lead/Lag: WJSI-Q vs Michigan Consumer Sentiment (quarterly) ---")
    print(f"  {'Lag (qtrs)':>12}  {'r':>8}  {'p':>8}  Note")
    print("  " + "-" * 55)

    results = []
    for lag in range(-12, 13):
        if lag < 0:
            x = merged["wjsi_q"].iloc[:lag].values
            y = merged["sentiment"].iloc[-lag:].values
        elif lag == 0:
            x = merged["wjsi_q"].values
            y = merged["sentiment"].values
        else:
            x = merged["wjsi_q"].iloc[lag:].values
            y = merged["sentiment"].iloc[:-lag].values
        if len(x) < 12:
            continue
        r, p = stats.pearsonr(x, y)
        note = ("← WJSI leads" if lag < 0
                else ("← contemporaneous" if lag == 0 else "← sentiment leads"))
        print(f"  {lag:>12}  {r:>+8.4f}  {p:>8.4f}  {note}")
        results.append((lag, r, p))

    if not results:
        return

    best_lag, best_r, best_p = max(results, key=lambda x: x[1])
    print(f"\nBest lag: {best_lag} quarters  (r = {best_r:.4f}, p = {best_p:.4f})")
    if best_lag < 0:
        print(f"*** WJSI-Q leads consumer sentiment by {-best_lag} quarter(s) ***")
    elif best_lag > 0:
        print(f"Note: sentiment leads WJSI-Q by {best_lag} quarter(s) at quarterly frequency.")

    # Scatter at best lag
    if best_lag < 0:
        x_vals = merged["wjsi_q"].iloc[:best_lag].values
        y_vals = merged["sentiment"].iloc[-best_lag:].values
        x_yrs  = merged["ydec"].iloc[:best_lag].values
    elif best_lag == 0:
        x_vals, y_vals, x_yrs = (merged["wjsi_q"].values,
                                  merged["sentiment"].values,
                                  merged["ydec"].values)
    else:
        x_vals = merged["wjsi_q"].iloc[best_lag:].values
        y_vals = merged["sentiment"].iloc[:-best_lag].values
        x_yrs  = merged["ydec"].iloc[best_lag:].values

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(x_vals, y_vals, c=x_yrs, cmap="Blues", s=30, alpha=0.8, zorder=3)
    plt.colorbar(sc, ax=ax, label="Year")
    m, b = np.polyfit(x_vals, y_vals, 1)
    xs = np.linspace(x_vals.min(), x_vals.max(), 100)
    ax.plot(xs, m * xs + b, color="#c0392b", lw=1.5,
            label=f"r = {best_r:.3f}  (p = {best_p:.3f})")
    lag_desc = (f"WJSI leads by {-best_lag}Q" if best_lag < 0
                else ("contemporaneous" if best_lag == 0
                      else f"Sentiment leads by {best_lag}Q"))
    ax.set_title(f"WJSI-Q vs. Michigan Sentiment  [{lag_desc}]",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("WJSI-Q (t)")
    ax.set_ylabel(f"Michigan Sentiment (t + {abs(best_lag)}Q)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_quarterly_sentiment_lead.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart: wjsi_quarterly_sentiment_lead.png")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def run_checklist(df: pd.DataFrame):
    print("\n" + "=" * 55)
    print("WJSI QUARTERLY — VALIDATION CHECKLIST")
    print("=" * 55)

    def get_q(yr, q):
        row = df[(df["year"] == yr) & (df["quarter"] == q)]
        return row["wjsi_q"].values[0] if not row.empty else None

    base_val = df[df["year"] == BASE_YEAR]["wjsi_q"].mean()

    def check(label, condition, detail=""):
        marker = "[✓]" if condition else "[✗]"
        print(f"{marker} {label}")
        if not condition and detail:
            print(f"    → {detail}")

    v_2001q3 = get_q(2001, 3)
    v_2009q2 = get_q(2009, 2)
    v_2020q2 = get_q(2020, 2)
    v_2019q4 = get_q(2019, 4)
    v_latest = df["wjsi_q"].iloc[-1]

    check("2001 recession (Q3 2001) below base",
          v_2001q3 is not None and v_2001q3 < base_val,
          f"2001 Q3 = {v_2001q3:.1f}, base avg = {base_val:.1f}")
    check("GFC trough (Q2 2009) ≥ 15 pts below base",
          v_2009q2 is not None and v_2009q2 < base_val - 15,
          f"2009 Q2 = {v_2009q2:.1f}")
    check("COVID shock (Q2 2020) below base",
          v_2020q2 is not None and v_2020q2 < base_val,
          f"2020 Q2 = {v_2020q2:.1f}")
    check("Pre-COVID (Q4 2019) ≥ 85",
          v_2019q4 is not None and v_2019q4 >= 85,
          f"2019 Q4 = {v_2019q4:.1f}")
    check("Latest reading below base (structural deterioration)",
          v_latest < base_val,
          f"Latest = {v_latest:.1f}")

    print("=" * 55)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("WJSI QUARTERLY INDEX CONSTRUCTION")
    print("=" * 60)

    print("\nLoading components...")
    df = load_components()
    print(f"Raw data: {len(df)} quarter-rows, "
          f"{int(df['year'].min())} – {int(df['year'].max())}")

    print("\nNormalising (z-scores + direction alignment)...")
    df = zscore(df)
    df = align_direction(df)

    print("\nBuilding quarterly index...")
    df_q = build_index(df)

    save_outputs(df_q)

    print("\nGenerating charts...")
    chart_quarterly_history(df_q)
    chart_quarterly_vs_annual(df_q)
    chart_quarterly_components(df_q)
    chart_lead_lag_quarterly(df_q)

    run_checklist(df_q)

    print(f"\nDone.")
    print(f"  CSV:    outputs/wjsi_quarterly.csv")
    print(f"  Charts: outputs/charts/wjsi_quarterly_*.png")

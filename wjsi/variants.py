"""
variants.py — Two additional WJSI variants for methodology testing.

Variant A: Annual, 4-component (ex job openings)
    Components: union + quits + layoffs + tenure
    Motivation: removes the directionally-ambiguous openings rate; tests whether
    JOLTS still dominates (now 2/4 = 50% JOLTS vs 3/5 = 60% in headline).

Variant B: Monthly, JOLTS-only (3-component)
    Components: openings + quits + layoffs — all at monthly frequency
    Motivation: tests whether a pure JOLTS composite can act as a real-time
    labor market health indicator without annual data dependencies.
    Note: openings treated as POSITIVE here (more demand = tighter market =
    more worker leverage), which is the natural reading for a real-time gauge
    as opposed to the "turnover instability" framing in the headline annual index.

Run:  cd wjsi && python variants.py
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

CLEAN = Path("data/clean")
RAW   = Path("data/raw")
OUT   = Path("outputs")
OUT.mkdir(parents=True, exist_ok=True)

BASE_YEAR   = 2005   # same base as headline index
BASE_MONTH  = "2005-01"  # approximate base for monthly index

RECESSIONS_ANNUAL = [(2001.17, 2001.83), (2007.92, 2009.42), (2020.08, 2020.25)]

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
def zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std()

def shift_and_index(series: pd.Series, base_value: float) -> pd.Series:
    """Shift so min=1, then express relative to base_value."""
    shifted = series + (-series.min() + 1.0)
    base_shifted = base_value + (-series.min() + 1.0)
    return (shifted / base_shifted) * 100

def shade_recessions(ax, recessions=RECESSIONS_ANNUAL):
    for s, e in recessions:
        ax.axvspan(s, e, alpha=0.12, color="grey", zorder=0)

def shade_recessions_dates(ax):
    for s, e in [("2001-03-01","2001-11-01"),
                 ("2007-12-01","2009-06-01"),
                 ("2020-02-01","2020-04-01")]:
        ax.axvspan(pd.to_datetime(s), pd.to_datetime(e), alpha=0.12, color="grey", zorder=0)


# ---------------------------------------------------------------------------
# VARIANT A: Annual, 4-component (ex openings)
# ---------------------------------------------------------------------------
def build_variant_a():
    print("\n" + "="*60)
    print("VARIANT A: Annual 4-component index (ex job openings)")
    print("="*60)

    union  = pd.read_csv(CLEAN / "union_rate.csv")[["year","union_rate"]]
    jolts  = pd.read_csv(CLEAN / "jolts_annual.csv")[["year","quits_rate","layoffs_rate"]]
    tenure = pd.read_csv(CLEAN / "tenure_annual.csv")[["year","median_tenure"]]

    df = union.merge(jolts, on="year").merge(tenure, on="year", how="left")
    df = df[df["year"] >= 2001].sort_values("year").reset_index(drop=True)

    # Z-score
    df["union_z"]   =  zscore(df["union_rate"])
    df["quits_z"]   =  zscore(df["quits_rate"])
    df["layoffs_z"] = -zscore(df["layoffs_rate"])   # higher layoffs = less secure
    df["tenure_z"]  =  zscore(df["median_tenure"])

    components = ["union_z", "quits_z", "layoffs_z", "tenure_z"]
    df["composite"] = df[components].mean(axis=1)

    # Base value at BASE_YEAR
    base_mask = df["year"] == BASE_YEAR
    if not base_mask.any():
        raise ValueError(f"Base year {BASE_YEAR} not in data")
    base_val = df.loc[base_mask, "composite"].values[0]
    df["wjsi_ex_openings"] = shift_and_index(df["composite"], base_val)

    # Also load headline 5-component for comparison
    headline = pd.read_csv(OUT / "wjsi_annual.csv")[["year","wjsi"]]
    df = df.merge(headline, on="year", how="left")

    print(f"\n{'year':>6}  {'4-comp (ex open)':>18}  {'5-comp headline':>16}  {'diff':>6}")
    print("-"*52)
    for _, r in df.iterrows():
        diff = r["wjsi_ex_openings"] - r["wjsi"] if not np.isnan(r["wjsi"]) else float("nan")
        print(f"{int(r.year):>6}  {r.wjsi_ex_openings:>18.1f}  {r.wjsi:>16.1f}  {diff:>+6.1f}")

    # Save
    df[["year","wjsi_ex_openings","composite"] + components].to_csv(
        OUT / "wjsi_variant_a_ex_openings.csv", index=False
    )
    print(f"\nSaved outputs/wjsi_variant_a_ex_openings.csv")
    return df


# ---------------------------------------------------------------------------
# VARIANT B: Monthly JOLTS-only (3-component)
# ---------------------------------------------------------------------------
def parse_jolts_monthly(path: Path, value_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    month_map = {f"M{i:02d}": i for i in range(1, 13)}
    df = df[df["period"].isin(month_map)].copy()
    df["month"] = df["period"].map(month_map)
    df["date"] = pd.to_datetime(df[["year","month"]].assign(day=1))
    df = df.rename(columns={"value": value_col})[["date", value_col]]
    return df.sort_values("date").reset_index(drop=True)

def build_variant_b():
    print("\n" + "="*60)
    print("VARIANT B: Monthly JOLTS-only index (openings + quits + layoffs)")
    print("="*60)

    openings = parse_jolts_monthly(RAW / "jolts_openings_raw.csv", "openings_rate")
    quits    = parse_jolts_monthly(RAW / "jolts_quits_raw.csv",    "quits_rate")
    layoffs  = parse_jolts_monthly(RAW / "jolts_layoffs_raw.csv",  "layoffs_rate")

    df = openings.merge(quits, on="date").merge(layoffs, on="date")
    df = df.sort_values("date").reset_index(drop=True)

    # Z-score over full sample
    df["openings_z"] =  zscore(df["openings_rate"])   # positive: more openings = tighter market
    df["quits_z"]    =  zscore(df["quits_rate"])       # positive: worker confidence
    df["layoffs_z"]  = -zscore(df["layoffs_rate"])     # inverted: more layoffs = less secure

    df["composite"] = df[["openings_z","quits_z","layoffs_z"]].mean(axis=1)

    # Base: average of BASE_YEAR months
    base_rows = df[df["date"].dt.year == BASE_YEAR]
    if base_rows.empty:
        raise ValueError(f"No data for base year {BASE_YEAR}")
    base_val = base_rows["composite"].mean()
    df["jolts_mci"] = shift_and_index(df["composite"], base_val)

    # 12-month rolling average for trend line
    df["jolts_mci_ma12"] = df["jolts_mci"].rolling(12, center=True).mean()

    print(f"\nDate range: {df['date'].min().date()} → {df['date'].max().date()}  ({len(df)} months)")
    print(f"\nKey moments (monthly index, base {BASE_YEAR}=100):")
    for label, date_str in [
        ("Jan 2009 (GFC trough)",  "2009-01-01"),
        ("Apr 2020 (COVID shock)", "2020-04-01"),
        ("Nov 2021 (Great Resignation peak)", "2021-11-01"),
        ("Dec 2024", "2024-12-01"),
        ("Dec 2025 (latest full year)", "2025-12-01"),
    ]:
        row = df[df["date"] == pd.to_datetime(date_str)]
        if not row.empty:
            print(f"  {label:40s}: {row['jolts_mci'].values[0]:6.1f}")

    df.to_csv(OUT / "jolts_mci_monthly.csv", index=False)
    print(f"\nSaved outputs/jolts_mci_monthly.csv")
    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart_variant_a(df_a):
    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    # Panel 1: comparison lines
    ax = axes[0]
    shade_recessions(ax)
    ax.plot(df_a["year"], df_a["wjsi_ex_openings"],
            color="#1B4F8A", lw=2.2, marker="o", ms=4, label="4-comp ex openings (union + quits + layoffs + tenure)")
    ax.plot(df_a["year"], df_a["wjsi"],
            color="#C0392B", lw=1.6, ls="--", marker="s", ms=3.5, label="5-comp headline (includes openings)")
    ax.axhline(100, color="black", lw=0.8, ls=":", alpha=0.5, label=f"Base = {BASE_YEAR}")
    ax.set_title("Variant A: Annual Index ex Job Openings vs. Headline WJSI", fontweight="bold", fontsize=11)
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.legend(fontsize=9)
    ax.set_xlim(df_a["year"].min()-0.5, df_a["year"].max()+0.5)

    # Panel 2: difference (ex_openings minus headline)
    ax = axes[1]
    diff = df_a["wjsi_ex_openings"] - df_a["wjsi"]
    colors = ["#1A7A4A" if v >= 0 else "#C0392B" for v in diff]
    ax.bar(df_a["year"], diff, color=colors, alpha=0.75, width=0.7)
    ax.axhline(0, color="black", lw=0.8)
    shade_recessions(ax)
    ax.set_title("Difference: 4-comp (ex openings) minus 5-comp headline  (positive = openings was dragging index down)", fontsize=10)
    ax.set_ylabel("Index point difference")
    ax.set_xlabel("Year")
    ax.set_xlim(df_a["year"].min()-0.5, df_a["year"].max()+0.5)

    fig.tight_layout()
    fig.savefig(OUT / "variant_a_ex_openings.png", bbox_inches="tight")
    plt.close(fig)
    print("\nChart saved: outputs/variant_a_ex_openings.png")


def chart_variant_b(df_b):
    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    # Panel 1: monthly index + 12m MA
    ax = axes[0]
    shade_recessions_dates(ax)
    ax.plot(df_b["date"], df_b["jolts_mci"],
            color="#1B4F8A", lw=0.9, alpha=0.45, label="Monthly")
    ax.plot(df_b["date"], df_b["jolts_mci_ma12"],
            color="#1B4F8A", lw=2.2, label="12-month moving average")
    ax.axhline(100, color="black", lw=0.7, ls=":", alpha=0.5, label=f"Base = {BASE_YEAR}")

    # Annotate key moments
    for label, date_str, offset_y, va in [
        ("GFC\ntrough", "2009-01-01", -12, "top"),
        ("COVID\nshock", "2020-04-01", -12, "top"),
        ("Great\nResignation\npeak", "2021-11-01", 10, "bottom"),
    ]:
        row = df_b[df_b["date"] == pd.to_datetime(date_str)]
        if not row.empty:
            y = row["jolts_mci"].values[0]
            ax.annotate(label, xy=(row["date"].values[0], y),
                xytext=(0, offset_y), textcoords="offset points",
                ha="center", va=va, fontsize=8, color="#555555",
                arrowprops=dict(arrowstyle="->", color="#888888", lw=0.7))

    ax.set_title(f"Variant B: Monthly JOLTS-Only Composite  (openings + quits + layoffs, base {BASE_YEAR}=100)",
                 fontweight="bold", fontsize=11)
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 2: three components as z-scores
    ax = axes[1]
    shade_recessions_dates(ax)
    ax.plot(df_b["date"], df_b["openings_z"],  color="#1A7A4A", lw=1.3, label="Job openings rate (z)")
    ax.plot(df_b["date"], df_b["quits_z"],     color="#1B4F8A", lw=1.3, label="Quit rate (z)")
    ax.plot(df_b["date"], df_b["layoffs_z"],   color="#C0392B", lw=1.3, label="Layoffs rate (z, inverted)")
    ax.axhline(0, color="black", lw=0.7, ls="--", alpha=0.5)
    ax.set_title("Component Z-scores (positive = more worker-favourable)", fontsize=10)
    ax.set_ylabel("Z-score")
    ax.set_xlabel("Month")
    ax.legend(fontsize=9, loc="upper left")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.tight_layout()
    fig.savefig(OUT / "variant_b_jolts_monthly.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart saved: outputs/variant_b_jolts_monthly.png")


def chart_annual_comparison(df_a, df_b):
    """Compare headline, ex-openings, and JOLTS-MCI (annualised) on one chart."""
    # Annualise variant B
    df_b["year"] = df_b["date"].dt.year
    b_ann = df_b.groupby("year")["jolts_mci"].mean().reset_index()
    b_ann.columns = ["year", "jolts_mci_ann"]

    merged = df_a[["year","wjsi","wjsi_ex_openings"]].merge(b_ann, on="year", how="outer").sort_values("year")

    fig, ax = plt.subplots(figsize=(12, 5))
    shade_recessions(ax)

    ax.plot(merged["year"], merged["wjsi"],
            color="#C0392B", lw=1.8, ls="--", marker="s", ms=3.5, label="5-comp headline (union+openings+quits+layoffs+tenure)")
    ax.plot(merged["year"], merged["wjsi_ex_openings"],
            color="#1B4F8A", lw=2.2, marker="o", ms=4, label="4-comp ex openings (union+quits+layoffs+tenure)")
    ax.plot(merged["year"], merged["jolts_mci_ann"],
            color="#1A7A4A", lw=1.8, ls="-.", marker="^", ms=4, label="JOLTS-MCI annual avg (openings+quits+layoffs)")

    ax.axhline(100, color="black", lw=0.7, ls=":", alpha=0.5)
    ax.set_title(f"Index Comparison: Headline vs. Variant A (ex openings) vs. Variant B (JOLTS-only)\nAll indexed to {BASE_YEAR} = 100",
                 fontweight="bold", fontsize=11)
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8.5, loc="upper right")
    ax.set_xlim(merged["year"].min()-0.5, merged["year"].max()+0.5)

    fig.tight_layout()
    fig.savefig(OUT / "variant_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart saved: outputs/variant_comparison.png")


# ---------------------------------------------------------------------------
# Correlation summary
# ---------------------------------------------------------------------------
def correlation_summary(df_a, df_b):
    # Load comparators
    u3 = pd.read_csv(RAW / "unrate_fred.csv")
    u3["date"] = pd.to_datetime(u3["date"])
    u3["year"] = u3["date"].dt.year
    u3_ann = u3.groupby("year")["value"].mean().reset_index()
    u3_ann.columns = ["year","u3"]

    u6 = pd.read_csv(RAW / "u6_fred.csv")
    u6["date"] = pd.to_datetime(u6["date"])
    u6["year"] = u6["date"].dt.year
    u6_ann = u6.groupby("year")["value"].mean().reset_index()
    u6_ann.columns = ["year","u6"]

    sentiment = pd.read_csv(RAW / "michigan_sentiment_fred.csv")
    sentiment["date"] = pd.to_datetime(sentiment["date"])
    sentiment["year"] = sentiment["date"].dt.year
    sent_ann = sentiment.groupby("year")["value"].mean().reset_index()
    sent_ann.columns = ["year","sentiment"]

    df_b_ann = df_b.copy()
    df_b_ann["year"] = df_b_ann["date"].dt.year
    b_ann = df_b_ann.groupby("year")["jolts_mci"].mean().reset_index()
    b_ann.columns = ["year","jolts_mci_ann"]

    comp = df_a[["year","wjsi","wjsi_ex_openings"]].merge(b_ann, on="year", how="outer")
    comp = comp.merge(u3_ann, on="year", how="left")
    comp = comp.merge(u6_ann, on="year", how="left")
    comp = comp.merge(sent_ann, on="year", how="left")

    print("\n" + "="*60)
    print("CORRELATION SUMMARY (vs external indicators, annual)")
    print("="*60)
    print(f"\n{'Indicator':<28} {'vs U-3':>8} {'vs U-6':>8} {'vs Sent.':>10}")
    print("-"*58)
    for col, label in [
        ("wjsi",          "5-comp headline"),
        ("wjsi_ex_openings", "4-comp ex openings"),
        ("jolts_mci_ann", "JOLTS-MCI (ann)"),
    ]:
        sub = comp[["year", col, "u3", "u6", "sentiment"]].dropna()
        if sub.empty:
            continue
        r_u3   = sub[col].corr(sub["u3"])
        r_u6   = sub[col].corr(sub["u6"])
        r_sent = sub[col].corr(sub["sentiment"])
        print(f"  {label:<26} {r_u3:>+8.3f} {r_u6:>+8.3f} {r_sent:>+10.3f}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    df_a = build_variant_a()
    df_b = build_variant_b()

    print("\nGenerating charts...")
    chart_variant_a(df_a)
    chart_variant_b(df_b)
    chart_annual_comparison(df_a, df_b)
    correlation_summary(df_a, df_b)

    print("\nDone. Outputs in wjsi/outputs/")

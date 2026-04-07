"""
construct.py — Build the WJSI index and produce all validation charts.

Run after clean.py:
    python construct.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CLEAN = Path("data/clean")
RAW = Path("data/raw")
OUT = Path("outputs")
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

# NBER recession shading (year-month tuples, approximate annual boundaries for annual charts)
RECESSIONS = [
    (2001.17, 2001.83),   # Mar 2001 – Nov 2001
    (2007.92, 2009.42),   # Dec 2007 – Jun 2009
    (2020.08, 2020.25),   # Feb 2020 – Apr 2020
]

# Primary 5-component index: pt_econ excluded — it overlaps structurally with U-6
# (U-6 literally contains involuntary part-time workers as a subcomponent),
# producing r=0.81 with U-6 that drops to r=0.15 without pt_econ.
# The 5-component version is the headline WJSI. pt_econ is retained as a reference variant.
COMPONENTS_FULL = ["union_z", "openings_z", "quits_z", "layoffs_z", "tenure_z"]
COMPONENTS_WITH_PT = ["pt_econ_z", "union_z", "openings_z", "quits_z", "layoffs_z", "tenure_z"]
COMPONENTS_LEGACY = ["union_z", "tenure_z"]  # pre-JOLTS: union + tenure only

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def shade_recessions(ax, recessions=RECESSIONS, ymin=0, ymax=1):
    for start, end in recessions:
        ax.axvspan(start, end, alpha=0.15, color="grey", zorder=0)


# ---------------------------------------------------------------------------
# Load and merge all clean components
# ---------------------------------------------------------------------------
def load_components() -> pd.DataFrame:
    pt = pd.read_csv(CLEAN / "pt_econ_rate.csv")
    union = pd.read_csv(CLEAN / "union_rate.csv")
    jolts = pd.read_csv(CLEAN / "jolts_annual.csv")
    tenure = pd.read_csv(CLEAN / "tenure_annual.csv")

    df = pt[["year", "pt_econ_rate"]].merge(
        union[["year", "union_rate"]], on="year", how="outer"
    ).merge(
        jolts[["year", "openings_rate", "quits_rate", "layoffs_rate"]], on="year", how="outer"
    ).merge(
        tenure[["year", "median_tenure"]], on="year", how="outer"
    ).sort_values("year").reset_index(drop=True)

    df["covid_flag"] = df["year"].isin([2020, 2021])
    return df


# ---------------------------------------------------------------------------
# 4.1  Z-score normalization (over full available period per series)
# ---------------------------------------------------------------------------
def zscore(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mapping = {
        "pt_econ_rate": "pt_econ_z",
        "union_rate": "union_z",
        "openings_rate": "openings_z",
        "quits_rate": "quits_z",
        "layoffs_rate": "layoffs_z",
        "median_tenure": "tenure_z",
    }
    for raw_col, z_col in mapping.items():
        if raw_col in df.columns:
            col = df[raw_col]
            df[z_col] = (col - col.mean()) / col.std()
    return df


# ---------------------------------------------------------------------------
# 4.2  Directional alignment
# Higher z = more job security
# ---------------------------------------------------------------------------
def align_direction(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # More part-time involuntary = less secure → flip
    if "pt_econ_z" in df.columns:
        df["pt_econ_z"] = df["pt_econ_z"] * -1
    # More layoffs = less secure → flip
    if "layoffs_z" in df.columns:
        df["layoffs_z"] = df["layoffs_z"] * -1
    # Openings: treated as ambiguous-negative (high turnover = less stability) → flip
    # NOTE: This is tested in backtest.py with openings as positive and excluded.
    if "openings_z" in df.columns:
        df["openings_z"] = df["openings_z"] * -1
    return df


# ---------------------------------------------------------------------------
# 4.3–4.6  Build JOLTS-era full index
# ---------------------------------------------------------------------------
def build_full_index(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Returns (full_era_df, chosen_base_year)."""
    # Restrict to JOLTS era
    full = df[df["year"] >= 2001].copy()
    full = full.dropna(subset=["union_z", "openings_z", "quits_z", "layoffs_z"])

    # Primary 5-component composite (ex pt_econ)
    full["composite_equal"] = full[COMPONENTS_FULL].mean(axis=1)

    # Reference 6-component composite (with pt_econ) — saved for comparison
    full["composite_with_pt"] = full[COMPONENTS_WITH_PT].mean(axis=1)

    # Shift composite to a positive range before ratio indexing.
    # Z-score averages can be near zero at the base year, causing division blowup.
    # Shift so the series minimum = 1.0, preserving all relative movements.
    comp_min = full["composite_equal"].min()
    shift = -comp_min + 1.0
    full["composite_shifted"] = full["composite_equal"] + shift

    # 4.5 Test candidate base years
    print("\nBase-year sensitivity:")
    print(f"{'base':>6} | {'2001':>6} | {'2009':>6} | {'2019':>6} | {'2020':>6} | {'2022':>6} | {'latest':>6}")
    print("-" * 55)

    key_years = [2001, 2009, 2019, 2020, 2022, full["year"].max()]
    for base in [2003, 2004, 2005, 2006, 2007]:
        if base not in full["year"].values:
            continue
        bv = full.loc[full["year"] == base, "composite_shifted"].values[0]
        vals = []
        for yr in key_years:
            row = full.loc[full["year"] == yr, "composite_shifted"]
            vals.append(f"{(row.values[0] / bv * 100):6.1f}" if not row.empty else "  N/A")
        print(f"  {base} | {' | '.join(vals)}")

    # 4.6 Chosen base year
    # Select base year where 2009 is meaningfully below 100 and 2019 is meaningfully above 100.
    BASE_YEAR = 2005
    if BASE_YEAR not in full["year"].values:
        for fallback in [2004, 2006, 2003, 2007]:
            if fallback in full["year"].values:
                BASE_YEAR = fallback
                break

    base_val = full.loc[full["year"] == BASE_YEAR, "composite_shifted"].values[0]
    full["wjsi"] = (full["composite_shifted"] / base_val) * 100

    # Also index the 6-component (with pt_econ) variant for reference
    shift_pt = -full["composite_with_pt"].min() + 1.0
    full["composite_with_pt_s"] = full["composite_with_pt"] + shift_pt
    base_val_pt = full.loc[full["year"] == BASE_YEAR, "composite_with_pt_s"].values[0]
    full["wjsi_with_pt"] = (full["composite_with_pt_s"] / base_val_pt) * 100

    print(f"\n✓ Chosen base year: {BASE_YEAR} (primary 5-component index, ex pt_econ)")
    print(f"  Rationale: pt_econ excluded — structural overlap with U-6 (r drops 0.81→0.15 without it).")
    print(f"\n{'year':>6} {'wjsi (5-comp)':>14} {'wjsi (w/pt)':>12}")
    for _, row in full[["year", "wjsi", "wjsi_with_pt"]].iterrows():
        print(f"{int(row.year):>6} {row.wjsi:>14.1f} {row.wjsi_with_pt:>12.1f}")

    return full, BASE_YEAR


# ---------------------------------------------------------------------------
# 4.7  Legacy series 1983–2000
# ---------------------------------------------------------------------------
def build_legacy_index(df: pd.DataFrame, base_year: int) -> pd.DataFrame:
    legacy = df[df["year"] <= 2000].copy()
    legacy = legacy.dropna(subset=["union_z", "tenure_z"])

    if legacy.empty:
        print("WARNING: No legacy-era data found (years ≤ 2000). Skipping legacy series.")
        return pd.DataFrame()

    legacy["composite_legacy"] = legacy[COMPONENTS_LEGACY].mean(axis=1)

    # Apply same shift logic: shift so minimum = 1 across the combined legacy+full range
    # Use the full df to compute the shift for consistent scaling
    all_legacy_composite = df[df["year"] <= 2000].copy()
    all_legacy_composite["cl"] = all_legacy_composite[COMPONENTS_LEGACY].mean(axis=1)
    leg_min = all_legacy_composite["cl"].min()
    leg_shift = -leg_min + 1.0
    legacy["composite_shifted"] = legacy["composite_legacy"] + leg_shift

    # Base value: use the same base_year (or its z-score legacy composite) for splice coherence
    full_at_base = df[df["year"] == base_year]
    if full_at_base.empty or full_at_base[COMPONENTS_LEGACY].isna().all().all():
        legacy_base_val = legacy["composite_shifted"].mean()
        print(f"WARNING: Base year {base_year} not in legacy range; using mean as base.")
    else:
        raw_base = full_at_base[COMPONENTS_LEGACY].mean(axis=1).values[0]
        legacy_base_val = raw_base + leg_shift

    legacy["wjsi_legacy"] = (legacy["composite_shifted"] / legacy_base_val) * 100

    print(f"\nLegacy series ({legacy.year.min()}–{legacy.year.max()}):")
    print(legacy[["year", "wjsi_legacy"]].to_string(index=False))
    return legacy


# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------
def save_outputs(full_df, legacy_df, base_year):
    Path("outputs").mkdir(parents=True, exist_ok=True)

    # Annual WJSI — primary (5-component, ex pt_econ) + reference variant (with pt_econ)
    cols = ["year", "wjsi", "wjsi_with_pt", "composite_equal"] + COMPONENTS_FULL + ["covid_flag"]
    full_df[[c for c in cols if c in full_df.columns]].to_csv(OUT / "wjsi_annual.csv", index=False)
    print(f"\nSaved outputs/wjsi_annual.csv ({len(full_df)} rows)")
    print(f"  Primary index: 5-component (ex pt_econ) → 'wjsi' column")
    print(f"  Reference:     6-component (with pt_econ) → 'wjsi_with_pt' column")

    # Legacy
    if not legacy_df.empty:
        leg_cols = ["year", "wjsi_legacy", "composite_legacy"] + COMPONENTS_LEGACY
        legacy_df[[c for c in leg_cols if c in legacy_df.columns]].to_csv(
            OUT / "wjsi_legacy_1983.csv", index=False
        )
        print(f"Saved outputs/wjsi_legacy_1983.csv ({len(legacy_df)} rows)")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart1_full_history(full_df, base_year):
    fig, ax = plt.subplots(figsize=(12, 5))
    shade_recessions(ax)

    years = full_df["year"]
    wjsi = full_df["wjsi"]
    ax.plot(years, wjsi, color="#1f4e79", linewidth=2.2, label="WJSI")
    ax.axhline(100, color="black", linewidth=0.8, linestyle="--", alpha=0.6, label=f"Base ({base_year}=100)")

    # Event annotations
    events = {
        2001: ("9/11 +\nDot-com bust", "up"),
        2009: ("Housing\ncrash", "down"),
        2020: ("COVID\nshock", "down"),
        2022: ("Post-COVID\ntightening", "up"),
    }
    for yr, (label, direction) in events.items():
        row = full_df[full_df["year"] == yr]
        if row.empty:
            continue
        y_val = row["wjsi"].values[0]
        offset = 6 if direction == "up" else -8
        ax.annotate(
            label, xy=(yr, y_val), xytext=(yr, y_val + offset),
            fontsize=7.5, ha="center", va="bottom" if direction == "up" else "top",
            arrowprops=dict(arrowstyle="-", color="grey", lw=0.8),
        )

    ax.set_title(f"Worker Job Security Index, 2001–Present (Base Year = {base_year} = 100)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Index (Base = 100)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_full_history.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 1: wjsi_full_history.png")


def chart2_spliced(full_df, legacy_df, base_year):
    fig, ax = plt.subplots(figsize=(12, 5))
    shade_recessions(ax)

    ax.plot(full_df["year"], full_df["wjsi"], color="#1f4e79", linewidth=2.2, label="WJSI (full, 2001–present)")

    if not legacy_df.empty:
        ax.plot(legacy_df["year"], legacy_df["wjsi_legacy"], color="#1f4e79", linewidth=2.2,
                linestyle="--", label="WJSI legacy (1983–2000, 3-component)")

    ax.axvline(2001, color="dimgrey", linewidth=0.9, linestyle=":", alpha=0.8)
    ax.text(2001.2, ax.get_ylim()[1] * 0.97, "JOLTS\ndata begins", fontsize=7.5, color="dimgrey", va="top")
    ax.axhline(100, color="black", linewidth=0.8, linestyle="--", alpha=0.5, label=f"Base ({base_year}=100)")

    ax.set_title(f"Worker Job Security Index, 1983–Present (Base Year = {base_year} = 100)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Index (Base = 100)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_spliced.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 2: wjsi_spliced.png")


def chart3_components(full_df):
    z_cols = [c for c in COMPONENTS_FULL if c in full_df.columns]
    labels = {
        "pt_econ_z": "Part-time (economic) rate (inverted)",
        "union_z": "Union membership rate",
        "openings_z": "Job openings rate (inverted)",
        "quits_z": "Quits rate",
        "layoffs_z": "Layoffs rate (inverted)",
        "tenure_z": "Median tenure",
    }
    n = len(z_cols)
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, col in zip(axes, z_cols):
        shade_recessions(ax)
        ax.plot(full_df["year"], full_df[col], color="#1f4e79", linewidth=1.5)
        ax.axhline(0, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
        ax.set_ylabel("Z-score", fontsize=8)
        ax.set_title(labels.get(col, col), fontsize=9)

    axes[-1].set_xlabel("Year")
    fig.suptitle("WJSI Component Z-scores (positive = more secure)", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS / "component_contributions.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 3: component_contributions.png")


def _load_unrate_annual() -> pd.DataFrame:
    """Load U-3 from FRED, convert to annual average."""
    for fname in ["unrate_fred.csv", "unrate_bls_raw.csv"]:
        p = RAW / fname
        if p.exists():
            df = pd.read_csv(p)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df["year"] = df["date"].dt.year
                annual = df.groupby("year")["value"].mean().reset_index()
                annual.columns = ["year", "unrate"]
                return annual
    return pd.DataFrame(columns=["year", "unrate"])


def chart4_vs_unemployment(full_df):
    unrate = _load_unrate_annual()
    merged = full_df[["year", "wjsi"]].merge(unrate, on="year", how="inner")
    if merged.empty:
        print("Chart 4: skipped (no UNRATE data)")
        return

    fig, ax1 = plt.subplots(figsize=(12, 5))
    shade_recessions(ax1)

    color_wjsi = "#1f4e79"
    color_ur = "#c0392b"

    ax1.plot(merged["year"], merged["wjsi"], color=color_wjsi, linewidth=2, label="WJSI (left)")
    ax1.set_ylabel("WJSI", color=color_wjsi)
    ax1.tick_params(axis="y", colors=color_wjsi)

    ax2 = ax1.twinx()
    ax2.plot(merged["year"], merged["unrate"], color=color_ur, linewidth=1.5, linestyle="--",
             label="Unemployment rate (right, inverted)")
    ax2.invert_yaxis()  # invert so both move in same direction
    ax2.set_ylabel("Unemployment rate (%) — inverted", color=color_ur)
    ax2.tick_params(axis="y", colors=color_ur)

    lines = [
        mpatches.Patch(color=color_wjsi, label="WJSI"),
        mpatches.Patch(color=color_ur, label="U-3 Unemployment (inverted)"),
    ]
    ax1.legend(handles=lines, fontsize=9)
    ax1.set_title("WJSI vs. U-3 Unemployment Rate", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_vs_unemployment.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 4: wjsi_vs_unemployment.png")


def chart5_vs_u6(full_df):
    u6_path = RAW / "u6_fred.csv"
    if not u6_path.exists():
        print("Chart 5: skipped (no U-6 data)")
        return
    u6 = pd.read_csv(u6_path)
    u6["date"] = pd.to_datetime(u6["date"])
    u6["year"] = u6["date"].dt.year
    u6_ann = u6.groupby("year")["value"].mean().reset_index()
    u6_ann.columns = ["year", "u6"]

    merged = full_df[["year", "wjsi"]].merge(u6_ann, on="year", how="inner")
    if merged.empty:
        print("Chart 5: skipped (no overlap)")
        return

    fig, ax1 = plt.subplots(figsize=(12, 5))
    shade_recessions(ax1)

    color_wjsi = "#1f4e79"
    color_u6 = "#8e44ad"

    ax1.plot(merged["year"], merged["wjsi"], color=color_wjsi, linewidth=2, label="WJSI (left)")
    ax1.set_ylabel("WJSI", color=color_wjsi)
    ax1.tick_params(axis="y", colors=color_wjsi)

    ax2 = ax1.twinx()
    ax2.plot(merged["year"], merged["u6"], color=color_u6, linewidth=1.5, linestyle="--",
             label="U-6 rate (right, inverted)")
    ax2.invert_yaxis()
    ax2.set_ylabel("U-6 Underemployment (%) — inverted", color=color_u6)
    ax2.tick_params(axis="y", colors=color_u6)

    lines = [
        mpatches.Patch(color=color_wjsi, label="WJSI"),
        mpatches.Patch(color=color_u6, label="U-6 Underemployment (inverted)"),
    ]
    ax1.legend(handles=lines, fontsize=9)
    ax1.set_title("WJSI vs. U-6 Underemployment Rate", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_vs_u6.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 5: wjsi_vs_u6.png")


def chart6_base_year_sensitivity(full_df):
    fig, ax = plt.subplots(figsize=(12, 5))
    shade_recessions(ax)

    colors = ["#1f4e79", "#2980b9", "#27ae60", "#e67e22", "#e74c3c"]
    for base, color in zip([2003, 2004, 2005, 2006, 2007], colors):
        if base not in full_df["year"].values:
            continue
        bv = full_df.loc[full_df["year"] == base, "composite_shifted"].values[0]
        ax.plot(full_df["year"], (full_df["composite_shifted"] / bv) * 100,
                color=color, linewidth=1.6, label=f"Base = {base}")

    ax.axhline(100, color="black", linewidth=0.7, linestyle="--", alpha=0.5)
    ax.set_title("WJSI Sensitivity to Base Year Choice (2003–2007)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Index (Base = 100)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "wjsi_base_year_sensitivity.png", bbox_inches="tight")
    plt.close(fig)
    print("Chart 6: wjsi_base_year_sensitivity.png")


# ---------------------------------------------------------------------------
# Validation checklist (called from main or externally)
# ---------------------------------------------------------------------------
def run_checklist(full_df, base_year):
    print("\n" + "="*50)
    print("WJSI VALIDATION CHECKLIST")
    print("="*50)

    def get(yr):
        row = full_df[full_df["year"] == yr]
        return row["wjsi"].values[0] if not row.empty else None

    base_val = get(base_year) or 100
    results = {}

    def check(key, condition, fail_msg=""):
        status = "PASS" if condition else "FAIL"
        results[key] = condition
        marker = "[✓]" if condition else "[✗]"
        print(f"{marker} {key}: {status}")
        if not condition and fail_msg:
            print(f"    → {fail_msg}")

    v_2001 = get(2001)
    v_2009 = get(2009)
    v_2019 = get(2019)
    v_2020 = get(2020)
    v_latest = full_df["wjsi"].iloc[-1]

    check("Index falls during 2001 recession",
          v_2001 is not None and v_2001 < base_val,
          f"2001 value {v_2001:.1f} not below base {base_val:.1f}")
    check("Index falls during 2008-2009 recession",
          v_2009 is not None and v_2009 < base_val - 5,
          f"2009 value {v_2009:.1f} not ≥5 pts below base {base_val:.1f}")
    check("Index falls during 2020 COVID shock",
          v_2020 is not None and v_2020 < base_val,
          f"2020 value {v_2020:.1f} not below base {base_val:.1f}")
    check("Index recovers after each recession",
          v_2019 is not None and v_2019 > 95,
          f"2019 value {v_2019:.1f} suggests no recovery before COVID")
    check("2024 index value < base year value (structural deterioration)",
          v_latest < base_val,
          f"Latest ({full_df['year'].iloc[-1]}): {v_latest:.1f} vs base {base_val:.1f}")

    print("\n(Correlation checks run in correlations.py)")
    print("="*50)
    return results


if __name__ == "__main__":
    print("Loading components...")
    df = load_components()

    print("Computing z-scores...")
    df = zscore(df)
    df = align_direction(df)

    print("\nBuilding full JOLTS-era index...")
    full_df, BASE_YEAR = build_full_index(df)

    print("\nBuilding legacy 1983–2000 series...")
    legacy_df = build_legacy_index(df, BASE_YEAR)

    save_outputs(full_df, legacy_df, BASE_YEAR)

    print("\nGenerating charts...")
    chart1_full_history(full_df, BASE_YEAR)
    chart2_spliced(full_df, legacy_df, BASE_YEAR)
    chart3_components(full_df)
    chart4_vs_unemployment(full_df)
    chart5_vs_u6(full_df)
    chart6_base_year_sensitivity(full_df)

    run_checklist(full_df, BASE_YEAR)

    print("\nDone. See outputs/ and outputs/charts/")

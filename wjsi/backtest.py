"""
backtest.py — Sensitivity analysis on component weights.

Run after construct.py:
    python backtest.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

OUT = Path("outputs")
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

WEIGHTING_SCHEMES = {
    "Equal weight (baseline)": {
        "pt_econ_z": 1/6, "union_z": 1/6, "openings_z": 1/6,
        "quits_z": 1/6, "layoffs_z": 1/6, "tenure_z": 1/6,
    },
    "Union-heavy": {
        "pt_econ_z": 0.15, "union_z": 0.30, "openings_z": 0.10,
        "quits_z": 0.20, "layoffs_z": 0.20, "tenure_z": 0.05,
    },
    "JOLTS-focused": {
        "pt_econ_z": 0.15, "union_z": 0.10, "openings_z": 0.20,
        "quits_z": 0.25, "layoffs_z": 0.25, "tenure_z": 0.05,
    },
    "No-openings": {
        "pt_econ_z": 0.20, "union_z": 0.20, "openings_z": 0.00,
        "quits_z": 0.25, "layoffs_z": 0.25, "tenure_z": 0.10,
    },
    "Structural-only (no JOLTS)": {
        "pt_econ_z": 0.40, "union_z": 0.40, "openings_z": 0.00,
        "quits_z": 0.00, "layoffs_z": 0.00, "tenure_z": 0.20,
    },
}

KEY_YEARS = [2001, 2005, 2009, 2019, 2020, 2022]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

RECESSIONS = [
    (2001.17, 2001.83),
    (2007.92, 2009.42),
    (2020.08, 2020.25),
]


def shade_recessions(ax):
    for start, end in RECESSIONS:
        ax.axvspan(start, end, alpha=0.15, color="grey", zorder=0)


def compute_weighted_index(df: pd.DataFrame, weights: dict, base_year: int) -> pd.Series:
    """Compute weighted composite and index it to base_year=100."""
    avail = {col: w for col, w in weights.items() if col in df.columns and w > 0}
    total_w = sum(avail.values())
    if total_w == 0:
        return pd.Series(index=df.index, dtype=float)

    composite = sum(df[col] * (w / total_w) for col, w in avail.items())

    # Shift to positive range before ratio indexing (z-score averages can be near zero)
    shift = -composite.min() + 1.0
    composite_shifted = composite + shift

    row = df[df["year"] == base_year]
    if row.empty:
        return composite_shifted
    base_val = composite_shifted[row.index[0]]
    return (composite_shifted / base_val) * 100


def run_sensitivity():
    annual_path = OUT / "wjsi_annual.csv"
    if not annual_path.exists():
        print("ERROR: outputs/wjsi_annual.csv not found. Run construct.py first.")
        return

    df = pd.read_csv(annual_path)
    df = df.sort_values("year").reset_index(drop=True)

    # Detect base year from the data (where wjsi == 100)
    base_matches = df[df["wjsi"].round(1) == 100.0]["year"]
    BASE_YEAR = int(base_matches.iloc[0]) if not base_matches.empty else 2005

    print(f"Sensitivity analysis (base year: {BASE_YEAR})\n")

    # Compute each scheme's index
    scheme_series = {}
    for name, weights in WEIGHTING_SCHEMES.items():
        scheme_series[name] = compute_weighted_index(df, weights, BASE_YEAR)

    baseline = scheme_series["Equal weight (baseline)"]

    # Summary table
    header = f"{'Scheme':<35} " + " ".join(f"{y:>6}" for y in KEY_YEARS) + f" {'latest':>6} {'r_vs_base':>10}"
    print(header)
    print("-" * len(header))

    table_lines = [header, "-" * len(header)]
    all_robust = True

    for name, series in scheme_series.items():
        vals = []
        for yr in KEY_YEARS:
            row = df[df["year"] == yr]
            if not row.empty:
                idx = row.index[0]
                vals.append(f"{series[idx]:6.1f}")
            else:
                vals.append("   N/A")

        latest_idx = df.index[-1]
        latest_val = f"{series[latest_idx]:6.1f}"

        # Pearson r vs baseline over full series
        common = baseline.notna() & series.notna()
        if common.sum() > 3:
            r, p = stats.pearsonr(baseline[common], series[common])
        else:
            r, p = float("nan"), float("nan")

        if r < 0.85:
            all_robust = False

        line = f"{name:<35} {' '.join(vals)} {latest_val} {r:10.4f}"
        print(line)
        table_lines.append(line)

    robustness_msg = (
        "\nIndex is robust to weighting choice." if all_robust
        else "\nWeighting choice is material — investigate further."
    )
    print(robustness_msg)
    table_lines.append(robustness_msg)

    # Write text output
    with open(OUT / "sensitivity_table.txt", "w") as f:
        f.write("\n".join(table_lines))
    print(f"\nSaved outputs/sensitivity_table.txt")

    # Chart
    fig, ax = plt.subplots(figsize=(12, 5))
    shade_recessions(ax)

    colors = ["#1f4e79", "#2980b9", "#27ae60", "#e67e22", "#e74c3c"]
    styles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

    for (name, series), color, style in zip(scheme_series.items(), colors, styles):
        ax.plot(df["year"], series, color=color, linewidth=1.8,
                linestyle=style, label=name)

    ax.axhline(100, color="black", linewidth=0.7, linestyle="--", alpha=0.4)
    ax.set_title("WJSI Sensitivity to Component Weighting", fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Index ({BASE_YEAR} = 100)")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(CHARTS / "sensitivity_weights.png", bbox_inches="tight")
    plt.close(fig)
    print("Saved outputs/charts/sensitivity_weights.png")


if __name__ == "__main__":
    run_sensitivity()

"""
correlations.py — Correlation analysis between WJSI and external FRED indicators.

Run after construct.py:
    python correlations.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

RAW = Path("data/raw")
OUT = Path("outputs")
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

FRED_INDICATORS = {
    "michigan_sentiment": "Michigan Consumer Sentiment",
    "conference_board": "Conference Board Consumer Confidence",
    "u6": "U-6 Underemployment Rate",
    "savings_rate": "Personal Saving Rate",
    "real_gdp_growth": "Real GDP Growth Rate",
    "median_hh_income": "Real Median Household Income",
}


def load_fred_annual(var_name: str):
    """Load a FRED CSV and convert to annual averages."""
    path = RAW / f"{var_name}_fred.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    annual = df.groupby("year")["value"].mean().reset_index()
    annual.columns = ["year", var_name]
    return annual


def interpret_r(r: float) -> str:
    abs_r = abs(r)
    if abs_r > 0.85:
        return "Strong — investigate redundancy"
    elif abs_r >= 0.60:
        return "Meaningful — not redundant"
    else:
        return "Weak — captures something different"


def run_correlations():
    # Load WJSI
    wjsi_path = OUT / "wjsi_annual.csv"
    if not wjsi_path.exists():
        print("ERROR: outputs/wjsi_annual.csv not found. Run construct.py first.")
        return

    wjsi_df = pd.read_csv(wjsi_path)[["year", "wjsi"]]

    # Load all FRED indicators
    indicator_dfs = {}
    for var_name in FRED_INDICATORS:
        df = load_fred_annual(var_name)
        if df is not None:
            indicator_dfs[var_name] = df

    if not indicator_dfs:
        print("ERROR: No FRED indicator files found in data/raw/. Run fetch_fred.py first.")
        return

    # Merge all
    merged = wjsi_df.copy()
    for var_name, df in indicator_dfs.items():
        merged = merged.merge(df, on="year", how="left")

    merged = merged.sort_values("year").reset_index(drop=True)

    output_lines = []

    def out(line=""):
        print(line)
        output_lines.append(line)

    out("=" * 75)
    out("WJSI CORRELATION ANALYSIS")
    out("=" * 75)

    # 7.2 Static correlations
    out("\n--- 7.2 Static Correlations with WJSI ---\n")
    header = f"{'Indicator':<35} {'Period':>15} {'n':>4} {'r':>8} {'p':>8}  Interpretation"
    out(header)
    out("-" * 90)

    corr_results = {}
    for var_name, label in FRED_INDICATORS.items():
        if var_name not in merged.columns:
            out(f"{label:<35} {'N/A':>15} {'–':>4} {'–':>8} {'–':>8}  No data")
            continue

        pair = merged[["year", "wjsi", var_name]].dropna()
        if len(pair) < 5:
            out(f"{label:<35} {'insufficient':>15} {'–':>4} {'–':>8} {'–':>8}  Fewer than 5 obs")
            continue

        r, p = stats.pearsonr(pair["wjsi"], pair[var_name])
        period = f"{pair['year'].min()}–{pair['year'].max()}"
        interp = interpret_r(r)
        out(f"{label:<35} {period:>15} {len(pair):>4} {r:>8.4f} {p:>8.4f}  {interp}")
        corr_results[var_name] = {"r": r, "p": p, "label": label, "n": len(pair), "period": period}

    # 7.3 Lead/lag analysis vs. Michigan Sentiment
    out("\n--- 7.3 Lead/Lag Analysis: WJSI vs. Michigan Consumer Sentiment ---\n")

    michigan_label = "michigan_sentiment"
    lead_lag_results = []

    if michigan_label in merged.columns:
        pair = merged[["year", "wjsi", michigan_label]].dropna().reset_index(drop=True)
        wjsi_s = pair["wjsi"]
        sent_s = pair[michigan_label]

        out(f"{'Lag':>5} {'r':>8} {'p':>8}  Note")
        out("-" * 40)

        for lag in range(-4, 5):
            if lag < 0:
                x = wjsi_s.iloc[:lag].values
                y = sent_s.iloc[-lag:].values
            elif lag > 0:
                x = wjsi_s.iloc[lag:].values
                y = sent_s.iloc[:-lag].values
            else:
                x = wjsi_s.values
                y = sent_s.values

            if len(x) < 5:
                continue

            r, p = stats.pearsonr(x, y)
            note = "← WJSI leads" if lag < 0 else ("← contemporaneous" if lag == 0 else "← sentiment leads")
            out(f"{lag:>5} {r:>8.4f} {p:>8.4f}  {note}")
            lead_lag_results.append({"lag": lag, "r": r, "p": p})

        if lead_lag_results:
            best = max(lead_lag_results, key=lambda d: abs(d["r"]))
            best_lag = best["lag"]
            best_r = best["r"]

            out(f"\nBest lag: {best_lag} (r = {best_r:.4f})")
            if best_lag <= -1:
                finding = f"WJSI leads consumer sentiment by {abs(best_lag)} year(s). This is the key finding — publish."
            elif best_lag == 0:
                finding = "WJSI is contemporaneous with consumer sentiment — useful but not predictive."
            else:
                finding = f"Consumer sentiment leads WJSI by {best_lag} year(s) — reconsider index design."
            out(f"\n*** {finding} ***")

            # Chart 7 — lead/lag bar chart
            lags = [d["lag"] for d in lead_lag_results]
            rs = [d["r"] for d in lead_lag_results]
            colors = ["#1f4e79" if d["lag"] == best_lag else "#7f8c8d" for d in lead_lag_results]

            fig, ax = plt.subplots(figsize=(9, 4))
            bars = ax.bar(lags, rs, color=colors, edgecolor="white", linewidth=0.5)
            ax.axhline(0, color="black", linewidth=0.6)
            ax.set_xlabel("Lag (negative = WJSI leads, positive = sentiment leads)", fontsize=9)
            ax.set_ylabel("Pearson r", fontsize=9)
            ax.set_title("Cross-correlation: WJSI vs. Michigan Consumer Sentiment\n(negative lag = WJSI leads)",
                         fontsize=11, fontweight="bold")
            ax.set_xticks(lags)
            for bar, r_val in zip(bars, rs):
                ax.text(bar.get_x() + bar.get_width() / 2, r_val + (0.01 if r_val >= 0 else -0.03),
                        f"{r_val:.2f}", ha="center", va="bottom" if r_val >= 0 else "top", fontsize=8)
            fig.tight_layout()
            fig.savefig(CHARTS / "lead_lag_michigan.png", bbox_inches="tight")
            plt.close(fig)
            print("Chart 7: lead_lag_michigan.png")
    else:
        out("Michigan Sentiment data not available — lead/lag analysis skipped.")
        finding = "Lead/lag analysis not run — no Michigan Sentiment data."
        best_lag = None
        best_r = None

    # 7.4 Correlation matrix heatmap
    available_vars = [v for v in FRED_INDICATORS if v in merged.columns]
    if available_vars:
        corr_cols = ["wjsi"] + available_vars
        corr_data = merged[corr_cols].dropna()
        if len(corr_data) > 5:
            corr_matrix = corr_data.corr()
            labels_map = {"wjsi": "WJSI", **{k: v for k, v in FRED_INDICATORS.items()}}
            corr_matrix.index = [labels_map.get(c, c) for c in corr_matrix.index]
            corr_matrix.columns = [labels_map.get(c, c) for c in corr_matrix.columns]

            fig, ax = plt.subplots(figsize=(9, 7))
            sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="RdBu_r",
                        center=0, vmin=-1, vmax=1, ax=ax,
                        annot_kws={"size": 9}, linewidths=0.5)
            ax.set_title("Correlation Matrix: WJSI and External Indicators", fontsize=11, fontweight="bold")
            plt.xticks(rotation=30, ha="right", fontsize=8)
            plt.yticks(rotation=0, fontsize=8)
            fig.tight_layout()
            fig.savefig(CHARTS / "correlation_matrix.png", bbox_inches="tight")
            plt.close(fig)
            print("Chart 8: correlation_matrix.png")

    # 7.5 Redundancy check on U-6
    u6_note = ""
    if "u6" in corr_results:
        r_u6 = abs(corr_results["u6"]["r"])
        if r_u6 > 0.90:
            u6_note = f"⚠️  WJSI correlation with U-6 = {r_u6:.3f} > 0.90 — potential redundancy. Consider dropping a JOLTS component."
        else:
            u6_note = f"WJSI correlation with U-6 = {r_u6:.3f} < 0.90 — not redundant with U-6."

    # 7.5 Overall assessment
    out("\n--- Overall Assessment ---")
    out(u6_note)

    all_pass = True
    if "u6" in corr_results and abs(corr_results["u6"]["r"]) > 0.90:
        all_pass = False
    if "michigan_sentiment" in corr_results and abs(corr_results["michigan_sentiment"]["r"]) < 0.50:
        all_pass = False

    if all_pass:
        assessment = "Proceed to white paper"
    else:
        issues = []
        if "u6" in corr_results and abs(corr_results["u6"]["r"]) > 0.90:
            issues.append("U-6 redundancy")
        if "michigan_sentiment" in corr_results and abs(corr_results["michigan_sentiment"]["r"]) < 0.50:
            issues.append("weak consumer confidence correlation")
        assessment = f"Revisit index design — {', '.join(issues)}"

    out(f"\nASSESSMENT: {assessment}")
    out("=" * 75)

    # Write summary file
    with open(OUT / "correlation_summary.txt", "w") as f:
        f.write("\n".join(output_lines))
    print(f"\nSaved outputs/correlation_summary.txt")

    # Print final validation items for checklist
    return {
        "u6_r": corr_results.get("u6", {}).get("r"),
        "michigan_r": corr_results.get("michigan_sentiment", {}).get("r"),
        "best_lead_lag": best_lag if lead_lag_results else None,
    }


if __name__ == "__main__":
    run_correlations()

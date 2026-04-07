# Worker Job Security Index (WJSI)

A composite index of US worker job security, combining six structural and labor-market components into a single annual series (2001–present), with a legacy 3-component series back to 1983.

---

## Quick Start

```bash
# 1. Install dependencies
pip install pandas numpy matplotlib seaborn scipy requests openpyxl statsmodels fredapi

# 2. Set API keys
export BLS_API_KEY="your_bls_key"    # register at https://data.bls.gov/registrationEngine/
export FRED_API_KEY="your_fred_key"  # register at https://fred.stlouisfed.org/docs/api/api_key.html

# 3. Run full pipeline
cd wjsi/
python run_all.py

# Or run steps individually:
python fetch_bls.py      # BLS API + tenure scrape
python fetch_fred.py     # FRED API
python clean.py          # clean & normalize
python construct.py      # build index + charts 1–6
python backtest.py       # sensitivity analysis + chart 7
python correlations.py   # correlation analysis + charts 8–9
```

---

## Repository Structure

```
wjsi/
├── data/
│   ├── raw/                  # Raw fetched CSVs (commit these)
│   └── clean/                # Processed annual series
├── outputs/
│   ├── charts/               # PNG chart outputs
│   ├── wjsi_annual.csv       # Primary index output
│   ├── wjsi_monthly.csv      # Underlying monthly series (not indexed)
│   ├── wjsi_legacy_1983.csv  # Pre-JOLTS 3-component series
│   ├── correlation_summary.txt
│   └── sensitivity_table.txt
├── fetch_bls.py
├── fetch_fred.py
├── clean.py
├── construct.py
├── backtest.py
├── correlations.py
├── run_all.py
└── README.md
```

---

## Index Components

| Component | Source | Period | Direction |
|---|---|---|---|
| Part-time for economic reasons rate | BLS LNS12032194 / LNS12000000 | 1955– | Inverted (more = less secure) |
| Union membership rate | BLS LUU0204899600 | 1983– | Positive (more = more secure) |
| JOLTS job openings rate | BLS JTS000000000000000JOR | 2001– | Inverted (see note) |
| JOLTS quits rate | BLS JTS000000000000000QUR | 2001– | Positive (more = more secure) |
| JOLTS layoffs rate | BLS JTS000000000000000LDR | 2001– | Inverted (more = less secure) |
| Median tenure (wage & salary workers) | BLS tenure supplement | 1983– | Positive (more = more secure) |

---

## Key Design Decisions

1. **Base year chosen**: 2005
   - Rationale: 2009 trough falls well below 100 (captures Great Recession severity); 2019 pre-COVID peak falls above 100 (captures recovery); reasonable spread for public communication.

2. **Openings rate direction**: treated as negative (inverted)
   - Rationale: high openings in this context correlate with high turnover and worker churn, not worker bargaining power. This is tested in sensitivity analysis. The no-openings weighting scheme is also provided.

3. **COVID handling**: 2020–2021 flagged (not excluded) in headline series
   - Rationale: the COVID shock is real and should appear in the index. The `covid_flag` column allows downstream analysis to exclude these years when testing structural relationships.

4. **Tenure URLs that failed**: See `data/raw/fetch_log.txt` for any parsing failures. The scraper logs each URL's outcome. Linear interpolation fills gaps between biennial observations.

5. **BLS API series IDs**: Any errors are logged in `data/raw/fetch_log.txt`. The 20-year-per-request limit is handled automatically by chunking.

---

## Outputs

### Charts

| File | Description |
|---|---|
| `wjsi_full_history.png` | Main WJSI line chart with recession shading and event labels |
| `wjsi_spliced.png` | Legacy (1983–2000, dashed) + full (2001–present, solid) series |
| `component_contributions.png` | Six-panel z-score subplot for each component |
| `wjsi_vs_unemployment.png` | Dual-axis: WJSI vs. U-3 (inverted) |
| `wjsi_vs_u6.png` | Dual-axis: WJSI vs. U-6 underemployment (inverted) |
| `wjsi_base_year_sensitivity.png` | Five candidate base years (2003–2007) |
| `sensitivity_weights.png` | Five weighting schemes on one chart |
| `lead_lag_michigan.png` | Cross-correlation at lags -4 to +4 vs. Michigan Sentiment |
| `correlation_matrix.png` | Heatmap of WJSI vs. all six external indicators |

### CSV Outputs

- `wjsi_annual.csv` — columns: `year`, `wjsi`, `composite_equal`, 6×`_z` components, `covid_flag`
- `wjsi_legacy_1983.csv` — columns: `year`, `wjsi_legacy`, `composite_legacy`, 3×`_z` components
- `wjsi_monthly.csv` — monthly pt_econ and JOLTS rates (not indexed)

---

## Success Criteria

| Test | Threshold |
|---|---|
| Falls in all three recessions | ≥5 index points below base in 2009 |
| Structural deterioration present | Latest year ≥10 pts below base |
| Not redundant with U-6 | Pearson r < 0.90 |
| Correlated with consumer confidence | Pearson r > 0.50 |
| Robust to weighting | All schemes correlate >0.85 with baseline |
| Lead/lag finding | Maximum r at lag ≤ 0 |

If all six pass → ready for LISEP partnership discussion.

---

## Data Sources

- **BLS Public Data API v2**: https://api.bls.gov/publicAPI/v2/timeseries/data/
- **BLS Tenure Supplement**: https://www.bls.gov/news.release/tenure.nr0.htm
- **FRED (St. Louis Fed)**: https://fred.stlouisfed.org/

# Worker Job Security Index (WJSI)

A composite annual index measuring **structural job security** for American workers — independent of headline unemployment statistics.

Built in collaboration with [LISEP](https://lisep.org) (Ludwig Institute for Shared Economic Prosperity).

---

## The Problem

Headline unemployment (U-3) has been at or below 4% since 2022 — a level historically associated with a strong labour market. Yet over the same period:

- The voluntary quit rate fell 25% (from 2.76% to 2.07%)
- Union membership hit a post-war low of 9.9%
- Median job tenure began declining

Workers were **employed**, but increasingly **stuck rather than secure**. The WJSI is designed to capture that distinction.

---

## Index Construction

### Components (headline, 5-component)

| Component | Source | Direction | Rationale |
|---|---|---|---|
| Union membership rate | BLS CPS | ↑ = more secure | Collective bargaining power |
| Job openings rate (JOLTS) | BLS JOLTS | ↓ = more secure | High churn signal, not stability |
| Voluntary quit rate (JOLTS) | BLS JOLTS | ↑ = more secure | Worker confidence / outside options |
| Layoffs & discharges rate (JOLTS) | BLS JOLTS | ↓ = more secure | Involuntary job loss |
| Median job tenure | BLS ETS | ↑ = more secure | Structural employment stability |

Each component is **z-score normalised** over the full available sample, directionally aligned so higher = more secure, then averaged into a composite. The composite is shifted to a positive range and expressed as an index (base year 2005 = 100).

### Why not U-6 or part-time for economic reasons?
Including involuntary part-time work created r = 0.81 with U-6 (because U-6 literally contains that subcomponent). Dropping it reduced U-6 correlation to r = 0.15 — making the index structurally differentiated rather than a repackaging of existing measures.

### Data coverage
- **JOLTS era (headline):** 2001–present, annual
- **Legacy series:** 1983–2000 (union + tenure only, 2-component)
- **Monthly variant:** JOLTS-only composite (openings + quits + layoffs), 2001–present

---

## Key Findings

### WJSI leads Michigan Consumer Sentiment by ~2 years

| Lag | Headline r | p-value |
|---|---|---|
| Concurrent | +0.15 | 0.47 |
| Index leads by 1yr | +0.18 | 0.40 |
| **Index leads by 2yr** | **+0.45** | **0.033** |
| Index leads by 3yr | +0.25 | 0.26 |

The predictive relationship is carried by the **joint signal** of structural durability (union + tenure) and flow stability (JOLTS). Pure JOLTS-only or structural-only variants lose significance.

### WJSI vs. headline unemployment diverge most when it matters
Post-2022: U-3 ≤ 4% while WJSI declined from 99 to 87 — driven by quit rate collapse, union erosion, and tenure decline. Workers are employed but structurally less secure.

### Index at key moments (base 2005 = 100)

| Year | WJSI | Context |
|---|---|---|
| 2001 | 89.8 | Dot-com bust + 9/11 |
| 2005 | 100.0 | Base year |
| 2009 | 83.2 | GFC trough |
| 2019 | 98.4 | Pre-COVID peak |
| 2020 | 51.7 | COVID shock |
| 2022 | 99.1 | Post-COVID tightening |
| 2024 | 86.8 | Present (structural deterioration) |

---

## Variants

| Variant | Components | Frequency | Key difference |
|---|---|---|---|
| **Headline** | Union + openings + quits + layoffs + tenure | Annual | Primary index |
| **Variant A** | Union + quits + layoffs + tenure (ex openings) | Annual | Tests openings sign convention |
| **Variant B (JOLTS-MCI)** | Openings + quits + layoffs | Monthly | Real-time tightness gauge |

Variant B (JOLTS-only) tracks U-3 at r = −0.77 — it's measuring cyclical tightness, not structural security. The sentiment lead story disappears without the structural components.

---

## Repository Structure

```
.
├── wjsi/
│   ├── fetch_bls.py          # BLS API v2 fetcher (6 series + tenure scraper)
│   ├── fetch_fred.py         # FRED fetcher (sentiment, U-6, savings rate, etc.)
│   ├── clean.py              # Annual averaging, tenure interpolation, COVID flags
│   ├── construct.py          # Index construction, z-scoring, base-year indexing
│   ├── backtest.py           # 5 weighting scheme sensitivity tests
│   ├── correlations.py       # Lead/lag vs Michigan, Granger causality, permutation tests
│   ├── variants.py           # Variant A (ex openings) + Variant B (monthly JOLTS-MCI)
│   ├── run_all.py            # Pipeline runner
│   ├── data/
│   │   ├── raw/              # Raw API responses (CSV)
│   │   └── clean/            # Processed annual series (CSV)
│   └── outputs/
│       ├── wjsi_annual.csv               # Primary index output
│       ├── wjsi_legacy_1983.csv          # 1983–2000 legacy series
│       ├── jolts_mci_monthly.csv         # Monthly JOLTS-only composite
│       ├── wjsi_variant_a_ex_openings.csv
│       └── charts/                       # All generated charts
├── viz/                      # Interactive React + Recharts explorer
│   └── src/App.jsx           # Lag slider, dual-line overlay, Pearson r badge
├── make_memo.js              # docx-js script → WJSI_Briefing_Note.docx
└── WJSI_Briefing_Note.docx   # 3-page briefing note for LISEP
```

---

## Running the Pipeline

### Requirements
- Python 3.9+
- `pip install pandas numpy matplotlib scipy fredapi python-dotenv requests`
- Node 18+ (for the React explorer and memo generation)
- BLS API key (free at [bls.gov/developers](https://www.bls.gov/developers/))
- FRED API key (free at [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html))

### Setup
```bash
git clone https://github.com/amiasmg/worker-job-security-index.git
cd worker-job-security-index

# Add API keys
cp wjsi/.env.example wjsi/.env
# Edit wjsi/.env and add your BLS_API_KEY and FRED_API_KEY
```

### Run
```bash
cd wjsi

# Full pipeline (fetch → clean → construct → backtest → correlations)
python run_all.py

# Or step by step
python fetch_bls.py
python fetch_fred.py
python clean.py
python construct.py
python backtest.py
python correlations.py
python variants.py   # Variant A and B
```

### Interactive explorer
```bash
cd viz
npm install
npm run dev
# Open http://localhost:5173
```

---

## Data Sources

| Series | Source | Series ID |
|---|---|---|
| Union membership rate | BLS Current Population Survey | LUU0204899600 |
| Job openings rate | BLS JOLTS | JTS000000000000000JOR |
| Quit rate | BLS JOLTS | JTS000000000000000QUR |
| Layoffs & discharges rate | BLS JOLTS | JTS000000000000000LDR |
| Median job tenure | BLS Employee Tenure Survey | (biennial, scraped) |
| Michigan Consumer Sentiment | University of Michigan / FRED | UMCSENT |
| U-6 underemployment | BLS / FRED | U6RATE |
| U-3 unemployment | BLS / FRED | UNRATE |

---

## Methodological Notes

- **Openings sign convention:** Job openings are treated as a *negative* signal (high churn/instability) in the headline index. This is contested — the sensitivity analysis in `backtest.py` and `variants.py` tests both directions.
- **Base year:** 2005 chosen so that the 2009 GFC trough is meaningfully below 100 and 2019 is near 100, preserving directional readability across cycles.
- **COVID years (2020–2021) flagged** but not excluded — the COVID shock is a real structural event.
- **Granger causality:** WJSI → Michigan Sentiment passes at F=7.37, p=0.014. Permutation-corrected familywise p=0.16 — relationship is present but not conclusive on short sample (n=25).
- **Rolling window analysis:** The WJSI–sentiment lead relationship emerged post-GFC and is not present in pre-2008 data, suggesting it reflects a post-crisis structural regime.

---

## Status

This is preliminary research. Methodological feedback welcome — particularly on:
- Openings rate sign convention
- Weighting scheme (equal vs. structural-block vs. factor model)
- Extension of the legacy series pre-1983

---

## License

MIT — see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

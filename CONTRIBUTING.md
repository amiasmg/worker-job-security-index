# Contributing to WJSI

This is preliminary research and methodological feedback is welcome. The index will improve with more eyes on it.

## Open questions we'd most value input on

- **Openings sign convention** — job openings are currently treated as a negative signal (instability/churn). There's a reasonable case for the opposite. The sensitivity analysis in `backtest.py` tests both; we'd welcome argument either way.
- **Weighting scheme** — equal weights across 5 components means JOLTS drives 60% of the index. A structural-block weighting (JOLTS as one third, union one third, tenure one third) or a factor model approach (as used in the Fed's LMCI) may be more defensible.
- **Pre-1983 extension** — the legacy series uses only union + tenure. Other structural series that might extend coverage further back are welcome.
- **Granger causality on short sample** — the n=25 annual observations is the binding constraint on statistical rigour. Any methodological suggestions for handling this are appreciated.

## How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b your-feature-name`
3. Make your changes and run the pipeline: `cd wjsi && python run_all.py`
4. Open a pull request with a clear description of the change and the methodological rationale

For significant changes to index construction or component selection, open an issue first.

## Questions

Open an issue or start a discussion.

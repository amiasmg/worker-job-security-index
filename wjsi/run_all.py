"""
run_all.py — Master runner: executes all WJSI pipeline steps in order.

Run:
    export BLS_API_KEY="your_key"
    export FRED_API_KEY="your_key"
    python run_all.py
"""

import subprocess
import sys
from pathlib import Path

STEPS = [
    ("fetch_bls.py", "Fetching BLS series and tenure data"),
    ("fetch_fred.py", "Fetching FRED series"),
    ("clean.py", "Cleaning and normalizing components"),
    ("construct.py", "Constructing index and charts"),
    ("backtest.py", "Running sensitivity analysis"),
    ("correlations.py", "Running correlation analysis"),
]


def run_step(script: str, description: str) -> bool:
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"Script: {script}")
    print("=" * 60)
    result = subprocess.run([sys.executable, script], cwd=Path(__file__).parent)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {script} exited with code {result.returncode}")
        return False
    print(f"\n✓ Completed: {script}")
    return True


if __name__ == "__main__":
    import os
    missing_keys = []
    if not os.environ.get("BLS_API_KEY"):
        missing_keys.append("BLS_API_KEY")
    if not os.environ.get("FRED_API_KEY"):
        missing_keys.append("FRED_API_KEY")
    if missing_keys:
        print(f"WARNING: Missing environment variables: {', '.join(missing_keys)}")
        print("API calls may fail or be rate-limited. Set them and re-run.")

    failed = []
    for script, description in STEPS:
        ok = run_step(script, description)
        if not ok:
            failed.append(script)
            resp = input(f"\nContinue despite failure in {script}? [y/N] ").strip().lower()
            if resp != "y":
                print("Aborting.")
                sys.exit(1)

    print("\n" + "="*60)
    if failed:
        print(f"Pipeline completed with failures: {', '.join(failed)}")
    else:
        print("Pipeline completed successfully.")
    print("="*60)
    print("\nOutputs:")
    for p in sorted(Path("outputs").rglob("*")):
        if p.is_file():
            print(f"  {p}")

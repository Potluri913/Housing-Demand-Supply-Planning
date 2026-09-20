"""Run the whole pipeline: python run_all.py"""
import subprocess
import sys
from pathlib import Path

STEPS = [
    "01_clean_listings.py",
    "02_supply_analysis.py",
    "03_generate_demo_transactions.py",
    "04_demand_forecast.py",
    "05_supply_plan.py",
]

for step in STEPS:
    print(f"\n{'=' * 70}\nRunning {step}\n{'=' * 70}")
    subprocess.run([sys.executable, str(Path(__file__).parent / "src" / step)], check=True)
print("\nDone. See outputs/tables and outputs/charts.")

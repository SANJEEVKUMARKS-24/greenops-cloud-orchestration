"""
Preliminary five-job comparison (Chapter 4 of the interim report),
re-run on the corrected simulator.

Uses the controlled 24-hour carbon profiles and the five hand-crafted
jobs, so every scheduler is compared on exactly the same inputs.

    python -m experiments.comparison.run_all
"""

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import (
    CORE_REGIONS,
    RESULTS_DIR,
    load_traces,
    make_scheduler,
    preliminary_workload,
    run_simulation,
)


# ============================================================
# CONFIGURATION
# ============================================================

RESULTS_DIRECTORY = os.path.join(RESULTS_DIR, "comparison")

# Same settings as the preliminary experiment.
SCHEDULERS = {
    "Round Robin": ("round_robin", {}),
    "Cost Only": ("cost_only", {}),
    "Greenest Region": ("greenest_region", {}),
    "Temporal Green": ("temporal_green", {}),
    "GreenOps MOO": (
        "greenops_moo",
        dict(carbon_weight=0.5, cost_weight=0.2, waiting_weight=0.3),
    ),
}

COLUMNS = [
    "scheduler",
    "total_jobs",
    "completed_jobs",
    "rejected_jobs",
    "total_carbon_g",
    "total_energy_kwh",
    "total_cost",
    "sla_violations",
    "sla_violation_rate",
    "average_latency",
    "p95_latency",
]


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("GREENOPS SCHEDULER COMPARISON (5 jobs, controlled traces)")
    print("=" * 60)

    os.makedirs(RESULTS_DIRECTORY, exist_ok=True)

    traces = load_traces("controlled", CORE_REGIONS)

    all_results = []

    for name, (key, params) in SCHEDULERS.items():

        print(f"\nRUNNING: {name}")

        summary, jobs = run_simulation(
            make_scheduler(key, max_wait=6, **params),
            traces,
            preliminary_workload(),
            verbose=True,
        )

        summary["scheduler"] = name

        all_results.append(summary)

        output_file = os.path.join(
            RESULTS_DIRECTORY,
            f"{name.lower().replace(' ', '_')}.csv"
        )

        jobs.to_csv(output_file, index=False)

    comparison = pd.DataFrame(all_results)[COLUMNS]

    comparison_file = os.path.join(RESULTS_DIRECTORY, "comparison.csv")

    comparison.to_csv(comparison_file, index=False)

    print("\n" + "=" * 60)
    print("FINAL SCHEDULER COMPARISON")
    print("=" * 60)

    print(comparison.round(3).to_string(index=False))

    print(f"\nComparison saved to:\n{comparison_file}")


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

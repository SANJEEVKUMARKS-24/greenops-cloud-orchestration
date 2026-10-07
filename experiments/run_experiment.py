"""
Run ONE scheduler on ONE workload and print the per-job decisions.

Defaults reproduce the 100-job GreenOps MOO experiment:

    python -m experiments.run_experiment

Other examples:

    python -m experiments.run_experiment --scheduler temporal_green
    python -m experiments.run_experiment --period summer_2024 --forecast-error 0.15
    python -m experiments.run_experiment --period controlled --quiet
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import (
    CORE_REGIONS,
    PERIODS,
    RESULTS_DIR,
    SCHEDULER_LABELS,
    load_traces,
    load_workload,
    make_scheduler,
    run_simulation,
)
from experiments.evaluation import MAX_WAIT, MOO_PARAMS


# ============================================================
# PATH CONFIGURATION
# ============================================================

WORKLOAD_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "workload_traces",
    "workload_100.csv"
)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Run a single GreenOps simulation"
    )

    parser.add_argument(
        "--scheduler",
        default="greenops_moo",
        choices=sorted(SCHEDULER_LABELS)
    )

    parser.add_argument(
        "--period",
        default="winter_2024",
        choices=("controlled",) + PERIODS,
        help="carbon traces: 24h controlled profile or historical period"
    )

    parser.add_argument("--workload", default=WORKLOAD_FILE)

    parser.add_argument(
        "--forecast-error",
        type=float,
        default=0.0,
        help="relative forecast error at 24h horizon (0 = perfect)"
    )

    parser.add_argument("--max-wait", type=float, default=MAX_WAIT)

    parser.add_argument("--quiet", action="store_true")

    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    # ========================================================
    # SCENARIO
    # ========================================================

    traces = load_traces(args.period, CORE_REGIONS)

    jobs = load_workload(args.workload)

    params = (
        dict(MOO_PARAMS, verbose=not args.quiet)
        if args.scheduler.startswith("greenops")
        else {}
    )

    scheduler = make_scheduler(
        args.scheduler,
        max_wait=args.max_wait,
        **params
    )

    # ========================================================
    # WORKLOAD INFORMATION
    # ========================================================

    print("\n========================================")
    print(" GREENOPS EXPERIMENT")
    print("========================================")

    print(f"\nScheduler     : {SCHEDULER_LABELS[args.scheduler]}")
    print(f"Carbon traces : {args.period}")
    print(f"Forecast error: {args.forecast_error:.0%}")
    print(f"Workload file : {os.path.relpath(args.workload, PROJECT_ROOT)}")
    print(f"Total jobs    : {len(jobs)}")
    print(f"First arrival : {jobs[0].arrival_time}")
    print(f"Last arrival  : {jobs[-1].arrival_time}")

    counts = {}

    for job in jobs:
        counts[job.flexibility] = counts.get(job.flexibility, 0) + 1

    print("\nWorkload distribution:")

    for workload_type, count in counts.items():
        print(
            f"  {workload_type:10s}: {count:3d} "
            f"({count / len(jobs) * 100:.1f}%)"
        )

    pinned = sum(1 for job in jobs if job.allowed_regions)

    print(f"  region-pinned: {pinned}")

    # ========================================================
    # RUN SIMULATION
    # ========================================================

    print("\nStarting simulation...\n")

    summary, results = run_simulation(
        scheduler,
        traces,
        jobs,
        forecast_error=args.forecast_error,
        verbose=not args.quiet,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n========== SUMMARY ==========\n")

    for key, value in summary.items():

        if isinstance(value, float):
            print(f"{key:28s}: {value:,.3f}")
        else:
            print(f"{key:28s}: {value}")

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output = args.output or os.path.join(
        RESULTS_DIR,
        f"{args.scheduler}_{args.period}_{len(jobs)}_jobs_results.csv"
    )

    os.makedirs(os.path.dirname(output), exist_ok=True)

    results.to_csv(output, index=False)

    print(f"\nResults saved to:\n{output}")

    print("\n========================================")
    print(" EXPERIMENT COMPLETED")
    print("========================================\n")


if __name__ == "__main__":
    main()

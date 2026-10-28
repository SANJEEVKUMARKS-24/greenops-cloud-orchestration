"""
GreenOps live demo - one command for the viva.

    python demo.py            (pauses between steps - press Enter)
    python demo.py --no-pause (runs straight through)

Steps
  1. The real carbon data the simulator uses
  2. GreenOps making decisions, job by job
  3. Five-job comparison (preliminary experiment)
  4. 100-job comparison on real January 2024 grid data
  5. Automated tests
"""

import argparse
import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from experiments.scenario import (
    CORE_REGIONS,
    load_traces,
    load_workload,
    make_scheduler,
    preliminary_workload,
    run_simulation,
)
from experiments.evaluation import MOO_PARAMS
from sim.forecast import REALISTIC_ERROR


WORKLOAD = os.path.join(PROJECT_ROOT, "data", "workload_traces", "workload_100.csv")

SCHEDULERS = [
    ("cost_only", "Cost Only"),
    ("round_robin", "Round Robin"),
    ("greenest_region", "Greenest Region"),
    ("temporal_green", "Temporal Green"),
    ("greenops_moo", "GreenOps (ours)"),
]

PAUSE = True


# ============================================================
# HELPERS
# ============================================================

def heading(number, title, explanation):

    print("\n" + "=" * 72)
    print(f" STEP {number}: {title}")
    print("=" * 72)
    print(explanation + "\n")


def pause():

    if PAUSE:
        input("\n   ... press Enter to continue ")


def params_for(key):

    return dict(MOO_PARAMS) if key.startswith("greenops") else {}


def comparison_table(traces, jobs_factory, forecast_error=0.0, max_wait=12,
                     moo_params=None):

    rows = []

    for key, label in SCHEDULERS:

        summary, _ = run_simulation(
            make_scheduler(
                key,
                max_wait=max_wait,
                **(moo_params if moo_params and key.startswith("greenops")
                   else params_for(key)),
            ),
            traces,
            jobs_factory(),
            forecast_error=forecast_error,
        )

        rows.append({
            "Scheduler": label,
            "Carbon (g)": round(summary["total_carbon_g"], 1),
            "Cost ($)": round(summary["total_cost"], 2),
            "SLA violations": int(summary["sla_violations"]),
            "Avg latency (h)": round(summary["average_latency"], 2),
        })

    table = pd.DataFrame(rows)

    baseline = table.loc[table["Scheduler"] == "Round Robin", "Carbon (g)"].iloc[0]

    table["Carbon vs Round Robin"] = (
        (table["Carbon (g)"] / baseline - 1) * 100
    ).map(lambda v: f"{v:+.1f} %")

    return table


# ============================================================
# STEPS
# ============================================================

def step_data():

    heading(
        1, "Real carbon data",
        "Hourly grid carbon intensity (gCO2eq per kWh) for January 2024.\n"
        "Germany and Norway come from Energy-Charts (real generation mix);\n"
        "India is modelled from official CEA figures.",
    )

    traces = load_traces("winter_2024", CORE_REGIONS)

    rows = []

    for name, values in traces.items():
        series = pd.Series(values)
        rows.append({
            "Region": name,
            "Mean": round(series.mean()),
            "Lowest hour": round(series.min()),
            "Highest hour": round(series.max()),
        })

    print(pd.DataFrame(rows).to_string(index=False))

    print("\n   -> Norway is ~25x cleaner than India: SPATIAL shifting.")
    print("   -> Germany swings by hundreds of g/kWh: TEMPORAL shifting.")

    pause()


def step_decisions():

    heading(
        2, "GreenOps making decisions",
        "For each arriving job GreenOps checks every region x start hour,\n"
        "rejects options that break the deadline or budget, then scores\n"
        "carbon, cost and deadline risk. First 12 jobs of the workload:",
    )

    traces = load_traces("winter_2024", CORE_REGIONS)

    jobs = load_workload(WORKLOAD)[:12]

    scheduler = make_scheduler("greenops_moo", max_wait=12,
                               **dict(MOO_PARAMS, verbose=True))

    run_simulation(scheduler, traces, jobs)

    print("\n   Strict jobs always start now (wait=0.0 h); flexible jobs may wait")
    print("   or move region when that saves carbon without risking the deadline.")
    print("   A job ID that appears again (e.g. J0004) is a waiting job being")
    print("   RE-PLANNED an hour later with a fresher carbon forecast.")

    pause()


def step_preliminary():

    heading(
        3, "Five-job comparison",
        "The preliminary experiment: 5 hand-made jobs, 3 regions, all\n"
        "five schedulers on exactly the same input.",
    )

    traces = load_traces("controlled", CORE_REGIONS)

    # Same settings as the preliminary experiment in the report (Table 4.2).
    table = comparison_table(
        traces, preliminary_workload, max_wait=6,
        moo_params=dict(carbon_weight=0.5, cost_weight=0.2, waiting_weight=0.3),
    )

    print(table.to_string(index=False))

    pause()


def step_full():

    heading(
        4, "100-job comparison on real grid data",
        "100 mixed jobs (strict / batch / flexible) on the real January 2024\n"
        f"carbon traces, with a realistic {REALISTIC_ERROR:.0%} carbon-forecast error.",
    )

    traces = load_traces("winter_2024", CORE_REGIONS)

    started = time.time()

    table = comparison_table(
        traces,
        lambda: load_workload(WORKLOAD),
        forecast_error=REALISTIC_ERROR,
    )

    print(table.to_string(index=False))

    print(f"\n   All five simulations finished in {time.time() - started:.1f} s.")
    print("   Full study (20 seeds x 2 seasons): GreenOps -26.8 % carbon vs")
    print("   Round Robin and -5.3 % vs Greenest Region, deadlines kept.")

    pause()


def step_tests():

    heading(
        5, "Automated tests",
        "50 unit and integration tests check the guarantees, e.g. strict jobs\n"
        "are never delayed and no deferral ever breaks a deadline.",
    )

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    lines = result.stderr.strip().splitlines()

    print("   " + "\n   ".join(lines[-3:]))


# ============================================================
# MAIN
# ============================================================

def main():

    global PAUSE

    parser = argparse.ArgumentParser(description="GreenOps live demo")
    parser.add_argument("--no-pause", action="store_true")
    args = parser.parse_args()

    PAUSE = not args.no_pause

    pd.set_option("display.width", 120)

    print("\n" + "#" * 72)
    print("  GreenOps Cloud Orchestration - live demo")
    print("  Carbon-aware spatial and temporal workload scheduling")
    print("#" * 72)

    step_data()
    step_decisions()
    step_preliminary()
    step_full()
    step_tests()

    print("\n" + "#" * 72)
    print("  Demo complete. Interactive results: open docs/dashboard.html")
    print("#" * 72 + "\n")


if __name__ == "__main__":
    main()

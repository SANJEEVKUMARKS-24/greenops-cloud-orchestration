"""
Trace-driven, data-aware evaluation for the workshop paper.

Setting
-------
* Workload : Alibaba Cluster Trace v2018 (real arrivals, runtimes and
             CPU demand), 10 % job sample per seed (~45 k jobs, 8 days)
* Cloud    : India, Germany, Norway; 1,280 vCPU each (80 nodes x 16)
* Carbon   : historical hourly traces, winter + summer 2024
* Forecast : calibrated error (15 % at 24 h)
* Network  : data moves when a job runs outside its home region
             (0.005 kWh/GB, $0.02/GB, 1 Gbit/s)

Experiments
-----------
P1  main        9 policies incl. two published baselines
                (Wait Awhile [Wiesner'21], Online Threshold [Lechowicz'24])
P2  frontier    GreenOps carbon-weight sweep vs baselines (carbon, SLA, cost)
P3  gravity     data intensity 0 ... 30 GB per core-hour (data gravity)
P4  forecast    forecast error 0 ... 50 %
P5  scale       2 % ... 20 % of the trace (9 k ... 90 k jobs)

    python -m experiments.paper [--only P1,P3] [--quick]

Output: results/paper/*.csv
"""

import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import (
    CORE_REGIONS,
    PERIODS,
    RESULTS_DIR,
    load_traces,
    make_scheduler,
    run_simulation,
)
from experiments.trace_workload import make_trace_workload
from experiments.evaluation import MOO_PARAMS, paired_permutation_test
from sim.forecast import REALISTIC_ERROR
from sim.network import NetworkModel


OUTPUT_DIR = os.path.join(RESULTS_DIR, "paper")

CAPACITY = 1280

FRACTION = 0.10

MAX_WAIT = 12

POLICIES = {
    "round_robin": ("round_robin", {}, "Round Robin"),
    "cost_only": ("cost_only", {}, "Cost Only"),
    "greenest_region": ("greenest_region", {}, "Greenest Region"),
    "wait_awhile": ("wait_awhile", {}, "Wait Awhile [17]"),
    "threshold": ("threshold", {}, "Online Threshold [12]"),
    "temporal_green": ("temporal_green", {}, "Temporal Green"),
    "greenops_spatial": ("greenops_spatial", dict(MOO_PARAMS),
                         "GreenOps (spatial only)"),
    "greenops_unaware": ("greenops_moo",
                         dict(MOO_PARAMS, transfer_aware=False),
                         "GreenOps (transfer-unaware)"),
    "greenops": ("greenops_moo", dict(MOO_PARAMS), "GreenOps"),
}


# ============================================================
# TASKS
# ============================================================

_TRACES = {}


def spec(experiment, policy, seed, period, params=None, label=None,
         forecast_error=REALISTIC_ERROR, gb_per_core_hour=1.0,
         fraction=FRACTION, capacity=CAPACITY, **extra):

    key, default_params, default_label = POLICIES[policy]

    return dict(
        experiment=experiment,
        policy=policy,
        scheduler=key,
        params=dict(default_params if params is None else params),
        label=label or default_label,
        seed=seed,
        period=period,
        forecast_error=forecast_error,
        gb_per_core_hour=gb_per_core_hour,
        fraction=fraction,
        capacity=capacity,
        **extra,
    )


def run(task):

    if task["period"] not in _TRACES:
        _TRACES[task["period"]] = load_traces(task["period"], CORE_REGIONS)

    jobs = make_trace_workload(
        task["seed"],
        CORE_REGIONS,
        fraction=task["fraction"],
        gb_per_core_hour=task["gb_per_core_hour"],
    )

    scheduler = make_scheduler(
        task["scheduler"], max_wait=MAX_WAIT, **task["params"]
    )

    started = time.perf_counter()

    summary, jobs_df = run_simulation(
        scheduler,
        _TRACES[task["period"]],
        jobs,
        forecast_error=task["forecast_error"],
        forecast_seed=task["seed"],
        cpu_capacity=task["capacity"],
        network=NetworkModel(),
    )

    row = {k: v for k, v in task.items() if k != "params"}

    for key, value in task["params"].items():
        row[f"param_{key}"] = value

    row.update(summary)

    row["wall_seconds"] = time.perf_counter() - started
    row["decisions"] = int(jobs_df["decisions"].sum())

    done = jobs_df[jobs_df["status"] == "completed"]

    row["energy_compute_kwh"] = done["energy_consumed"].sum()
    row["deferred_pct"] = (done["waiting_time"] > 1 / 60).mean() * 100

    for flex, group in done.groupby("flexibility"):
        row[f"{flex}_violation_rate"] = group["sla_violated"].mean() * 100

    return row


def execute(tasks, workers):

    # Longest first for better load balance.
    tasks = sorted(tasks, key=lambda t: -t["fraction"])

    if workers > 1:
        with Pool(workers) as pool:
            rows = pool.map(run, tasks, chunksize=1)
    else:
        rows = [run(t) for t in tasks]

    return pd.DataFrame(rows)


def summarise(df, by, metrics):

    grouped = df.groupby(by)[metrics]

    return (
        grouped.mean().add_suffix("_mean")
        .join(grouped.std().add_suffix("_std"))
        .reset_index()
    )


METRICS = [
    "total_carbon_g", "transfer_carbon_g", "total_cost", "transfer_cost",
    "sla_violation_rate", "strict_violation_rate", "mean_tardiness",
    "average_latency", "p95_latency", "moved_jobs_pct", "deferred_pct",
    "share_Norway", "share_Germany", "share_India", "wall_seconds",
]


# ============================================================
# P1 - MAIN
# ============================================================

def p1(seeds, workers):

    tasks = [
        spec("P1", policy, seed, period)
        for policy in POLICIES
        for period in PERIODS
        for seed in seeds
    ]

    df = execute(tasks, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "p1_main_runs.csv"), index=False)

    key = ["period", "seed"]

    ref = df.set_index(key + ["policy"])

    for name in ("round_robin", "greenest_region"):
        df[f"carbon_vs_{name}_pct"] = df.apply(
            lambda r: (r["total_carbon_g"]
                       / ref.loc[(r["period"], r["seed"], name),
                                 "total_carbon_g"] - 1) * 100,
            axis=1,
        )

    table = summarise(
        df, ["policy", "label"],
        METRICS + ["carbon_vs_round_robin_pct", "carbon_vs_greenest_region_pct"],
    )

    table.to_csv(os.path.join(OUTPUT_DIR, "p1_main_summary.csv"), index=False)

    tests = []

    ours = df[df["policy"] == "greenops"].sort_values(key)

    for other in POLICIES:

        if other == "greenops":
            continue

        rival = df[df["policy"] == other].sort_values(key)

        for metric in ("total_carbon_g", "sla_violation_rate", "total_cost",
                       "p95_latency"):

            diff, p_value = paired_permutation_test(
                ours[metric].values, rival[metric].values
            )

            tests.append(dict(
                rival=POLICIES[other][2], metric=metric,
                mean_difference=diff,
                relative_pct=diff / rival[metric].mean() * 100
                if rival[metric].mean() else np.nan,
                p_value=p_value, n_pairs=len(ours),
            ))

    pd.DataFrame(tests).to_csv(
        os.path.join(OUTPUT_DIR, "p1_significance.csv"), index=False
    )

    return table[["label", "total_carbon_g_mean", "carbon_vs_greenest_region_pct_mean",
                  "sla_violation_rate_mean", "p95_latency_mean",
                  "total_cost_mean", "moved_jobs_pct_mean"]]


# ============================================================
# P2 - CARBON / SLA / COST FRONTIER
# ============================================================

def p2(seeds, workers):

    tasks = []

    for wc in (0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0):

        params = dict(MOO_PARAMS, carbon_weight=wc)

        for period in PERIODS:
            for seed in seeds:
                tasks.append(spec(
                    "P2", "greenops", seed, period, params=params,
                    label=f"GreenOps w_c={wc}", carbon_weight=wc,
                ))

    for policy in ("round_robin", "cost_only", "greenest_region",
                   "wait_awhile", "threshold", "temporal_green"):
        for period in PERIODS:
            for seed in seeds:
                tasks.append(spec("P2", policy, seed, period, carbon_weight=np.nan))

    df = execute(tasks, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "p2_frontier_runs.csv"), index=False)

    table = summarise(df.fillna({"carbon_weight": -1}),
                      ["policy", "label", "carbon_weight"], METRICS)

    table.to_csv(os.path.join(OUTPUT_DIR, "p2_frontier_summary.csv"), index=False)

    return table[["label", "total_carbon_g_mean", "sla_violation_rate_mean",
                  "p95_latency_mean", "total_cost_mean"]]


# ============================================================
# P3 - DATA GRAVITY
# ============================================================

def p3(seeds, workers):

    policies = ("greenest_region", "wait_awhile", "threshold",
                "temporal_green", "greenops_unaware", "greenops")

    tasks = [
        spec("P3", policy, seed, period, gb_per_core_hour=gb)
        for gb in (0.0, 0.3, 1.0, 3.0, 10.0, 30.0)
        for policy in policies
        for period in PERIODS
        for seed in seeds
    ]

    df = execute(tasks, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "p3_gravity_runs.csv"), index=False)

    table = summarise(df, ["policy", "label", "gb_per_core_hour"], METRICS)

    table.to_csv(os.path.join(OUTPUT_DIR, "p3_gravity_summary.csv"), index=False)

    return table.pivot_table(index="gb_per_core_hour", columns="label",
                             values="total_carbon_g_mean").round(0)


# ============================================================
# P4 - FORECAST ERROR
# ============================================================

def p4(seeds, workers):

    tasks = [
        spec("P4", policy, seed, period, forecast_error=error)
        for error in (0.0, 0.15, 0.30, 0.50)
        for policy in ("wait_awhile", "temporal_green", "greenops")
        for period in PERIODS
        for seed in seeds
    ]

    # Forecast-free references
    tasks += [
        spec("P4", policy, seed, period, forecast_error=0.0)
        for policy in ("greenest_region", "threshold")
        for period in PERIODS
        for seed in seeds
    ]

    df = execute(tasks, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "p4_forecast_runs.csv"), index=False)

    table = summarise(df, ["policy", "label", "forecast_error"], METRICS)

    table.to_csv(os.path.join(OUTPUT_DIR, "p4_forecast_summary.csv"), index=False)

    return table.pivot_table(index="forecast_error", columns="label",
                             values=["total_carbon_g_mean",
                                     "sla_violation_rate_mean"]).round(2)


# ============================================================
# P5 - SCALE
# ============================================================

def p5():

    tasks = [
        spec("P5", policy, 0, "winter_2024", fraction=fraction,
             capacity=int(round(CAPACITY * fraction / FRACTION)))
        for fraction in (0.02, 0.05, 0.10, 0.20)
        for policy in ("greenest_region", "threshold", "greenops")
    ]

    df = execute(tasks, workers=1)

    df["jobs"] = df["total_jobs"]
    df["ms_per_job"] = df["wall_seconds"] / df["jobs"] * 1000

    df.to_csv(os.path.join(OUTPUT_DIR, "p5_scale_runs.csv"), index=False)

    return df[["label", "jobs", "capacity", "wall_seconds", "ms_per_job",
               "total_carbon_g", "sla_violation_rate"]]


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="P1,P2,P3,P4,P5")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--workers", type=int,
                        default=max(1, (os.cpu_count() or 2) - 2))
    args = parser.parse_args()

    selected = {e.strip().upper() for e in args.only.split(",")}

    main_seeds = range(2) if args.quick else range(6)
    seeds = range(1) if args.quick else range(3)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)

    steps = [
        ("P1", lambda: p1(main_seeds, args.workers)),
        ("P2", lambda: p2(seeds, args.workers)),
        ("P3", lambda: p3(seeds, args.workers)),
        ("P4", lambda: p4(seeds, args.workers)),
        ("P5", p5),
    ]

    for key, step in steps:

        if key not in selected:
            continue

        started = time.time()

        print(f"\n{'=' * 70}\n{key}\n{'=' * 70}", flush=True)

        print(step().round(3).to_string(), flush=True)

        print(f"[{key} finished in {time.time() - started:.0f} s]", flush=True)


if __name__ == "__main__":
    main()

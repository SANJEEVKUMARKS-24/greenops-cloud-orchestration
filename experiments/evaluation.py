"""
GreenOps research-grade evaluation.

Experiments
-----------
E1  main        all schedulers x 2 trace periods x 20 seeds, 300 jobs,
                realistic (calibrated) forecast error
E2  sweep       weight sweep over the (carbon, cost, SLA-risk) simplex for
                the weighted-sum and Pareto/Tchebycheff modes -> Pareto
                frontier + hypervolume
E3  forecast    forecast-error sensitivity (0 ... 50 %), with and without
                the confidence gate, on the 3-region and a Germany-only
                (pure temporal shifting) scenario
E4  maxwait     how much temporal flexibility is actually useful
E5  load        system load (utilisation) sensitivity
E6  extended    6-region scenario (adds France, Poland, Great Britain)
E7  scale       scalability of the decision engine (wall-clock time)

Usage
-----
    python -m experiments.evaluation                 # everything
    python -m experiments.evaluation --only E1,E3    # a subset
    python -m experiments.evaluation --quick         # fewer seeds

Results go to results/evaluation/*.csv. Figures are produced by
experiments/plots.py.
"""

import argparse
import itertools
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
    EXTENDED_REGIONS,
    PERIODS,
    RESULTS_DIR,
    SCHEDULER_LABELS,
    load_traces,
    make_scheduler,
    make_workload,
    run_simulation,
)
from sim.forecast import REALISTIC_ERROR


OUTPUT_DIR = os.path.join(RESULTS_DIR, "evaluation")

NUM_JOBS = 300

# Weights selected on tuning seeds 100-104 (never used for evaluation).
MOO_PARAMS = dict(
    carbon_weight=0.6,
    cost_weight=0.2,
    waiting_weight=0.2,
    risk_aversion=0.5,
    risk_exponent=2.0,
)

MAX_WAIT = 12

MAIN_SCHEDULERS = (
    "round_robin",
    "cost_only",
    "greenest_region",
    "temporal_green",
    "greenops_spatial",
    "greenops_moo",
    "greenops_pareto",
)

# `load` rescales the arrival rate so that per-region utilisation is
# comparable across scenarios (one region gets a third of the load of
# three regions).
SCENARIOS = {
    "core": dict(regions=CORE_REGIONS, locality=0.25, load=1.0),
    "germany_only": dict(regions=("Germany",), locality=0.0, load=1 / 3),
    "extended": dict(regions=EXTENDED_REGIONS, locality=0.25, load=1.0),
}


# ============================================================
# TASK EXECUTION (runs inside worker processes)
# ============================================================

_TRACE_CACHE = {}


def _traces(period, regions):

    key = (period, tuple(regions))

    if key not in _TRACE_CACHE:
        _TRACE_CACHE[key] = load_traces(period, regions)

    return _TRACE_CACHE[key]


def task(experiment, scheduler, seed, period="winter_2024",
         scenario="core", label=None, params=None, num_jobs=NUM_JOBS,
         load_scale=1.0, forecast_error=REALISTIC_ERROR,
         max_wait=MAX_WAIT, keep_jobs=False, **extra):

    return dict(
        experiment=experiment,
        scheduler=scheduler,
        label=label or SCHEDULER_LABELS[scheduler],
        seed=seed,
        period=period,
        scenario=scenario,
        params=dict(params or {}),
        num_jobs=num_jobs,
        load_scale=load_scale,
        forecast_error=forecast_error,
        max_wait=max_wait,
        keep_jobs=keep_jobs,
        **extra,
    )


def default_params(scheduler):

    if scheduler.startswith("greenops"):
        return dict(MOO_PARAMS)

    return {}


def run_task(spec):

    scenario = SCENARIOS[spec["scenario"]]

    traces = _traces(spec["period"], scenario["regions"])

    jobs = make_workload(
        spec["num_jobs"],
        spec["seed"],
        locality_fraction=scenario["locality"],
        region_names=scenario["regions"],
        load_scale=spec["load_scale"] * scenario["load"],
    )

    params = spec["params"] or default_params(spec["scheduler"])

    scheduler = make_scheduler(
        spec["scheduler"],
        max_wait=spec["max_wait"],
        **params,
    )

    started = time.perf_counter()

    summary, jobs_df = run_simulation(
        scheduler,
        traces,
        jobs,
        forecast_error=spec["forecast_error"],
        forecast_seed=spec["seed"],
    )

    elapsed = time.perf_counter() - started

    row = {
        key: value
        for key, value in spec.items()
        if key not in ("params", "keep_jobs")
    }

    for key, value in params.items():
        row[f"param_{key}"] = value

    row.update(summary)

    row["wall_seconds"] = elapsed
    row["decisions"] = int(jobs_df["decisions"].sum())

    if spec["keep_jobs"]:

        jobs_df = jobs_df.assign(
            label=spec["label"],
            seed=spec["seed"],
            period=spec["period"],
        )

        return row, jobs_df

    return row, None


def execute(specs, workers):

    rows = []
    frames = []

    if workers > 1:

        with Pool(workers) as pool:
            results = pool.map(run_task, specs, chunksize=4)

    else:

        results = [run_task(spec) for spec in specs]

    for row, jobs_df in results:

        rows.append(row)

        if jobs_df is not None:
            frames.append(jobs_df)

    jobs = pd.concat(frames, ignore_index=True) if frames else None

    return pd.DataFrame(rows), jobs


# ============================================================
# STATISTICS
# ============================================================

def paired_permutation_test(a, b, iterations=20000, seed=0):
    """
    Two-sided paired sign-flip permutation test on mean(a - b).
    Returns (mean difference, p-value).
    """

    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)

    observed = abs(diff.mean())

    rng = np.random.default_rng(seed)

    signs = rng.choice([-1.0, 1.0], size=(iterations, len(diff)))

    null = np.abs((signs * diff).mean(axis=1))

    p_value = (np.sum(null >= observed - 1e-12) + 1) / (iterations + 1)

    return diff.mean(), p_value


def hypervolume_2d(points, reference):
    """Exact 2-D hypervolume (minimisation) of a point set."""

    pts = sorted(
        (p for p in points if p[0] < reference[0] and p[1] < reference[1]),
        key=lambda p: (p[0], p[1]),
    )

    front = []

    best_y = float("inf")

    for x, y in pts:
        if y < best_y:
            front.append((x, y))
            best_y = y

    volume = 0.0

    for i, (x, y) in enumerate(front):

        next_x = front[i + 1][0] if i + 1 < len(front) else reference[0]

        volume += (next_x - x) * (reference[1] - y)

    return volume


def summarise(df, by, metrics):

    grouped = df.groupby(by)[metrics]

    out = grouped.mean().add_suffix("_mean").join(
        grouped.std().add_suffix("_std")
    )

    return out.reset_index()


# ============================================================
# E1 - MAIN COMPARISON
# ============================================================

def experiment_main(seeds, workers):

    specs = [
        task("E1", scheduler, seed, period=period,
             keep_jobs=(seed < 5))
        for period in PERIODS
        for seed in seeds
        for scheduler in MAIN_SCHEDULERS
    ]

    df, jobs = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e1_main_runs.csv"), index=False)

    jobs.to_csv(os.path.join(OUTPUT_DIR, "e1_main_jobs.csv"), index=False)

    # ---------------------------------------------------------
    # Paired relative metrics (same seed + period)
    # ---------------------------------------------------------

    key = ["period", "seed"]

    reference = df.set_index(key + ["scheduler"])

    def ref(name, column):
        return df.apply(
            lambda r: reference.loc[(r["period"], r["seed"], name), column],
            axis=1,
        )

    df["carbon_vs_round_robin_pct"] = (
        (df["total_carbon_g"] / ref("round_robin", "total_carbon_g") - 1)
        * 100
    )

    df["carbon_vs_greenest_pct"] = (
        (df["total_carbon_g"] / ref("greenest_region", "total_carbon_g") - 1)
        * 100
    )

    df["cost_overhead_vs_cost_only_pct"] = (
        (df["total_cost"] / ref("cost_only", "total_cost") - 1) * 100
    )

    metrics = [
        "total_carbon_g",
        "total_cost",
        "avg_carbon_intensity",
        "sla_violations",
        "sla_violation_rate",
        "mean_tardiness",
        "average_latency",
        "p95_latency",
        "p99_latency",
        "strict_avg_latency",
        "carbon_vs_round_robin_pct",
        "carbon_vs_greenest_pct",
        "cost_overhead_vs_cost_only_pct",
        "rejected_jobs",
    ]

    table = summarise(df, ["period", "scheduler", "label"], metrics)

    pooled = summarise(df, ["scheduler", "label"], metrics)
    pooled.insert(0, "period", "both")

    table = pd.concat([table, pooled], ignore_index=True)

    table.to_csv(os.path.join(OUTPUT_DIR, "e1_main_summary.csv"), index=False)

    # ---------------------------------------------------------
    # Significance: GreenOps MOO vs every other scheduler
    # ---------------------------------------------------------

    tests = []

    moo = df[df["scheduler"] == "greenops_moo"].sort_values(key)

    for other in MAIN_SCHEDULERS:

        if other == "greenops_moo":
            continue

        rival = df[df["scheduler"] == other].sort_values(key)

        for metric in ("total_carbon_g", "total_cost", "average_latency",
                       "sla_violations"):

            mean_diff, p_value = paired_permutation_test(
                moo[metric].values,
                rival[metric].values,
            )

            tests.append(dict(
                comparison=f"GreenOps MOO - {SCHEDULER_LABELS[other]}",
                metric=metric,
                mean_difference=mean_diff,
                relative_pct=mean_diff / rival[metric].mean() * 100
                if rival[metric].mean() else np.nan,
                p_value=p_value,
                n_pairs=len(moo),
            ))

    pd.DataFrame(tests).to_csv(
        os.path.join(OUTPUT_DIR, "e1_significance.csv"),
        index=False,
    )

    return table


# ============================================================
# E2 - WEIGHT SWEEP / PARETO FRONTIER
# ============================================================

def simplex_grid(step=0.1):

    n = int(round(1 / step))

    for i, j in itertools.product(range(n + 1), repeat=2):

        if i + j > n:
            continue

        yield (
            round(i * step, 3),
            round(j * step, 3),
            round((n - i - j) * step, 3),
        )


def experiment_sweep(seeds, workers):

    specs = []

    for wc, wk, wr in simplex_grid(0.1):

        params = dict(
            carbon_weight=wc,
            cost_weight=wk,
            waiting_weight=wr,
            risk_aversion=MOO_PARAMS["risk_aversion"],
            risk_exponent=MOO_PARAMS["risk_exponent"],
        )

        for mode in ("greenops_moo", "greenops_pareto"):
            for period in PERIODS:
                for seed in seeds:
                    specs.append(task(
                        "E2",
                        mode,
                        seed,
                        period=period,
                        params=params,
                        label=f"{SCHEDULER_LABELS[mode]} "
                              f"({wc:.1f}/{wk:.1f}/{wr:.1f})",
                    ))

    for scheduler in ("round_robin", "cost_only", "greenest_region",
                      "temporal_green"):
        for period in PERIODS:
            for seed in seeds:
                specs.append(task("E2", scheduler, seed, period=period))

    df, _ = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e2_sweep_runs.csv"), index=False)

    group = [
        "scheduler", "label",
        "param_carbon_weight", "param_cost_weight", "param_waiting_weight",
    ]

    points = (
        df.fillna({c: -1 for c in group[2:]})
        .groupby(group)[["total_carbon_g", "total_cost", "average_latency",
                         "p95_latency", "sla_violations"]]
        .mean()
        .reset_index()
    )

    points.to_csv(os.path.join(OUTPUT_DIR, "e2_sweep_points.csv"), index=False)

    # ---------------------------------------------------------
    # Hypervolume (carbon, cost) per scheduler family,
    # normalised to [0, 1] with reference point 1.1
    # ---------------------------------------------------------

    c_min, c_max = points["total_carbon_g"].min(), points["total_carbon_g"].max()
    k_min, k_max = points["total_cost"].min(), points["total_cost"].max()

    def norm(row):
        return (
            (row["total_carbon_g"] - c_min) / (c_max - c_min),
            (row["total_cost"] - k_min) / (k_max - k_min),
        )

    hv_rows = []

    for scheduler, group_df in points.groupby("scheduler"):

        normalised = [norm(r) for _, r in group_df.iterrows()]

        hv_rows.append(dict(
            scheduler=scheduler,
            label=SCHEDULER_LABELS[scheduler],
            configurations=len(group_df),
            hypervolume=hypervolume_2d(normalised, (1.1, 1.1)),
        ))

    baselines = points[~points["scheduler"].str.startswith("greenops")]

    hv_rows.append(dict(
        scheduler="all_baselines",
        label="All four baselines together",
        configurations=len(baselines),
        hypervolume=hypervolume_2d(
            [norm(r) for _, r in baselines.iterrows()], (1.1, 1.1)
        ),
    ))

    hv = pd.DataFrame(hv_rows).sort_values("hypervolume", ascending=False)

    hv.to_csv(os.path.join(OUTPUT_DIR, "e2_hypervolume.csv"), index=False)

    return hv


# ============================================================
# E3 - FORECAST-ERROR SENSITIVITY
# ============================================================

FORECAST_VARIANTS = {
    "temporal_green": ("temporal_green", {}),
    "greenops_moo": ("greenops_moo", dict(MOO_PARAMS)),
    "greenops_moo_nogate": (
        "greenops_moo",
        dict(MOO_PARAMS, risk_aversion=0.0),
    ),
}

FORECAST_LABELS = {
    "temporal_green": "Temporal Green",
    "greenops_moo": "GreenOps MOO (confidence gate)",
    "greenops_moo_nogate": "GreenOps MOO (no gate)",
}


def experiment_forecast(seeds, workers):

    errors = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50)

    specs = []

    for scenario in ("core", "germany_only"):
        for error in errors:
            for variant, (scheduler, params) in FORECAST_VARIANTS.items():
                for period in PERIODS:
                    for seed in seeds:
                        specs.append(task(
                            "E3", scheduler, seed,
                            period=period,
                            scenario=scenario,
                            params=params,
                            label=FORECAST_LABELS[variant],
                            forecast_error=error,
                            variant=variant,
                        ))

        # Forecast-independent references
        for scheduler in ("round_robin", "greenest_region"):
            for period in PERIODS:
                for seed in seeds:
                    specs.append(task(
                        "E3", scheduler, seed,
                        period=period,
                        scenario=scenario,
                        forecast_error=0.0,
                        variant=scheduler,
                    ))

    df, _ = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e3_forecast_runs.csv"), index=False)

    table = summarise(
        df,
        ["scenario", "variant", "label", "forecast_error"],
        ["total_carbon_g", "total_cost", "sla_violations",
         "average_latency", "p95_latency"],
    )

    table.to_csv(os.path.join(OUTPUT_DIR, "e3_forecast_summary.csv"),
                 index=False)

    return table


# ============================================================
# E4 - MAX WAIT (practical limits of temporal shifting)
# ============================================================

def experiment_maxwait(seeds, workers):

    waits = (0, 1, 2, 4, 6, 8, 12, 18, 24)

    specs = [
        task("E4", scheduler, seed, period=period, scenario=scenario,
             max_wait=wait)
        for scenario in ("core", "germany_only")
        for wait in waits
        for scheduler in ("temporal_green", "greenops_moo")
        for period in PERIODS
        for seed in seeds
    ]

    df, _ = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e4_maxwait_runs.csv"), index=False)

    table = summarise(
        df,
        ["scenario", "scheduler", "label", "max_wait"],
        ["total_carbon_g", "total_cost", "sla_violations",
         "average_latency", "p95_latency"],
    )

    table.to_csv(os.path.join(OUTPUT_DIR, "e4_maxwait_summary.csv"),
                 index=False)

    return table


# ============================================================
# E5 - LOAD SENSITIVITY
# ============================================================

def experiment_load(seeds, workers):

    loads = (0.5, 1.0, 1.5, 2.0, 3.0)

    schedulers = ("round_robin", "cost_only", "greenest_region",
                  "temporal_green", "greenops_moo")

    specs = [
        task("E5", scheduler, seed, period=period, load_scale=load)
        for load in loads
        for scheduler in schedulers
        for period in PERIODS
        for seed in seeds
    ]

    df, _ = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e5_load_runs.csv"), index=False)

    table = summarise(
        df,
        ["scheduler", "label", "load_scale"],
        ["total_carbon_g", "total_cost", "sla_violations",
         "sla_violation_rate", "average_latency", "p95_latency",
         "share_Norway"],
    )

    table.to_csv(os.path.join(OUTPUT_DIR, "e5_load_summary.csv"), index=False)

    return table


# ============================================================
# E6 - EXTENDED REGION SET
# ============================================================

def experiment_extended(seeds, workers):

    specs = [
        task("E6", scheduler, seed, period=period, scenario="extended",
             load_scale=2.0)
        for scheduler in MAIN_SCHEDULERS
        for period in PERIODS
        for seed in seeds
    ]

    df, _ = execute(specs, workers)

    df.to_csv(os.path.join(OUTPUT_DIR, "e6_extended_runs.csv"), index=False)

    share_columns = [c for c in df.columns if c.startswith("share_")]

    table = summarise(
        df,
        ["scheduler", "label"],
        ["total_carbon_g", "total_cost", "sla_violations",
         "average_latency", "p95_latency"] + share_columns,
    )

    table.to_csv(os.path.join(OUTPUT_DIR, "e6_extended_summary.csv"),
                 index=False)

    return table


# ============================================================
# E7 - SCALABILITY
# ============================================================

def experiment_scale():

    sizes = (100, 500, 1000, 2000, 5000)

    specs = [
        task("E7", scheduler, 0, num_jobs=size)
        for size in sizes
        for scheduler in ("greenest_region", "temporal_green",
                          "greenops_moo", "greenops_pareto")
    ]

    # Constant load: more jobs = longer horizon, same utilisation.
    # Serial on purpose: wall-clock timing.
    df, _ = execute(specs, workers=1)

    df["ms_per_decision"] = df["wall_seconds"] / df["decisions"] * 1000

    df.to_csv(os.path.join(OUTPUT_DIR, "e7_scale_runs.csv"), index=False)

    return df[["label", "num_jobs", "wall_seconds", "decisions",
               "ms_per_decision", "sla_violations"]]


# ============================================================
# MAIN
# ============================================================

EXPERIMENTS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7")


def main():

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])

    parser.add_argument("--only", default=",".join(EXPERIMENTS))
    parser.add_argument("--quick", action="store_true",
                        help="3 seeds instead of 20/10")
    parser.add_argument("--workers", type=int,
                        default=max(1, (os.cpu_count() or 2) - 2))

    args = parser.parse_args()

    selected = {e.strip().upper() for e in args.only.split(",")}

    main_seeds = range(3) if args.quick else range(20)
    seeds = range(3) if args.quick else range(10)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    steps = [
        ("E1", "Main comparison", lambda: experiment_main(main_seeds, args.workers)),
        ("E2", "Weight sweep / Pareto frontier", lambda: experiment_sweep(seeds, args.workers)),
        ("E3", "Forecast-error sensitivity", lambda: experiment_forecast(seeds, args.workers)),
        ("E4", "Max-wait sensitivity", lambda: experiment_maxwait(seeds, args.workers)),
        ("E5", "Load sensitivity", lambda: experiment_load(seeds, args.workers)),
        ("E6", "Extended regions", lambda: experiment_extended(seeds, args.workers)),
        ("E7", "Scalability", experiment_scale),
    ]

    for key, title, run in steps:

        if key not in selected:
            continue

        started = time.time()

        print(f"\n{'=' * 70}\n{key}: {title}\n{'=' * 70}")

        result = run()

        print(result.round(3).to_string(index=False))

        print(f"\n[{key} finished in {time.time() - started:.1f} s]")

    print(f"\nResults written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

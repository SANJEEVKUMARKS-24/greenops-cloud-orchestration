"""
Shared experiment building blocks: regions, carbon traces, workloads,
scheduler factory and a single-run helper.

Every experiment script builds its scenario through this module so that
all schedulers are always compared on identical inputs.
"""

import csv
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sim.job import Job
from sim.region import Region
from sim.engine import CloudSimulator
from sim.forecast import CarbonForecaster

from metrics.collector import MetricsCollector

from schedulers.round_robin import RoundRobinScheduler
from schedulers.cost_only import CostOnlyScheduler
from schedulers.greenest_region import GreenestRegionScheduler
from schedulers.temporal_green import TemporalGreenScheduler
from schedulers.carbon_aware_moo import CarbonAwareMOOScheduler

from data.workload_traces.generate_workload import generate_jobs


# ============================================================
# PATHS
# ============================================================

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

CONTROLLED_TRACE_DIR = os.path.join(DATA_DIR, "carbon_traces")

HISTORICAL_TRACE_DIR = os.path.join(
    DATA_DIR,
    "carbon_traces",
    "historical"
)

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")


# ============================================================
# REGION PROFILES
#
# India, Germany and Norway keep the parameters used in the
# preliminary report. France, Poland and Great Britain form the
# extended region set.
#
# PUE values are representative facility averages (Uptime
# Institute surveys: cold-climate Nordic sites ~1.15, newer EU
# sites ~1.3, hot-climate sites ~1.6).
# ============================================================

REGION_PROFILES = {
    "India": dict(
        cost_per_cpu_hour=0.08,
        idle_power_kw=0.12,
        max_power_kw=0.55,
        pue=1.60,
        trace="india",
    ),
    "Germany": dict(
        cost_per_cpu_hour=0.11,
        idle_power_kw=0.10,
        max_power_kw=0.50,
        pue=1.30,
        trace="germany",
    ),
    "Norway": dict(
        cost_per_cpu_hour=0.14,
        idle_power_kw=0.08,
        max_power_kw=0.42,
        pue=1.15,
        trace="norway",
    ),
    "France": dict(
        cost_per_cpu_hour=0.12,
        idle_power_kw=0.10,
        max_power_kw=0.48,
        pue=1.35,
        trace="france",
    ),
    "Poland": dict(
        cost_per_cpu_hour=0.09,
        idle_power_kw=0.11,
        max_power_kw=0.52,
        pue=1.45,
        trace="poland",
    ),
    "Great Britain": dict(
        cost_per_cpu_hour=0.13,
        idle_power_kw=0.10,
        max_power_kw=0.48,
        pue=1.35,
        trace="great_britain",
    ),
}

CORE_REGIONS = ("India", "Germany", "Norway")

EXTENDED_REGIONS = (
    "India",
    "Germany",
    "Norway",
    "France",
    "Poland",
    "Great Britain",
)

PERIODS = ("winter_2024", "summer_2024")


# ============================================================
# CARBON TRACES
# ============================================================

def load_controlled_trace(filename):
    """24-hour profile {hour: intensity} (preliminary experiment)."""

    df = pd.read_csv(filename)

    return dict(
        zip(
            df["time"],
            df["carbon_intensity"]
        )
    )


def load_historical_trace(period, trace_name, column="carbon_intensity"):
    """Multi-week hourly list [intensity_h0, intensity_h1, ...]."""

    df = pd.read_csv(
        os.path.join(
            HISTORICAL_TRACE_DIR,
            period,
            f"{trace_name}.csv"
        )
    )

    return df[column].astype(float).tolist()


def load_traces(period, region_names=CORE_REGIONS):
    """
    period = "controlled"      -> original 24-hour CSV profiles
    period = "winter_2024" ... -> historical hourly traces
    """

    traces = {}

    for name in region_names:

        trace_name = REGION_PROFILES[name]["trace"]

        if period == "controlled":

            traces[name] = load_controlled_trace(
                os.path.join(
                    CONTROLLED_TRACE_DIR,
                    f"{trace_name}.csv"
                )
            )

        else:

            traces[name] = load_historical_trace(
                period,
                trace_name
            )

    return traces


# ============================================================
# REGIONS
# ============================================================

def build_regions(
    traces,
    cpu_capacity=16,
    memory_capacity=32
):
    """Fresh Region objects (never share state between runs)."""

    regions = []

    for name, trace in traces.items():

        profile = REGION_PROFILES[name]

        regions.append(
            Region(
                name=name,
                cpu_capacity=cpu_capacity,
                memory_capacity=memory_capacity,
                cost_per_cpu_hour=profile["cost_per_cpu_hour"],
                carbon_trace=(
                    dict(trace) if isinstance(trace, dict)
                    else list(trace)
                ),
                idle_power_kw=profile["idle_power_kw"],
                max_power_kw=profile["max_power_kw"],
                pue=profile["pue"],
            )
        )

    return regions


# ============================================================
# WORKLOADS
# ============================================================

def load_workload(filename):

    jobs = []

    with open(filename, "r", newline="") as file:

        reader = csv.DictReader(file)

        for row in reader:

            allowed = row.get("allowed_regions") or ""

            jobs.append(
                Job(
                    job_id=row["job_id"],
                    arrival_time=float(row["arrival_time"]),
                    cpu_required=int(row["cpu_required"]),
                    memory_required=int(row["memory_required"]),
                    runtime=float(row["runtime"]),
                    deadline=float(row["deadline"]),
                    flexibility=row["flexibility"],
                    max_cost=(
                        float(row["max_cost"])
                        if row.get("max_cost") else None
                    ),
                    carbon_priority=float(row["carbon_priority"]),
                    allowed_regions=(
                        allowed.split(";") if allowed else None
                    ),
                )
            )

    return jobs


def make_workload(
    num_jobs,
    seed,
    locality_fraction=0.25,
    region_names=CORE_REGIONS,
    load_scale=1.0
):

    return generate_jobs(
        num_jobs=num_jobs,
        seed=seed,
        locality_fraction=locality_fraction,
        region_names=region_names,
        load_scale=load_scale,
    )


def preliminary_workload():
    """The five hand-crafted jobs of the preliminary experiment."""

    return [
        # Strict real-time workload
        Job("J001", 0, 4, 4, 2, 6, "strict", 2.0, 0.5),
        # Batch workload
        Job("J002", 1, 2, 4, 3, 8, "batch", 1.0, 0.6),
        # Flexible workload
        Job("J003", 2, 4, 8, 2, 10, "flexible", 1.5, 0.8),
        # Strict workload
        Job("J004", 3, 2, 4, 1, 8, "strict", 1.0, 0.4),
        # Flexible workload designed to test temporal shifting
        Job("J005", 10, 4, 8, 2, 18, "flexible", 1.5, 0.9),
    ]


# ============================================================
# SCHEDULERS
# ============================================================

SCHEDULER_LABELS = {
    "round_robin": "Round Robin",
    "cost_only": "Cost Only",
    "greenest_region": "Greenest Region",
    "temporal_green": "Temporal Green",
    "greenops_spatial": "GreenOps (spatial only)",
    "greenops_moo": "GreenOps MOO",
    "greenops_pareto": "GreenOps Pareto",
}

BASELINES = (
    "round_robin",
    "cost_only",
    "greenest_region",
    "temporal_green",
)


def make_scheduler(key, max_wait=12, **params):

    if key == "round_robin":
        return RoundRobinScheduler()

    if key == "cost_only":
        return CostOnlyScheduler()

    if key == "greenest_region":
        return GreenestRegionScheduler()

    if key == "temporal_green":
        return TemporalGreenScheduler(max_wait=max_wait)

    if key == "greenops_moo":
        return CarbonAwareMOOScheduler(max_wait=max_wait, **params)

    if key == "greenops_pareto":
        return CarbonAwareMOOScheduler(
            max_wait=max_wait,
            mode="pareto",
            **params
        )

    if key == "greenops_spatial":
        return CarbonAwareMOOScheduler(max_wait=0, **params)

    raise ValueError(f"unknown scheduler {key!r}")


# ============================================================
# SINGLE RUN
# ============================================================

def run_simulation(
    scheduler,
    traces,
    jobs,
    forecast_error=0.0,
    forecast_seed=0,
    cpu_capacity=16,
    verbose=False
):
    """
    Run one scheduler on one scenario.

    Returns (summary dict, per-job DataFrame).
    """

    regions = build_regions(traces, cpu_capacity=cpu_capacity)

    forecaster = None

    if forecast_error > 0:

        forecaster = CarbonForecaster(
            regions,
            error_level=forecast_error,
            seed=forecast_seed
        )

    metrics = MetricsCollector()

    simulator = CloudSimulator(
        regions=regions,
        scheduler=scheduler,
        metrics=metrics,
        forecaster=forecaster,
        verbose=verbose
    )

    for job in jobs:
        simulator.submit_job(job)

    simulator.run()

    return metrics.summary(), metrics.dataframe()

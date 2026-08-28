import os
import copy
import pandas as pd

from sim.job import Job
from sim.region import Region
from sim.engine import CloudSimulator

from metrics.collector import MetricsCollector

from schedulers.round_robin import RoundRobinScheduler
from schedulers.cost_only import CostOnlyScheduler
from schedulers.greenest_region import GreenestRegionScheduler
from schedulers.temporal_green import TemporalGreenScheduler
from schedulers.carbon_aware_moo import CarbonAwareMOOScheduler


# ============================================================
# CONFIGURATION
# ============================================================

CARBON_DATA_DIRECTORY = "data/carbon_traces"

RESULTS_DIRECTORY = "results/comparison"

os.makedirs(
    RESULTS_DIRECTORY,
    exist_ok=True
)


# ============================================================
# LOAD CARBON TRACE
# ============================================================

def load_carbon_trace(filename):

    df = pd.read_csv(filename)

    return dict(
        zip(
            df["time"],
            df["carbon_intensity"]
        )
    )


# ============================================================
# LOAD ALL REGIONAL CARBON DATA
# ============================================================

def load_all_carbon_traces():

    india = load_carbon_trace(
        os.path.join(
            CARBON_DATA_DIRECTORY,
            "india.csv"
        )
    )

    germany = load_carbon_trace(
        os.path.join(
            CARBON_DATA_DIRECTORY,
            "germany.csv"
        )
    )

    norway = load_carbon_trace(
        os.path.join(
            CARBON_DATA_DIRECTORY,
            "norway.csv"
        )
    )

    return {
        "India": india,
        "Germany": germany,
        "Norway": norway
    }


# ============================================================
# CREATE FRESH REGIONS
#
# IMPORTANT:
# Every scheduler gets a completely fresh set of regions.
# ============================================================

def create_regions(carbon_traces):

    return [

        Region(
            name="India",
            cpu_capacity=16,
            memory_capacity=32,
            cost_per_cpu_hour=0.08,
            carbon_trace=copy.deepcopy(
                carbon_traces["India"]
            )
        ),

        Region(
            name="Germany",
            cpu_capacity=16,
            memory_capacity=32,
            cost_per_cpu_hour=0.11,
            carbon_trace=copy.deepcopy(
                carbon_traces["Germany"]
            )
        ),

        Region(
            name="Norway",
            cpu_capacity=16,
            memory_capacity=32,
            cost_per_cpu_hour=0.14,
            carbon_trace=copy.deepcopy(
                carbon_traces["Norway"]
            )
        )
    ]


# ============================================================
# CREATE COMMON WORKLOAD
#
# Every scheduler receives exactly the same jobs.
# ============================================================

def create_workloads():

    return [

        # ----------------------------------------------------
        # J001
        # Strict real-time workload
        # ----------------------------------------------------

        Job(
            job_id="J001",
            arrival_time=0,
            cpu_required=4,
            memory_required=4,
            runtime=2,
            deadline=6,
            flexibility="strict",
            max_cost=2.0,
            carbon_priority=0.5
        ),

        # ----------------------------------------------------
        # J002
        # Batch workload
        # ----------------------------------------------------

        Job(
            job_id="J002",
            arrival_time=1,
            cpu_required=2,
            memory_required=4,
            runtime=3,
            deadline=8,
            flexibility="batch",
            max_cost=1.0,
            carbon_priority=0.6
        ),

        # ----------------------------------------------------
        # J003
        # Flexible workload
        # ----------------------------------------------------

        Job(
            job_id="J003",
            arrival_time=2,
            cpu_required=4,
            memory_required=8,
            runtime=2,
            deadline=10,
            flexibility="flexible",
            max_cost=1.5,
            carbon_priority=0.8
        ),

        # ----------------------------------------------------
        # J004
        # Strict workload
        # ----------------------------------------------------

        Job(
            job_id="J004",
            arrival_time=3,
            cpu_required=2,
            memory_required=4,
            runtime=1,
            deadline=8,
            flexibility="strict",
            max_cost=1.0,
            carbon_priority=0.4
        ),

        # ----------------------------------------------------
        # J005
        # Flexible workload
        #
        # Designed to test temporal shifting.
        # ----------------------------------------------------

        Job(
            job_id="J005",
            arrival_time=10,
            cpu_required=4,
            memory_required=8,
            runtime=2,
            deadline=18,
            flexibility="flexible",
            max_cost=1.5,
            carbon_priority=0.9
        )
    ]


# ============================================================
# CREATE SCHEDULERS
# ============================================================

def create_schedulers():

    return {

        "Round Robin":
            RoundRobinScheduler(),

        "Cost Only":
            CostOnlyScheduler(),

        "Greenest Region":
            GreenestRegionScheduler(),

        "Temporal Green":
            TemporalGreenScheduler(
                max_wait=6
            ),

        "GreenOps MOO":
            CarbonAwareMOOScheduler(
                carbon_weight=0.5,
                cost_weight=0.2,
                waiting_weight=0.3,
                max_wait=6
            )
    }


# ============================================================
# RUN ONE SCHEDULER
# ============================================================

def run_scheduler(
    scheduler_name,
    scheduler,
    carbon_traces,
    verbose=False
):

    print("\n")
    print("=" * 60)
    print(
        f"RUNNING: {scheduler_name}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Fresh regions
    # --------------------------------------------------------

    regions = create_regions(
        carbon_traces
    )

    # --------------------------------------------------------
    # Fresh workloads
    # --------------------------------------------------------

    jobs = create_workloads()

    # --------------------------------------------------------
    # Fresh metrics collector
    # --------------------------------------------------------

    metrics = MetricsCollector()

    # --------------------------------------------------------
    # Fresh simulator
    # --------------------------------------------------------

    simulator = CloudSimulator(
        regions=regions,
        scheduler=scheduler,
        metrics=metrics
    )

    # --------------------------------------------------------
    # Submit jobs
    # --------------------------------------------------------

    for job in jobs:

        simulator.submit_job(job)

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    simulator.run()

    # --------------------------------------------------------
    # Get summary
    # --------------------------------------------------------

    summary = metrics.summary()

    # --------------------------------------------------------
    # Add scheduler name
    # --------------------------------------------------------

    summary["scheduler"] = scheduler_name

    # --------------------------------------------------------
    # Save individual results
    # --------------------------------------------------------

    safe_name = (
        scheduler_name
        .lower()
        .replace(" ", "_")
    )

    output_file = os.path.join(
        RESULTS_DIRECTORY,
        f"{safe_name}.csv"
    )

    metrics.save_csv(
        output_file
    )

    print(
        f"\nSaved: {output_file}"
    )

    return summary


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print(
        "GREENOPS SCHEDULER COMPARISON"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Load carbon traces once
    # --------------------------------------------------------

    carbon_traces = (
        load_all_carbon_traces()
    )

    # --------------------------------------------------------
    # Create scheduler definitions
    # --------------------------------------------------------

    scheduler_definitions = (
        create_schedulers()
    )

    # --------------------------------------------------------
    # Store all summaries
    # --------------------------------------------------------

    all_results = []

    # --------------------------------------------------------
    # Run every scheduler
    # --------------------------------------------------------

    for scheduler_name, scheduler in (
        scheduler_definitions.items()
    ):

        summary = run_scheduler(
            scheduler_name,
            scheduler,
            carbon_traces
        )

        all_results.append(
            summary
        )

    # ========================================================
    # CREATE COMPARISON DATAFRAME
    # ========================================================

    comparison = pd.DataFrame(
        all_results
    )

    # --------------------------------------------------------
    # Reorder columns
    # --------------------------------------------------------

    preferred_columns = [

        "scheduler",

        "total_jobs",
        "completed_jobs",

        "total_carbon_g",
        "total_energy_kwh",

        "total_cost",

        "sla_violations",
        "sla_violation_rate",

        "average_latency",
        "p95_latency"
    ]

    existing_columns = [
        column
        for column in preferred_columns
        if column in comparison.columns
    ]

    comparison = comparison[
        existing_columns
    ]

    # ========================================================
    # SAVE COMPARISON
    # ========================================================

    comparison_file = os.path.join(
        RESULTS_DIRECTORY,
        "comparison.csv"
    )

    comparison.to_csv(
        comparison_file,
        index=False
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print("\n")
    print("=" * 60)
    print(
        "FINAL SCHEDULER COMPARISON"
    )
    print("=" * 60)

    print(
        comparison.to_string(
            index=False
        )
    )

    print("\n")
    print(
        f"Comparison saved to:"
    )

    print(
        comparison_file
    )

    print("\n")
    print("=" * 60)
    print(
        "EXPERIMENT COMPLETE"
    )
    print("=" * 60)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
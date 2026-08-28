import pandas as pd

from sim.job import Job
from sim.region import Region
from sim.engine import CloudSimulator

from schedulers.carbon_aware_moo import (
    CarbonAwareMOOScheduler
)

from metrics.collector import MetricsCollector


# ==========================================
# Carbon Trace Loader
# ==========================================

def load_carbon_trace(filename):

    df = pd.read_csv(filename)

    return dict(
        zip(
            df["time"],
            df["carbon_intensity"]
        )
    )


# ==========================================
# Load Carbon Traces
# ==========================================

india_carbon = load_carbon_trace(
    "data/carbon_traces/india.csv"
)

germany_carbon = load_carbon_trace(
    "data/carbon_traces/germany.csv"
)

norway_carbon = load_carbon_trace(
    "data/carbon_traces/norway.csv"
)


# ==========================================
# Create Regions
# ==========================================

regions = [

    Region(
    name="India",
    cpu_capacity=16,
    memory_capacity=32,
    cost_per_cpu_hour=0.08,
    carbon_trace=india_carbon,
    idle_power_kw=0.12,
    max_power_kw=0.55
    ),

    Region(
    name="Germany",
    cpu_capacity=16,
    memory_capacity=32,
    cost_per_cpu_hour=0.11,
    carbon_trace=germany_carbon,
    idle_power_kw=0.10,
    max_power_kw=0.50
),

    Region(
        name="Norway",
        cpu_capacity=16,
        memory_capacity=32,
        cost_per_cpu_hour=0.14,
        carbon_trace=norway_carbon,
        idle_power_kw=0.08,
        max_power_kw=0.42
    )
]


# ==========================================
# Create GreenOps Scheduler
# ==========================================

scheduler = CarbonAwareMOOScheduler(
    carbon_weight=0.5,
    cost_weight=0.2,
    waiting_weight=0.3,
    max_wait=6
)


# ==========================================
# Metrics Collector
# ==========================================

metrics = MetricsCollector()


# ==========================================
# Create Simulator
# ==========================================

simulator = CloudSimulator(
    regions=regions,
    scheduler=scheduler,
    metrics=metrics
)


# ==========================================
# Create Workloads
# ==========================================

jobs = [

    # --------------------------------------
    # Strict workload
    # --------------------------------------

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

    # --------------------------------------
    # Deadline-bound batch
    # --------------------------------------

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

    # --------------------------------------
    # Flexible workload
    # --------------------------------------

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

    # --------------------------------------
    # Strict workload
    # --------------------------------------

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

    # --------------------------------------
    # Flexible workload designed to test
    # temporal shifting
    # --------------------------------------

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


# ==========================================
# Submit Jobs
# ==========================================

for job in jobs:

    simulator.submit_job(job)


# ==========================================
# Run Simulation
# ==========================================

print("\n========================================")
print(" GREENOPS MULTI-OBJECTIVE EXPERIMENT")
print("========================================\n")

simulator.run()


# ==========================================
# Job Results
# ==========================================

print("\n========== JOB RESULTS ==========\n")

for result in metrics.get_results():

    print(result)


# ==========================================
# Summary
# ==========================================

summary = metrics.summary()

print("\n========== SUMMARY ==========\n")

for key, value in summary.items():

    print(f"{key}: {value}")


# ==========================================
# Save Results
# ==========================================

output_file = (
    "results/carbon_aware_moo_results.csv"
)

metrics.save_csv(output_file)

print(
    f"\nResults saved to {output_file}"
)
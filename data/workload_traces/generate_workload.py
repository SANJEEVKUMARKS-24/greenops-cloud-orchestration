import argparse
import csv
import os
import random
import sys

# Allow importing the project's Job class
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sim.job import Job


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_NUM_JOBS = 100
DEFAULT_SEED = 42

# Fraction of jobs that carry a data-residency constraint and may
# only run in their "home" region (e.g. Indian payment data that
# must stay in India, or a German sovereign-cloud workload).
DEFAULT_LOCALITY_FRACTION = 0.25

DEFAULT_REGIONS = ("India", "Germany", "Norway")

# Compute price per region ($ per CPU-hour), used to set budgets.
# Budgets are a multiple of the cheapest cost the job could
# achieve in the regions it is allowed to use, so they scale with
# job size. A free-to-move job needs a multiplier >= 1.75 to
# afford Norway (0.14 / 0.08).
REGION_PRICES = {
    "India": 0.08,
    "Germany": 0.11,
    "Norway": 0.14,
    "France": 0.12,
    "Poland": 0.09,
    "Great Britain": 0.13,
}

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "workload_100.csv"
)


# ============================================================
# WORKLOAD PROFILES
# ============================================================

WORKLOAD_PROFILES = {

    # --------------------------------------------------------
    # Strict real-time workloads
    # --------------------------------------------------------

    "strict": {
        "probability": 0.40,

        "cpu_range": (1, 4),
        "memory_range": (2, 8),

        "runtime_range": (1, 3),

        # Tight deadline
        "deadline_slack_range": (2, 5),

        # Budget = job size x cheapest price x multiplier
        "budget_multiplier_range": (1.3, 2.2),

        "carbon_priority_range": (0.2, 0.6)
    },


    # --------------------------------------------------------
    # Deadline-bound batch workloads
    # --------------------------------------------------------

    "batch": {
        "probability": 0.35,

        "cpu_range": (2, 8),
        "memory_range": (4, 16),

        "runtime_range": (2, 6),

        # More scheduling flexibility
        "deadline_slack_range": (5, 10),

        "budget_multiplier_range": (1.1, 2.0),

        "carbon_priority_range": (0.5, 0.8)
    },


    # --------------------------------------------------------
    # Fully flexible workloads
    # --------------------------------------------------------

    "flexible": {
        "probability": 0.25,

        "cpu_range": (2, 8),
        "memory_range": (4, 16),

        "runtime_range": (2, 6),

        # Large deadline window
        "deadline_slack_range": (8, 16),

        "budget_multiplier_range": (1.05, 1.9),

        "carbon_priority_range": (0.7, 1.0)
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def choose_workload_type():

    types = list(WORKLOAD_PROFILES.keys())

    probabilities = [
        WORKLOAD_PROFILES[t]["probability"]
        for t in types
    ]

    return random.choices(
        types,
        weights=probabilities,
        k=1
    )[0]


def random_float(low, high, decimals=2):

    return round(
        random.uniform(low, high),
        decimals
    )


# ============================================================
# JOB GENERATOR
# ============================================================

def generate_jobs(
    num_jobs=DEFAULT_NUM_JOBS,
    seed=DEFAULT_SEED,
    locality_fraction=DEFAULT_LOCALITY_FRACTION,
    region_names=DEFAULT_REGIONS,
    load_scale=1.0
):
    """
    Generate a heterogeneous workload.

    load_scale > 1 compresses inter-arrival times (more jobs per
    hour, higher utilisation); load_scale < 1 stretches them.

    Locality constraints are drawn from a SEPARATE random stream so
    that the other job attributes for a given seed do not change
    when locality_fraction or region_names change.
    """

    random.seed(seed)

    locality_rng = random.Random(seed + 7919)

    jobs = []

    current_arrival = 0

    for i in range(1, num_jobs + 1):

        # ----------------------------------------------------
        # Select workload type
        # ----------------------------------------------------

        flexibility = choose_workload_type()

        profile = WORKLOAD_PROFILES[flexibility]


        # ----------------------------------------------------
        # Arrival time
        # ----------------------------------------------------

        # Most jobs arrive within a simulated 24-hour period.
        #
        # Inter-arrival time is randomly selected so that
        # multiple jobs can overlap and create resource
        # contention.

        if i == 1:

            arrival_time = 0

        else:

            inter_arrival = random.choices(
                population=[0, 1, 2, 3],
                weights=[0.15, 0.40, 0.30, 0.15],
                k=1
            )[0]

            current_arrival += inter_arrival / load_scale

            arrival_time = round(current_arrival, 2)

            if arrival_time == int(arrival_time):
                arrival_time = int(arrival_time)


        # ----------------------------------------------------
        # CPU requirement
        # ----------------------------------------------------

        cpu_required = random.randint(
            profile["cpu_range"][0],
            profile["cpu_range"][1]
        )


        # ----------------------------------------------------
        # Memory requirement
        # ----------------------------------------------------

        memory_required = random.randint(
            profile["memory_range"][0],
            profile["memory_range"][1]
        )


        # ----------------------------------------------------
        # Runtime
        # ----------------------------------------------------

        runtime = random.randint(
            profile["runtime_range"][0],
            profile["runtime_range"][1]
        )


        # ----------------------------------------------------
        # Deadline
        # ----------------------------------------------------

        deadline_slack = random.randint(
            profile["deadline_slack_range"][0],
            profile["deadline_slack_range"][1]
        )

        deadline = arrival_time + runtime + deadline_slack


        # ----------------------------------------------------
        # Data-locality constraint
        # ----------------------------------------------------

        allowed_regions = None

        if locality_rng.random() < locality_fraction:

            allowed_regions = [
                locality_rng.choice(list(region_names))
            ]

        # ----------------------------------------------------
        # Maximum cost
        # ----------------------------------------------------

        budget_multiplier = random.uniform(
            profile["budget_multiplier_range"][0],
            profile["budget_multiplier_range"][1]
        )

        reference_price = min(
            REGION_PRICES[name]
            for name in (allowed_regions or region_names)
        )

        max_cost = round(
            cpu_required
            * runtime
            * reference_price
            * budget_multiplier,
            2
        )


        # ----------------------------------------------------
        # Carbon priority
        # ----------------------------------------------------

        carbon_priority = random_float(
            profile["carbon_priority_range"][0],
            profile["carbon_priority_range"][1]
        )


        # ----------------------------------------------------
        # Create Job
        # ----------------------------------------------------

        job = Job(

            job_id=f"J{i:04d}",

            arrival_time=arrival_time,

            cpu_required=cpu_required,

            memory_required=memory_required,

            runtime=runtime,

            deadline=deadline,

            flexibility=flexibility,

            max_cost=max_cost,

            carbon_priority=carbon_priority,

            allowed_regions=allowed_regions
        )


        jobs.append(job)


    return jobs


# ============================================================
# SAVE WORKLOAD TO CSV
# ============================================================

def save_workload(
    jobs,
    filename
):

    os.makedirs(
        os.path.dirname(filename),
        exist_ok=True
    )

    with open(
        filename,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "job_id",
            "arrival_time",
            "cpu_required",
            "memory_required",
            "runtime",
            "deadline",
            "flexibility",
            "max_cost",
            "carbon_priority",
            "allowed_regions"
        ])

        for job in jobs:

            writer.writerow([
                job.job_id,
                job.arrival_time,
                job.cpu_required,
                job.memory_required,
                job.runtime,
                job.deadline,
                job.flexibility,
                job.max_cost,
                job.carbon_priority,
                ";".join(sorted(job.allowed_regions))
                if job.allowed_regions else ""
            ])


# ============================================================
# DISPLAY WORKLOAD STATISTICS
# ============================================================

def print_statistics(jobs):

    print("\n========================================")
    print(" GENERATED WORKLOAD")
    print("========================================")

    print(f"Total jobs : {len(jobs)}")

    print(
        f"Simulation arrival range : "
        f"{jobs[0].arrival_time} - "
        f"{jobs[-1].arrival_time}"
    )

    print("\nWorkload distribution:")

    counts = {
        "strict": 0,
        "batch": 0,
        "flexible": 0
    }

    for job in jobs:

        counts[job.flexibility] += 1

    for workload_type, count in counts.items():

        percentage = (
            count / len(jobs)
        ) * 100

        print(
            f"  {workload_type:10s} : "
            f"{count:4d} "
            f"({percentage:.1f}%)"
        )

    print("\nResource statistics:")

    average_cpu = sum(
        job.cpu_required
        for job in jobs
    ) / len(jobs)

    average_memory = sum(
        job.memory_required
        for job in jobs
    ) / len(jobs)

    average_runtime = sum(
        job.runtime
        for job in jobs
    ) / len(jobs)

    print(
        f"  Average CPU       : "
        f"{average_cpu:.2f}"
    )

    print(
        f"  Average memory    : "
        f"{average_memory:.2f} GB"
    )

    print(
        f"  Average runtime   : "
        f"{average_runtime:.2f} hours"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate a GreenOps workload trace"
    )

    parser.add_argument("--jobs", type=int, default=DEFAULT_NUM_JOBS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--locality",
        type=float,
        default=DEFAULT_LOCALITY_FRACTION,
        help="fraction of region-pinned jobs"
    )
    parser.add_argument("--load-scale", type=float, default=1.0)
    parser.add_argument("--output", default=OUTPUT_FILE)

    args = parser.parse_args()

    jobs = generate_jobs(
        num_jobs=args.jobs,
        seed=args.seed,
        locality_fraction=args.locality,
        load_scale=args.load_scale
    )

    save_workload(
        jobs,
        args.output
    )

    print_statistics(jobs)

    pinned = sum(
        1 for job in jobs
        if job.allowed_regions
    )

    print(
        f"  Region-pinned jobs: {pinned}"
    )

    print(
        "\nWorkload saved to:"
    )

    print(
        args.output
    )
